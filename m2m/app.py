import os
import sys
import logging

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon

from m2m.gui.main_window import MainWindow
from m2m.gui.theme import apply_dark_theme


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    app = QtWidgets.QApplication(sys.argv)
    
    apply_dark_theme(app)
    # Use the MainWindow with embedded controller widgets
    main_window = MainWindow()

    # Add two controller widgets by default

    main_window.show()
    main_window.window_manager_layout.add_controller_widget()
    main_window.setWindowTitle("Motion2MIDI: Multi Device Window")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()