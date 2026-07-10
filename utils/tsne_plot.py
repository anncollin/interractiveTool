import numpy as np
from scipy.spatial import cKDTree

from PyQt5.QtWidgets import QWidget,QVBoxLayout,QMenu,QLabel,QDialog,QListWidget,QListWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor,QBrush

import matplotlib
import fastplotlib as fpl

from config import DISTANCE



class TSNEPlot(QWidget):

    calibration_map={
        "001001":"DMSO","001002":"DMSO","001023":"DMSO","001024":"DMSO",
        "002001":"DMSO","002002":"DMSO","002023":"DMSO","002024":"DMSO",
        "003001":"ActD_0.3","003002":"ActD_0.3","003023":"ActD_0.3","003024":"ActD_0.3",
        "004001":"BMH-21_2","004002":"BMH-21_2","004023":"BMH-21_2","004024":"BMH-21_2",
        "005001":"CAM_25","005002":"CAM_25","005023":"CAM_25","005024":"CAM_25",
        "006001":"CX-5461_10","006002":"CX-5461_10","006023":"CX-5461_10","006024":"CX-5461_10",
        "007001":"DIN_5","007002":"DIN_5","007023":"DIN_5","007024":"DIN_5",
        "008001":"DOX_5","008002":"DOX_5","008023":"DOX_5","008024":"DOX_5",
        "009001":"DRB_200","009002":"DRB_200","009023":"DRB_200","009024":"DRB_200",
        "010001":"ETO_500","010002":"ETO_500","010023":"ETO_500","010024":"ETO_500",
        "011001":"FLA_1.2","011002":"FLA_1.2","011023":"FLA_1.2","011024":"FLA_1.2",
        "012001":"HES_5","012002":"HES_5","012023":"HES_5","012024":"HES_5",
        "013001":"MEN_40","013002":"MEN_40","013023":"MEN_40","013024":"MEN_40",
        "014001":"MIT_3","014002":"MIT_3","014023":"MIT_3","014024":"MIT_3",
        "015001":"PLU_20","015002":"PLU_20","015023":"PLU_20","015024":"PLU_20",
        "016001":"t-BHP_100","016002":"t-BHP_100","016023":"t-BHP_100","016024":"t-BHP_100"
    }

    ###################################################################################################
    # INIT
    ###################################################################################################

    def __init__(self,neighbor_panel_callback=None):

        super().__init__()

        self.labels=None
        self.X=None
        self.Y=None
        self.scatter=None
        self.hover_idx=None
        self.tree=None
        self.neighbor_panel_callback=neighbor_panel_callback
        self.legend_dialog=None
        self.legend_shown_once=False

        self.fig=fpl.Figure()
        self.ax=self.fig[0,0]
        self.canvas=self.fig.show()

        lay=QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.setSpacing(0)
        lay.addWidget(self.canvas)

        self.hover_label=QLabel(self)
        self.hover_label.setStyleSheet("""
            QLabel {
                color: black;
                background-color: white;
                border: 1px solid black;
                padding: 4px;
            }
        """)
        self.hover_label.hide()

        self.canvas.add_event_handler(self.on_pointer_move,"pointer_move")
        self.canvas.add_event_handler(self.on_click,"pointer_down")
        self.canvas.add_event_handler(self.on_wheel,"wheel")

    ###################################################################################################
    # SET DATA
    ###################################################################################################

    def set_data(self,Y,labels,X):

        self.Y=np.asarray(Y,dtype=np.float32)
        self.labels=list(map(str,labels))
        self.X=np.asarray(X)
        self.tree=cKDTree(self.Y)

        self.draw_plot()

    ###################################################################################################
    # GET DRUG COLORS
    ###################################################################################################

    def _get_drug_to_color(self):

        calibration_drugs = sorted(set(self.calibration_map.values()))
        cmap = matplotlib.colormaps["tab20"].resampled(len(calibration_drugs))

        drug_to_color={
            drug:np.asarray(cmap(i),dtype=np.float32)
            for i,drug in enumerate(calibration_drugs)
        }

        return drug_to_color

    ###################################################################################################
    # DRAW PLOT
    ###################################################################################################

    def draw_plot(self):

        if self.Y is None:
            return

        self.ax.clear()

        n=len(self.Y)

        colors=np.zeros((n,4),dtype=np.float32)
        colors[:,0]=0.7
        colors[:,1]=0.7
        colors[:,2]=0.7
        colors[:,3]=0.25

        drug_to_color=self._get_drug_to_color()

        for i,label in enumerate(self.labels):

            parts=label.split("_")

            if len(parts)<3:
                continue

            well=parts[-1]

            if well not in self.calibration_map:
                continue

            drug=self.calibration_map[well]
            colors[i]=drug_to_color[drug]

        self.scatter=self.ax.add_scatter(
            data=self.Y,
            colors=colors,
            sizes=6
        )

        if not self.legend_shown_once:
            self._show_calibration_legend(drug_to_color)
            self.legend_shown_once=True

    ###################################################################################################
    # POINTER MOVE
    ###################################################################################################

    def on_pointer_move(self,event):

        if self.Y is None or self.tree is None:
            return

        x_screen=event.get("x",None)
        y_screen=event.get("y",None)

        if x_screen is None or y_screen is None:
            return

        world=self.ax.map_screen_to_world((x_screen,y_screen))

        if world is None:
            self.hover_idx=None
            self.hover_label.hide()
            return

        x=float(world[0])
        y=float(world[1])

        dist,idx=self.tree.query([x,y],k=1)

        if dist<1.5:

            self.hover_idx=int(idx)
            self.hover_label.setText(self.labels[idx])
            self.hover_label.adjustSize()
            self.hover_label.move(int(x_screen)+15,int(y_screen)+15)
            self.hover_label.show()
            self.hover_label.raise_()

        else:

            self.hover_idx=None
            self.hover_label.hide()

    ###################################################################################################
    # CLICK
    ###################################################################################################

    def on_click(self,event):

        if self.hover_idx is None:
            return

        if event.get("button",None)!=2:
            return

        menu=QMenu(self)
        act=menu.addAction("Explore neighborhood")
        chosen=menu.exec_(self.cursor().pos())

        if chosen==act:
            self._explore_neighborhood_from_idx(self.hover_idx,k=30)

    ###################################################################################################
    # WHEEL
    ###################################################################################################

    def on_wheel(self,event):

        modifiers=event.get("modifiers",[])

        if "Control" not in modifiers and "Ctrl" not in modifiers:
            event["handled"]=True
            return

    ###################################################################################################
    # EXPLORE NEIGHBORHOOD
    ###################################################################################################

    def _explore_neighborhood_from_idx(self,idx,k=10):

        neighbors=self._nearest_neighbors(idx,k=k)
        neighbor_labels=[self.labels[i] for i in neighbors]

        self._highlight_selection_and_neighbors(idx,neighbors)

        if self.neighbor_panel_callback:
            self.neighbor_panel_callback(self.labels[idx],neighbor_labels)

    ###################################################################################################
    # COMPUTE NEAREST NEIGHBORS
    ###################################################################################################

    def _nearest_neighbors(self,idx,k=10):

        if DISTANCE=="euclidean":
            x=self.X[idx]
            d=np.sum((self.X-x)**2,axis=1)
            d[idx]=np.inf
            order=np.argsort(d)
            return order[:k]

        elif DISTANCE=="cosine":
            norms=np.linalg.norm(self.X,axis=1,keepdims=True)
            norms[norms==0]=1.0
            Xn=self.X/norms
            similarity=Xn@Xn[idx]
            similarity[idx]=-np.inf
            order=np.argsort(-similarity)
            return order[:k]

        else:
            raise ValueError(f"Unknown DISTANCE='{DISTANCE}'")

    ###################################################################################################
    # HIGHLIGHT
    ###################################################################################################

    def _highlight_selection_and_neighbors(self,selected_idx,neighbor_indices):

        self.draw_plot()

        if len(neighbor_indices)>0:

            neighbor_points=self.Y[neighbor_indices]

            neighbor_colors=np.zeros((len(neighbor_points),4),dtype=np.float32)
            neighbor_colors[:,0]=1.0
            neighbor_colors[:,1]=0.0
            neighbor_colors[:,2]=0.0
            neighbor_colors[:,3]=1.0

            self.ax.add_scatter(
                data=neighbor_points,
                colors=neighbor_colors,
                sizes=12
            )

        selected_point=self.Y[selected_idx:selected_idx+1]

        selected_colors=np.zeros((1,4),dtype=np.float32)
        selected_colors[:,0]=1.0
        selected_colors[:,1]=1.0
        selected_colors[:,2]=0.0
        selected_colors[:,3]=1.0

        self.ax.add_scatter(
            data=selected_point,
            colors=selected_colors,
            sizes=20
        )

    ###################################################################################################
    # CALIBRATION LEGEND
    ###################################################################################################

    def _show_calibration_legend(self,drug_to_color):

        dlg=QDialog(self)
        dlg.setWindowTitle("Calibration drugs")

        lay=QVBoxLayout(dlg)

        lst=QListWidget()

        for drug,color_rgba in drug_to_color.items():

            rgb=(255*np.asarray(color_rgba[:3])).astype(int)

            item=QListWidgetItem(drug)

            item.setForeground(
                QBrush(
                    QColor(
                        int(rgb[0]),
                        int(rgb[1]),
                        int(rgb[2])
                    )
                )
            )

            lst.addItem(item)

        lay.addWidget(lst)

        dlg.resize(220,400)
        dlg.show()

        self.legend_dialog=dlg

    ###################################################################################################
    # FOCUS LABEL
    ###################################################################################################

    def focus_label(self,label,k=10):

        if self.labels is None:
            return

        if label not in self.labels:
            print("Label not found :",label)
            return

        idx=self.labels.index(label)

        self._explore_neighborhood_from_idx(idx,k=k)