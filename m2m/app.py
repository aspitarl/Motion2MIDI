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
    # Use the MainWindow with embedded controller widgets
    main_window = MainWindow()

    # Add two controller widgets by default
    main_window.window_manager_layout.add_controller_widget()

    main_window.show()
    main_window.resize(500, 500)  # Set larger initial size for multiple controllers with improved proportions
    main_window.setWindowTitle("Motion2MIDI: Multi Device Window")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()