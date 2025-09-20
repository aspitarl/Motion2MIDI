import os
import sys
import logging

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon

from m2m.gui.main_window import MainWindow


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    app.setStyleSheet("QFrame { border: 2px solid lightgray; } QLabel { border: none; }")
    # Use the MainWindow instead of SideBySideMainWindow
    main_window = MainWindow()

    # spawn a new window
    main_window.window_manager_layout.spawn_window()
    main_window.window_manager_layout.spawn_window()

    main_window.show()
    main_window.setWindowTitle("MIDI Motion: Multi Device Window")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()