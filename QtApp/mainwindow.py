# Authors: Victor Ferat <victor.ferat@live.fr>
#
# License: BSD (3-clause)
from qtpy.QtCore import (Qt, Slot, QStringListModel, QModelIndex, QSettings,
                         QEvent, QObject, QSize, QPoint, QMetaObject, Signal)
from qtpy.QtGui import QKeySequence, QDropEvent, QIcon
from qtpy.QtWidgets import (QApplication, QMainWindow, QFileDialog, QSplitter,
                            QMessageBox, QListView, QAction, QLabel, QFrame)

from .ui import UiWidget

import matplotlib
matplotlib.use('qt5agg')

class MainWindow(QMainWindow):
    """main window."""
    def __init__(self, model):
        super().__init__()
        self.model = model  # data model
        self.setWindowTitle("QtApp")
        self.UiWidget = UiWidget()
        self.setCentralWidget(self.UiWidget)

        self.connected = False
        self.previous_connected = False
        # trigger theme setting
        self.actions = {}  # contains all actions
        self.actions['resolve_streams'] = self.UiWidget.Button_refresh.clicked.connect(
                                                lambda: self.model.get_available_streams())
        
        self.actions['connect_stream'] = self.UiWidget.Button_connect.clicked.connect(
                                        lambda: self.model.connect())

        self.actions['disconnect_stream'] = self.UiWidget.Button_disconnect.clicked.connect(
                                                lambda: self.model.disconnect())

        self.actions['make_RS'] = self.UiWidget.Button_RS.clicked.connect(
                                                lambda: self.restingstate())
        self.actions['plot_ica'] = self.UiWidget.Button_plotICA.clicked.connect(
                                                lambda: self.plot_ica())
        # Add the callbackfunc to ..
        self.model.mySrc.data_signal.connect(self.UiWidget.TopoCanvas_._set_data)

        self.data_changed()
        self.show()

    def data_changed(self):
        # update sidebar
        self.UiWidget.QComboBox_stream.clear()
        self.UiWidget.QComboBox_stream.addItems([stream.name() for stream in self.model.available_streams])
        self.UiWidget.TopoCanvas_.info = self.model.info
        return()

    def restingstate(self):
        self.model.set_restingstate_data()
        self.model.run_ica()

    def plot_ica(self):
        fig = self.model.ica.plot_components(inst=self.model.set_restingstate_data,
                                             show=False)
        fig[0].show()

        

