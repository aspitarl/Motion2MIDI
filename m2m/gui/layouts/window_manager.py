import logging
from PyQt5 import QtWidgets, QtCore

from m2m.gui.controller_window import ControllerWindow as SingleControllerWindow


class WindowManagerLayout(QtWidgets.QVBoxLayout):
    def __init__(self, parent):
        super(WindowManagerLayout, self).__init__(parent)
        self.parent = parent
        self.windows = {}

        hlayout = QtWidgets.QHBoxLayout()
        # Create a button to spawn new SingleControllerWindow instances
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
        window = SingleControllerWindow(name=window_name)
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