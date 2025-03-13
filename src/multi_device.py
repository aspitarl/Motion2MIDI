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

        # Create a table widget to display the spawned windows and their settings
        self.window_table_widget = QtWidgets.QTableWidget(0, 4)
        self.window_table_widget.setHorizontalHeaderLabels(["Window Name", "Settings ComboBox", "Controller", "MIDI Port"])
        self.window_table_widget.cellDoubleClicked.connect(self.bring_window_to_front)
        self.addWidget(self.window_table_widget)

    def window_closed(self, window_obj):
        window_name = window_obj.name
        logging.debug(f"Window {window_name} closed")
        self.windows.pop(window_name)
        self.update_window_table()
        self.parent.distance_layout.update_window_comboboxes()

    def spawn_window(self):
        window_name = f"Window {len(self.windows) + 1}"
        window = SingleMainWindow(name=window_name)
        self.windows[window_name] = window
        window.closeEvent = self.create_close_event(window)
        window.show()
        # Position the new window to the side of the main window
        main_window_geometry = self.parent.geometry()
        window.move(main_window_geometry.right() + 10, main_window_geometry.top())

        self.update_window_table()
        self.parent.distance_layout.update_window_comboboxes()

    def create_close_event(self, window):
        def close_event(event):
            self.window_closed(window)
        return close_event

    def update_window_table(self):
        self.window_table_widget.setRowCount(0)
        # Rename windows to reset the numbering
        for i, window_name in enumerate(sorted(self.windows.keys()), start=1):
            new_name = f"Window {i}"
            window = self.windows.pop(window_name)
            window.name = new_name
            window.update_title()
            self.windows[new_name] = window

            # Add window name and settings combobox to the table
            row_position = self.window_table_widget.rowCount()
            self.window_table_widget.insertRow(row_position)
            window_name_item = QtWidgets.QTableWidgetItem(new_name)
            window_name_item.setFlags(window_name_item.flags() & ~QtCore.Qt.ItemIsEditable)  # Make item not editable
            self.window_table_widget.setItem(row_position, 0, window_name_item)
            
            # Clone the combobox for the table
            combobox = window.main_widget.settings_layout._fileselect_combo
            combobox_clone = self.clone_combobox(combobox)
            self.window_table_widget.setCellWidget(row_position, 1, combobox_clone)
            self.connect_comboboxes(combobox, combobox_clone)

            # Clone the controller, MIDI port, and MIDI channel comboboxes for the table
            controller_combobox = self.clone_combobox(window.main_widget.connection_layout.combobox_ovr_objects)
            midi_port_combobox = self.clone_combobox(window.main_widget.connection_layout.combobox_midi_ports)
            self.window_table_widget.setCellWidget(row_position, 2, controller_combobox)
            self.window_table_widget.setCellWidget(row_position, 3, midi_port_combobox)
            self.connect_comboboxes(window.main_widget.connection_layout.combobox_ovr_objects, controller_combobox)
            self.connect_comboboxes(window.main_widget.connection_layout.combobox_midi_ports, midi_port_combobox)

        self.parent.distance_layout.update_window_comboboxes()

    def clone_combobox(self, combobox):
        combobox_clone = QtWidgets.QComboBox()
        for index in range(combobox.count()):
            combobox_clone.addItem(combobox.itemText(index))
        combobox_clone.setCurrentIndex(combobox.currentIndex())
        return combobox_clone

    def connect_comboboxes(self, combobox1, combobox2):
        def update_combobox2(index):
            combobox2.blockSignals(True)
            combobox2.setCurrentIndex(index)
            combobox2.blockSignals(False)

        def update_combobox1(index):
            combobox1.blockSignals(True)
            combobox1.setCurrentIndex(index)
            combobox1.blockSignals(False)

        combobox1.currentIndexChanged.connect(update_combobox2)
        combobox2.currentIndexChanged.connect(update_combobox1)

    def bring_window_to_front(self, row, column):
        window_name = self.window_table_widget.item(row, 0).text()
        window = self.windows[window_name]
        print(f"Bringing {window_name} to front")
        window.raise_()
        window.activateWindow()

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