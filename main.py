import sys,os,numpy as np
import pandas as pd

from PyQt5.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFileDialog,QSplitter,QPushButton,QDialog,QTableWidget,QTableWidgetItem,QMessageBox,QListWidget,QListWidgetItem,QLabel,QLineEdit
from PyQt5.QtCore import QThread,pyqtSignal,Qt

from utils.ui_controls import ControlBar
from utils.tsne_plot import TSNEPlot
from utils.neighbor_panel import NeighborPanel
from utils.drug_mapping import *

from config import DISTANCE,RANDOM_SEED,MAX_POINTS,DEFAULT_NPZ_PATH, TSNE_BACKEND

def load_reduction_backend():

    if TSNE_BACKEND in ("auto","cuml"):

        try:
            from cuml.manifold import TSNE
            from cuml.decomposition import PCA

            print("Using cuML GPU backend")
            return TSNE,PCA,"cuml"

        except ImportError:

            if TSNE_BACKEND=="cuml":
                raise RuntimeError(
                    "TSNE_BACKEND='cuml', but cuML is not installed."
                )

    from sklearn.manifold import TSNE
    from sklearn.decomposition import PCA

    print("Using scikit-learn CPU backend")
    return TSNE,PCA,"sklearn"


TSNE,PCA,REDUCTION_BACKEND=load_reduction_backend()


#######################################################################################################
# CUDA TSNE WORKER
#######################################################################################################

class TSNEWorker(QThread):

    finished=pyqtSignal(object,object,object)

    def __init__(self,X,labels,perplexity,metric=DISTANCE):

        super().__init__()

        self.X=X
        self.labels=labels
        self.perplexity=perplexity
        self.metric=metric

    def run(self):

        X_tsne=self.X

        if self.metric=="cosine":
            norms=np.linalg.norm(X_tsne,axis=1,keepdims=True)
            norms[norms==0]=1.0
            X_tsne=X_tsne/norms

        if X_tsne.shape[1]>50:
                X_tsne=PCA(n_components=50).fit_transform(X_tsne)

        if REDUCTION_BACKEND=="cuml":

            tsne=TSNE(
                n_components=2,
                perplexity=self.perplexity,
                learning_rate=200,
                max_iter=1000,
                method="fft",
                metric=self.metric,
                n_neighbors=max(90,int(3*self.perplexity)),
                random_state=RANDOM_SEED,
                verbose=True
            )

        else:

            tsne=TSNE(
                n_components=2,
                perplexity=self.perplexity,
                learning_rate=200,
                max_iter=1000,
                method="barnes_hut",
                metric=self.metric,
                init="pca",
                random_state=RANDOM_SEED,
                verbose=1,
                n_jobs=-1
            )

        Y=np.asarray(tsne.fit_transform(X_tsne))

        self.finished.emit(Y,self.labels,self.X)

#######################################################################################################
# CANDIDATE TABLE DIALOG
#######################################################################################################

class CandidateDialog(QDialog):

    def __init__(self,df,click_callback,parent=None,title="Candidate list",aha_drug_map=None):

        super().__init__(parent)

        self.df=df
        self.click_callback=click_callback
        self.aha_drug_map={} if aha_drug_map is None else aha_drug_map

        self.setWindowTitle(title)
        self.resize(1000,500)

        layout=QVBoxLayout(self)

        self.table=QTableWidget()
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(list(df.columns))
        self.table.setSortingEnabled(False)

        for r in range(len(df)):

            for c,col in enumerate(df.columns):

                value=str(df.iloc[r][col])

                if col=="candidate_label":

                    drug,color=get_drug_display_info(value,self.aha_drug_map)

                    if drug is not None:

                        widget=QLabel(f'{value} <span style="color:{color};">({drug})</span>')
                        widget.setTextFormat(Qt.RichText)
                        widget.setAttribute(Qt.WA_TransparentForMouseEvents,True)
                        self.table.setCellWidget(r,c,widget)

                    else:

                        item=QTableWidgetItem(value)
                        self.table.setItem(r,c,item)

                else:

                    item=QTableWidgetItem(value)
                    self.table.setItem(r,c,item)

        self.table.resizeColumnsToContents()
        self.table.cellClicked.connect(self._on_cell_clicked)

        layout.addWidget(self.table)

    def _on_cell_clicked(self,row,col):

        if "candidate_label" not in self.df.columns:
            return

        label=str(self.df.iloc[row]["candidate_label"])

        if self.click_callback is not None:
            self.click_callback(label)

