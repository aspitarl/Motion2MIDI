import os
import sys
import logging  # Import logging module
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon
from main import MainWindow as SingleMainWindow

from distance_layout import DistanceLayout

script_path = os.path.dirname(os.path.realpath(__file__))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class WindowManagerLayout(QtWidgets.QVBoxLayout):
    def __init__(self, parent):
        super(WindowManagerLayout, self).__init__(parent)
        self.parent = parent
        self.windows = {}

        hlayout = QtWidgets.QHBoxLayout()
        # Create a button to spawn new SingleMainWindow instances
        self.spawn_button = QtWidgets.QPushButton("Spawn New Device Window")
        self.spawn_button.clicked.connect(self.spawn_window)
        hlayout.addWidget(self.spawn_button)

        self.addLayout(hlayout)

        # Create a list widget to display the spawned windows
        self.window_list_widget = QtWidgets.QListWidget()
        self.addWidget(self.window_list_widget)

    def window_closed(self, window_obj):
        window_name = window_obj.name
        logging.debug(f"Window {window_name} closed")
        self.windows.pop(window_name)
        self.update_window_list()
        self.parent.distance_layout.update_window_comboboxes()

    def spawn_window(self):
        window_name = f"Window {len(self.windows) + 1}"
        window = SingleMainWindow(name=window_name)
        self.windows[window_name] = window
        window.closeEvent = lambda event: self.window_closed(window)
        window.show()
        # Position the new window to the side of the main window
        main_window_geometry = self.parent.geometry()
        window.move(main_window_geometry.right() + 10, main_window_geometry.top())

        self.update_window_list()
        self.parent.distance_layout.update_window_comboboxes()

    def update_window_list(self):
        self.window_list_widget.clear()
        # Rename windows to reset the numbering
        for i, window_name in enumerate(sorted(self.windows.keys()), start=1):
            new_name = f"Window {i}"
            window = self.windows.pop(window_name)
            window.name = new_name
            window.update_title()
            self.windows[new_name] = window
            self.window_list_widget.addItem(new_name)

        print(self.windows.keys())
        self.parent.distance_layout.update_window_comboboxes()

class ControlWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(ControlWindow, self).__init__(parent)
        
        self.setWindowIcon(QIcon(os.path.join(script_path, 'icon/icon_multi.png')))
        # Create a central widget and set a vertical layout
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add WindowManagerLayout at the top
        self.window_manager_layout = WindowManagerLayout(parent=self)
        layout.addLayout(self.window_manager_layout)


        # add splitter 
        layout.addWidget(QtWidgets.QSplitter())
        
        self.distance_layout = DistanceLayout(parent=self)
        layout.addLayout(self.distance_layout)

        # Create menu bar
        self.create_menu_bar()

    def create_menu_bar(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu('View')

        self.always_on_top_action = QtWidgets.QAction('Always on Top', self, checkable=True)
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)
        self.always_on_top_action.setShortcut('Ctrl+T')
        view_menu.addAction(self.always_on_top_action)

    def toggle_always_on_top(self, checked):
        if checked:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
        self.show()

    def closeEvent(self, event):
        QtWidgets.QApplication.quit()  # Ensure the program exits when the control window is closed

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    app.setStyleSheet("QFrame { border: 2px solid lightgray; } QLabel { border: none; }")
    # Use the ControlWindow instead of SideBySideMainWindow
    main_window = ControlWindow()
    main_window.show()
    main_window.setWindowTitle("MIDI Motion: Multi Device Window")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()