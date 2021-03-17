# Authors: Victor Ferat <victor.ferat@live.fr>
#
# License: BSD (3-clause)

import sys
import os
import multiprocessing as mp
import matplotlib
from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt

from . import MainWindow, Model

def _run():
    app_name = "QtApp"
    matplotlib.use("Qt5Agg")
    app = QApplication(sys.argv)
    app.setApplicationName(app_name)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    model = Model()
    model.view = MainWindow(model)
    model.view.show()
    sys.exit(app.exec_())


def main():
    # Ensure we're always using a "framework build" on macOS.
    _MACOS_CONDA = sys.platform == "darwin" and "CONDA_PREFIX" in os.environ
    _RUNNING_PYTHONW = "MNELAB_RUNNING_PYTHONW" in os.environ

    if _MACOS_CONDA and not _RUNNING_PYTHONW:
        _run_pythonw()
    else:
        _run()


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)  # required for Linux/macOS
    _run()