#######################################################################################################
# WELL DRUG DIALOG
#######################################################################################################

class WellDrugDialog(QDialog):

    def __init__(self,labels,click_callback,parent=None,title="Well list"):

        super().__init__(parent)

        self.labels=list(map(str,labels))
        self.click_callback=click_callback
        self.parent_ref=parent
        self.list_widgets={}
        self.items_by_experiment={}

        self.setWindowTitle(title)
        self.resize(1100,650)

        main_layout=QVBoxLayout(self)

        search_layout=QHBoxLayout()

        self.search_edit=QLineEdit()
        self.search_edit.setPlaceholderText("Search drug name...")

        self.search_btn=QPushButton("Search")
        self.search_btn.clicked.connect(self.apply_filter)

        self.reset_btn=QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_filter)

        self.search_edit.returnPressed.connect(self.apply_filter)

        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.reset_btn)

        main_layout.addLayout(search_layout)

        columns_layout=QHBoxLayout()
        main_layout.addLayout(columns_layout)

        experiments=["AHA","AEC","AEB","ALB"]

        for experiment in experiments:

            col_layout=QVBoxLayout()

            title_label=QLabel(experiment)
            title_label.setAlignment(Qt.AlignCenter)

            list_widget=QListWidget()

            if experiment=="AHA":
                list_widget.setMinimumWidth(450)
            else:
                list_widget.setMinimumWidth(220)

            list_widget.itemClicked.connect(self._on_item_clicked)

            self.list_widgets[experiment]=list_widget
            self.items_by_experiment[experiment]=[]

            col_layout.addWidget(title_label)
            col_layout.addWidget(list_widget)

            columns_layout.addLayout(col_layout)

        self.populate_lists()

    def populate_lists(self):

        for experiment,list_widget in self.list_widgets.items():

            list_widget.clear()
            self.items_by_experiment[experiment]=[]

            experiment_labels=[
                label for label in self.labels
                if parse_label(label)[0]==experiment
            ]

            for label in sorted(experiment_labels):

                drug,color=get_drug_display_info(label,self.parent_ref.aha_drug_map)

                if drug is not None:
                    item=QListWidgetItem("")
                else:
                    item=QListWidgetItem(label)

                item.setData(Qt.UserRole,label)
                item.setData(Qt.UserRole+1,drug if drug is not None else "")
                item.setData(Qt.UserRole+2,color if color is not None else "")

                list_widget.addItem(item)

                if drug is not None:

                    widget=QLabel(f'{label} <span style="color:{color};">({drug})</span>')
                    widget.setTextFormat(Qt.RichText)
                    widget.setAttribute(Qt.WA_TransparentForMouseEvents,True)

                    list_widget.setItemWidget(item,widget)
                    item.setSizeHint(widget.sizeHint())

                self.items_by_experiment[experiment].append(item)

    def apply_filter(self):

        query=self.search_edit.text().strip().lower()

        if query=="":
            self.show_all_items()
            return

        for experiment,items in self.items_by_experiment.items():

            for item in items:

                label=item.data(Qt.UserRole)
                drug=item.data(Qt.UserRole+1)

                searchable=f"{label} {drug}".lower()
                item.setHidden(query not in searchable)

    def reset_filter(self):

        self.search_edit.blockSignals(True)
        self.search_edit.clear()
        self.search_edit.blockSignals(False)

        self.show_all_items()

    def show_all_items(self):

        for experiment,items in self.items_by_experiment.items():

            for item in items:
                item.setHidden(False)

    def _on_item_clicked(self,item):

        label=item.data(Qt.UserRole)

        if self.click_callback is not None:
            self.click_callback(label)

