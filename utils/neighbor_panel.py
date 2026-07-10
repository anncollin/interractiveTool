import os
import re

from PyQt5.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QFrame,QScrollArea,QPushButton,QGridLayout,QComboBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from config import IMG_ROOT

#######################################################################################################
# NEIGHBOR PANEL
#######################################################################################################

class NeighborPanel(QFrame):

    def __init__(self,close_callback=None):

        super().__init__()

        # Stored selection
        self.selected_label=None
        self.neighbor_labels=[]

        # Close callback
        self.close_callback=close_callback

        # Panel style
        self.setStyleSheet("background-color: #f8f8f8;")

        # Main layout
        self.main_layout=QVBoxLayout(self)
        self.main_layout.setContentsMargins(15,15,15,15)
        self.main_layout.setSpacing(15)

        # Top controls
        top_row=QHBoxLayout()
        top_row.addWidget(QLabel("Show"))
        self.neighbor_count_combo=QComboBox()
        self.neighbor_count_combo.addItems(["5","10","20","30"])
        self.neighbor_count_combo.setCurrentText("10")
        self.neighbor_count_combo.currentTextChanged.connect(self._on_neighbor_count_changed)
        top_row.addWidget(self.neighbor_count_combo)
        self.neighbor_count_label=QLabel("Showing 0 / 0 neighbors")
        top_row.addWidget(self.neighbor_count_label)
        top_row.addStretch()
        close_btn=QPushButton("Close panel")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self._on_close_clicked)
        top_row.addWidget(close_btn)
        self.main_layout.addLayout(top_row)

        # Selection block
        self.selection_block=None

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area,1)

        

    ###################################################################################################
    # CLOSE
    ###################################################################################################

    def _on_close_clicked(self):

        if self.close_callback:
            self.close_callback()
        else:
            self.setVisible(False)

    ###################################################################################################
    # CLEAR
    ###################################################################################################

    def clear(self):

        if self.selection_block is not None:

            self.main_layout.removeWidget(self.selection_block)
            self.selection_block.deleteLater()
            self.selection_block=None

        while self.scroll_layout.count()>0:

            item=self.scroll_layout.takeAt(0)

            widget=item.widget()

            if widget:
                widget.deleteLater()
    ###################################################################################################
    # SHOW NEIGHBORHOOD
    ###################################################################################################

    def show_neighborhood(self,selected_label,neighbor_labels):

        self.selected_label=selected_label
        self.neighbor_labels=list(neighbor_labels)

        self._refresh_displayed_neighbors()

    ###################################################################################################
    # REFRESH DISPLAYED NEIGHBORS
    ###################################################################################################

    def _refresh_displayed_neighbors(self):

        self.clear()

        if self.selected_label is None:
            return

        n_to_show=int(self.neighbor_count_combo.currentText())
        shown_neighbors=self.neighbor_labels[:n_to_show]

        self.neighbor_count_label.setText(
            f"Showing {len(shown_neighbors)} / {len(self.neighbor_labels)} closest neighbors"
        )

        self.selection_block=self._make_block("Selection",self.selected_label)

        self.main_layout.insertWidget(1,self.selection_block)

        for i,n in enumerate(shown_neighbors,start=1):

            self.scroll_layout.addWidget(
                self._make_block(f"Neighbor {i}",n)
            )

        self.scroll_layout.addStretch()

    ###################################################################################################
    # NEIGHBOR COUNT CHANGED
    ###################################################################################################

    def _on_neighbor_count_changed(self):

        if self.selected_label is not None:
            self._refresh_displayed_neighbors()

    ###################################################################################################
    # CREATE BLOCK
    ###################################################################################################

    def _make_block(self,title,label_string):

        block=QFrame()

        block.setStyleSheet("""
            background-color: #f4f4f4;
            border: 1px solid #ccc;
        """)

        block_layout=QVBoxLayout(block)
        block_layout.setContentsMargins(10,10,10,10)

        title_label=QLabel()
        title_label.setTextFormat(Qt.RichText)
        title_label.setText(f"{title} : {label_string}")

        title_label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
        """)

        block_layout.addWidget(title_label)

        path_label=re.sub(r"<[^>]+>","",label_string)
        path_label=path_label.split(" (",1)[0]

        grid=QGridLayout()
        grid.setSpacing(2)

        image_paths=self._get_image_paths(path_label)

        for idx,img_path in enumerate(image_paths):

            row=idx//15
            col=idx%15

            img_label=QLabel()

            img_label.setFixedSize(70,70)
            img_label.setAlignment(Qt.AlignCenter)

            img_label.setStyleSheet("""
                border: 1px solid red;
                background-color: black;
            """)

            pix=QPixmap(img_path)

            if not pix.isNull():

                pix=pix.scaled(
                    70,
                    70,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

                img_label.setPixmap(pix)

            else:

                img_label.setText("ERR")

            grid.addWidget(img_label,row,col)

        block_layout.addLayout(grid)

        return block

    ###################################################################################################
    # PARSE LABEL
    ###################################################################################################

    def _parse_label(self,label_string):

        parts=label_string.split("_")

        if len(parts)<3:

            print("Cannot parse :",label_string)

            return None,None,None

        dataset=parts[0]
        well=parts[-1]
        plate="_".join(parts[1:-1])

        return dataset,plate,well

    ###################################################################################################
    # GET IMAGE PATHS
    ###################################################################################################

    def _get_image_paths(self,label_string):

        dataset,plate,well=self._parse_label(label_string)

        if dataset is None:
            return []

        folder=os.path.join(
            IMG_ROOT,
            dataset,
            plate,
            well
        )

        if not os.path.isdir(folder):

            print("Missing folder :",folder)

            return []

        paths=[]

        for i in range(30):

            path=os.path.join(folder,f"cell_{i:03d}.png")

            if os.path.isfile(path):
                paths.append(path)

        return paths