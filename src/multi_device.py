import os
import sys
import logging  # Import logging module
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon
from main import MainWindow as SingleMainWindow

from distance_layout import DistanceLayout
from osc_handler import OSCPresetLayout

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
        self.window_table_widget.setHorizontalHeaderLabels(["Name", "Setting", "Controller", "MIDI Port"])
        self.window_table_widget.cellDoubleClicked.connect(self.bring_window_to_front)
        self.window_table_widget.setColumnWidth(0, 50)
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
            #TODO: having to replicate main.py windowCloseEvent here, as we are overriding the closeEvent method
            window.main_widget.datathread.stop()
            window.main_widget.disconnect_objects()
        return close_event

    def update_window_table(self):
        self.window_table_widget.setRowCount(0)

        # Make lists to store the comboboxes for each window
        fileselect_comboboxes = []
        midi_port_comboboxes = []
        controller_comboboxes = []
        # Rename windows to reset the numbering
        for i, window_name in enumerate(sorted(self.windows.keys()), start=1):
            new_name = f"Window {i}"
            window = self.windows.pop(window_name)
            window.name = new_name
            window.update_title()
            self.windows[new_name] = window

            # Add window name and settings fileselect_combobox to the table
            row_position = self.window_table_widget.rowCount()
            self.window_table_widget.insertRow(row_position)
            window_name_item = QtWidgets.QTableWidgetItem(new_name)
            window_name_item.setFlags(window_name_item.flags() & ~QtCore.Qt.ItemIsEditable)  # Make item not editable
            self.window_table_widget.setItem(row_position, 0, window_name_item)
            
            # Clone the fileselect_combobox for the table
            controller_combobox = self.clone_combobox(window.main_widget.connection_layout.combobox_ovr_objects)
            midi_port_combobox = self.clone_combobox(window.main_widget.connection_layout.combobox_midi_ports)
            fileselect_combobox = self.clone_combobox(window.main_widget.settings_layout._fileselect_combo)

            self.window_table_widget.setCellWidget(row_position, 1, fileselect_combobox)
            self.window_table_widget.setCellWidget(row_position, 2, controller_combobox)
            self.window_table_widget.setCellWidget(row_position, 3, midi_port_combobox)
            self.connect_comboboxes(window.main_widget.settings_layout._fileselect_combo, fileselect_combobox)
            self.connect_comboboxes(window.main_widget.connection_layout.combobox_ovr_objects, controller_combobox)
            self.connect_comboboxes(window.main_widget.connection_layout.combobox_midi_ports, midi_port_combobox)

            fileselect_comboboxes.append(fileselect_combobox)
            midi_port_comboboxes.append(midi_port_combobox)
            controller_comboboxes.append(controller_combobox)

        self.parent.distance_layout.update_window_comboboxes()

    def clone_combobox(self, fileselect_combobox):
        combobox_clone = QtWidgets.QComboBox()
        for index in range(fileselect_combobox.count()):
            combobox_clone.addItem(fileselect_combobox.itemText(index))
        combobox_clone.setCurrentIndex(fileselect_combobox.currentIndex())
        return combobox_clone

    def connect_comboboxes(self, combobox1, combobox2):
        #TODO: we are not connecting combobox1. this will keep adding connections from the comboboxes in subwindows to non-existent comboboxes in the table
        # Need to figure out how to disconnect the previous connection
        def update_combobox1(index):
            combobox1.blockSignals(True)
            combobox1.setCurrentIndex(index)
            combobox1.blockSignals(False)

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
        
        # Wrap DistanceLayout in a QWidget
        self.distance_widget = QtWidgets.QWidget()
        self.distance_layout = DistanceLayout(parent=self)
        self.distance_widget.setLayout(self.distance_layout)
        self.distance_widget.setVisible(False)  # Hide by default
        layout.addWidget(self.distance_widget)

        # Wrap OSC preset layout in a QWidget
        self.osc_widget = QtWidgets.QWidget()
        self.osc_preset_layout = OSCPresetLayout(parent=self)
        self.osc_widget.setLayout(self.osc_preset_layout)
        self.osc_widget.setVisible(False)  # Hide by default
        layout.addWidget(self.osc_widget)

        self.osc_preset_layout.osc_preset_table.itemSelectionChanged.connect(self.update_subwindow_settings)

        #TODO: cannot get width to follow the table correctly
        # Set initial width of the main window
        self.setMinimumWidth(380)


        # Create menu bar
        self.create_menu_bar()

    def update_subwindow_settings(self):
        selected_rows = self.osc_preset_layout.osc_preset_table.selectionModel().selectedRows()
        if len(selected_rows) > 0:
            selected_row = selected_rows[0].row()
            selected_preset = self.osc_preset_layout.osc_preset_table.item(selected_row, 0).text()
            logging.debug(f"Selected preset: {selected_preset}")
            for window_num, window in enumerate(self.window_manager_layout.windows.values()):
                fileselect_combobox = window.main_widget.settings_layout._fileselect_combo
                table_preset_name_for_window = self.osc_preset_layout.osc_preset_table.item(selected_row, window_num + 1).text()
                table_preset_name_for_window = table_preset_name_for_window.strip()
                # check if the preset name is in the fileselect_combobox
                if table_preset_name_for_window in [fileselect_combobox.itemText(i) for i in range(fileselect_combobox.count())]:
                    fileselect_combobox.setCurrentText(table_preset_name_for_window)
                    fileselect_combobox.currentIndexChanged.emit(fileselect_combobox.currentIndex())
                else:
                    logging.warning(f"Preset {table_preset_name_for_window} not found in fileselect_combobox for window {window_num + 1}")

    def create_menu_bar(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu('View')

        self.always_on_top_action = QtWidgets.QAction('Always on Top', self, checkable=True)
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)
        self.always_on_top_action.setShortcut('Ctrl+T')
        view_menu.addAction(self.always_on_top_action)

        self.show_distance_layout_action = QtWidgets.QAction('Show Distance Layout', self, checkable=True)
        self.show_distance_layout_action.triggered.connect(self.toggle_distance_layout)
        self.show_distance_layout_action.setChecked(False)  # Not checked by default
        self.show_distance_layout_action.setShortcut('Ctrl+D')  # Add keyboard shortcut
        view_menu.addAction(self.show_distance_layout_action)

        self.show_osc_layout_action = QtWidgets.QAction('Show OSC Layout', self, checkable=True)
        self.show_osc_layout_action.triggered.connect(self.toggle_osc_layout)
        self.show_osc_layout_action.setChecked(False)  # Not checked by default
        self.show_osc_layout_action.setShortcut('Ctrl+O')  # Add keyboard shortcut
        view_menu.addAction(self.show_osc_layout_action)

    #TODO: this is not behaving as expected under multiple toggles
    def toggle_distance_layout(self, checked):
        # get the current height of the main window and distance widget
        main_window_height = self.height()
        distance_widget_height = self.distance_widget.height() 
        self.distance_widget.setVisible(checked)
        # set the height of the main window to the main window height - distance widget height
        if checked:
            default_distance_widget_height = 200
            self.resize(self.width(), main_window_height + default_distance_widget_height)
            self.distance_widget.setMinimumHeight(default_distance_widget_height)
        else:
            self.resize(self.width(), main_window_height - distance_widget_height)

    def toggle_osc_layout(self, checked):
        # get the current height of the main window and osc widget
        main_window_height = self.height()
        osc_widget_height = self.osc_widget.height()
        self.osc_widget.setVisible(checked)
        # set the height of the main window to the main window height - osc widget height
        if checked:
            default_osc_widget_height = 200
            self.resize(self.width(), main_window_height + default_osc_widget_height)
            self.osc_widget.setMinimumHeight(default_osc_widget_height)
        else:
            self.resize(self.width(), main_window_height - osc_widget_height)

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

    # spawn a new window
    main_window.window_manager_layout.spawn_window()
    # main_window.window_manager_layout.spawn_window()

    main_window.show()
    main_window.setWindowTitle("MIDI Motion: Multi Device Window")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()