#######################################################################################################
# MAIN WINDOW
#######################################################################################################

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.labels=[]
        self.aha_drug_map=load_aha_drug_map()

        self.setWindowTitle("CUDA t-SNE Viewer")
        self.resize(1200,800)

        central=QWidget()
        self.setCentralWidget(central)

        main_v=QVBoxLayout(central)
        main_v.setContentsMargins(8,8,8,8)
        main_v.setSpacing(6)

        self.controls=ControlBar(self.on_reload,self.on_browse)
        self.controls.path_edit.setText(str(DEFAULT_NPZ_PATH))

        main_v.addWidget(self.controls)

        self.load_candidates_btn=QPushButton("Load candidate CSV")
        self.load_candidates_btn.clicked.connect(self.on_load_candidates_csv)
        main_v.addWidget(self.load_candidates_btn)

        self.load_wells_btn=QPushButton("Open well list")
        self.load_wells_btn.clicked.connect(self.on_open_well_list)
        main_v.addWidget(self.load_wells_btn)

        splitter=QSplitter(Qt.Horizontal)
        main_v.addWidget(splitter,1)

        self.plot=TSNEPlot()
        splitter.addWidget(self.plot)

        self.neigh=NeighborPanel(close_callback=self.hide_neighborhood)
        self.neigh.setVisible(False)
        splitter.addWidget(self.neigh)

        splitter.setStretchFactor(0,1)
        splitter.setStretchFactor(1,0)
        splitter.setSizes([1100,300])

        self.plot.neighbor_panel_callback=self.show_neighborhood

        self.on_reload()

    ###################################################################################################
    # BROWSE NPZ FILE
    ###################################################################################################

    def on_browse(self):

        path,_=QFileDialog.getOpenFileName(
            self,
            "Select NPZ",
            "",
            "NPZ files (*.npz)"
        )

        if path:
            self.controls.path_edit.setText(path)
            self.on_reload()

    ###################################################################################################
    # LOAD EMBEDDINGS
    ###################################################################################################

    def on_reload(self):

        path=self.controls.path_edit.text().strip()

        if not path:
            return

        data=np.load(path,allow_pickle=True)

        X=data["X"].astype(np.float32)
        labels=np.array(list(map(str,data["labels"])))

        if MAX_POINTS is not None and len(X)>MAX_POINTS:

            rng=np.random.default_rng(RANDOM_SEED)
            idx=rng.choice(len(X),MAX_POINTS,replace=False)

            X=X[idx]
            labels=labels[idx]

        labels=list(labels)

        self.labels=labels

        self.worker=TSNEWorker(X, labels, self.controls.perplexity.value(), metric=DISTANCE)
        self.worker.finished.connect(self.on_tsne_finished)
        self.worker.start()

    ###################################################################################################
    # TSNE FINISHED
    ###################################################################################################

    def on_tsne_finished(self,Y,labels,X):

        self.plot.set_data(Y,labels,X)

    ###################################################################################################
    # OPEN WELL LIST
    ###################################################################################################

    def on_open_well_list(self):

        if len(self.labels)==0:
            QMessageBox.warning(self,"No labels","No wells are currently loaded.")
            return

        self.well_dialog=WellDrugDialog(
            labels=self.labels,
            click_callback=self.on_well_clicked,
            parent=self,
            title="Well list"
        )

        self.well_dialog.show()

    ###################################################################################################
    # WELL CLICKED
    ###################################################################################################

    def on_well_clicked(self,label):

        self.plot.focus_label(label,k=30)

    ###################################################################################################
    # LOAD CANDIDATE CSV
    ###################################################################################################

    def on_load_candidates_csv(self):

        path,_=QFileDialog.getOpenFileName(
            self,
            "Select candidate CSV",
            "",
            "CSV files (*.csv)"
        )

        if not path:
            return

        df=pd.read_csv(path)

        if "candidate_label" not in df.columns:
            QMessageBox.warning(self,"Missing column","The selected CSV has no candidate_label column.")
            return

        self.candidate_dialog=CandidateDialog(
            df=df,
            click_callback=self.on_candidate_clicked,
            parent=self,
            title="Candidate list",
            aha_drug_map=self.aha_drug_map
        )

        self.candidate_dialog.show()

    ###################################################################################################
    # CANDIDATE CLICKED
    ###################################################################################################

    def on_candidate_clicked(self,label):

        self.plot.focus_label(label,k=10)

    ###################################################################################################
    # SHOW NEIGHBOR PANEL
    ###################################################################################################

    def show_neighborhood(self,selected_label,neighbor_labels):

        self.neigh.setVisible(True)

        selected_label=format_label_with_drug(selected_label,self.aha_drug_map)

        neighbor_labels=[
            format_label_with_drug(label,self.aha_drug_map)
            for label in neighbor_labels
        ]

        self.neigh.show_neighborhood(selected_label,neighbor_labels)

    ###################################################################################################
    # HIDE NEIGHBOR PANEL
    ###################################################################################################

    def hide_neighborhood(self):

        self.neigh.setVisible(False)

        if self.plot is not None:
            self.plot.draw_plot()

#######################################################################################################
# MAIN
#######################################################################################################

def main():
    app=QApplication(sys.argv)
    w=MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__=="__main__":
    main()