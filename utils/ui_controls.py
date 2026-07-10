from PyQt5.QtWidgets import QWidget,QHBoxLayout,QLabel,QPushButton,QDoubleSpinBox,QLineEdit

class ControlBar(QWidget):

    def __init__(self,reload_callback,browse_callback):

        super().__init__()

        layout=QHBoxLayout(self)

        layout.setContentsMargins(6,6,6,6)
        layout.setSpacing(8)

        self.perplexity=QDoubleSpinBox()
        self.perplexity.setRange(2.0,200.0)
        self.perplexity.setValue(30.0)

        self.path_edit=QLineEdit()
        self.path_edit.setPlaceholderText("Well embeddings NPZ path")

        browse_btn=QPushButton("Browse NPZ")
        reload_btn=QPushButton("Reload")

        browse_btn.clicked.connect(browse_callback)
        reload_btn.clicked.connect(reload_callback)

        self.path_edit.returnPressed.connect(reload_callback)

        layout.addWidget(QLabel("perplexity"))
        layout.addWidget(self.perplexity)
        layout.addSpacing(18)
        layout.addWidget(QLabel("Well embeddings"))
        layout.addWidget(self.path_edit,1)
        layout.addWidget(browse_btn)
        layout.addWidget(reload_btn)
