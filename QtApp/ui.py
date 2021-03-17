# Authors: Victor Ferat <victor.ferat@live.fr>
#
# License: BSD (3-clause)

import multiprocessing as mp
from qtpy.QtCore import (Qt, Slot, QStringListModel, QModelIndex, QSettings,
                         QEvent, QObject, QSize, QPoint, QMetaObject)
from qtpy.QtGui import QKeySequence, QDropEvent, QIcon
from qtpy.QtWidgets import QWidget, QGridLayout, QVBoxLayout,QPushButton, QComboBox, QGroupBox

from .widgets import TopoCanvas

class UiWidget(QWidget):
    """ ui window."""
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.layout1 = QGridLayout()
        self.layout.addLayout(self.layout1, 0, 0, 1, 1)
        self.layout2 = QGridLayout()
        self.layout.addLayout(self.layout2, 0, 1, 2, 3)

        # Layout1
        #   Box Stream
        self.groupBox_stream = QGroupBox("Stream")
        grid = QGridLayout()

        self.Button_refresh = QPushButton('refresh')
        grid.addWidget(self.Button_refresh, 0,4)

        self.QComboBox_stream = QComboBox()
        grid.addWidget(self.QComboBox_stream, 0,0,4, 1)

        self.Button_connect = QPushButton('connect')
        grid.addWidget(self.Button_connect, 2,0)

        self.Button_disconnect = QPushButton('disconnect')
        grid.addWidget(self.Button_disconnect, 2, 1)

        self.groupBox_stream.setLayout(grid)
        self.layout1.addWidget(self.groupBox_stream)

        #   Box ICA
        self.TopoCanvas_ = TopoCanvas()
        self.layout1.addWidget(self.TopoCanvas_, 3,0,1,2)

        self.Button_RS = QPushButton('Compute ICA')
        self.layout1.addWidget(self.Button_RS, 4,0,1,2)

        self.Button_plotICA = QPushButton('Plot ICA')
        self.layout1.addWidget(self.Button_plotICA, 5,0,1,2)

        # Layout2
        self.TopoCanvas_ = TopoCanvas()
        self.layout2.addWidget(self.TopoCanvas_)

        #
        self.setLayout(self.layout)
        
        