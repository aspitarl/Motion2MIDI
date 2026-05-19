import logging
from PyQt5 import QtWidgets, QtCore

header_height = 25

class WindowManagerLayout(QtWidgets.QVBoxLayout):
    def __init__(self, parent):
        super(WindowManagerLayout, self).__init__(parent)
        self.parent = parent
        self.controller_widgets = {}

        hlayout = QtWidgets.QHBoxLayout()
        # Create a button to spawn new controller widgets
        self.spawn_button = QtWidgets.QPushButton("Add New Controller")
        self.spawn_button.clicked.connect(self.add_controller_widget)
        hlayout.addWidget(self.spawn_button)

        self.addLayout(hlayout)

        # Create a scroll area for the table
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_area.setFixedHeight(100)  # Fixed height for scroll area

        # Create a table widget to display the spawned widgets and their settings
        self.controller_table_widget = QtWidgets.QTableWidget(0, 5)
        self.controller_table_widget.setHorizontalHeaderLabels(["Range Set", "Name", "Setting", "Controller", "MIDI Port"])
        self.controller_table_widget.setColumnWidth(0, 80)
        self.controller_table_widget.setColumnWidth(0, 100)
        # Configure table to resize to content
        self.controller_table_widget.verticalHeader().setVisible(False)
        self.controller_table_widget.horizontalHeader().setFixedHeight(header_height)
        self.controller_table_widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.controller_table_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        # Add table to scroll area
        self.scroll_area.setWidget(self.controller_table_widget)
        self.addWidget(self.scroll_area)
        

    def controller_removed(self, widget_name):
        logging.debug(f"Controller widget {widget_name} removed")
        self.controller_widgets.pop(widget_name, None)
        self.update_controller_table()
        if hasattr(self.parent, 'distance_layout'):
            self.parent.distance_layout.update_window_comboboxes()
        # Resize table to fit content after removal
        # Auto-resize main window width
        if hasattr(self.parent, 'adjustSize'):
            self.parent.adjustSize()

    def add_controller_widget(self):
        widget_name = f"Controller {len(self.controller_widgets) + 1}"
        controller_widget = self.parent.add_controller_widget(widget_name)
        controller_widget.range_set_selected = True
        self.controller_widgets[widget_name] = controller_widget
        
        # Add remove button functionality - create a custom widget for each row
        remove_button = QtWidgets.QPushButton("Remove")
        remove_button.clicked.connect(lambda: self.remove_controller_widget(widget_name))
        
        self.update_controller_table()
        if hasattr(self.parent, 'distance_layout'):
            self.parent.distance_layout.update_window_comboboxes()
        # Auto-resize main window width
        if hasattr(self.parent, 'adjustSize'):
            self.parent.adjustSize()

    def remove_controller_widget(self, widget_name):
        if widget_name in self.controller_widgets:
            widget = self.controller_widgets[widget_name]
            self.parent.remove_controller_widget(widget)
            self.controller_removed(widget_name)

    def update_controller_table(self):
        self.controller_table_widget.setRowCount(0)

        # Make lists to store the comboboxes for each controller widget
        fileselect_comboboxes = []
        midi_port_comboboxes = []
        controller_comboboxes = []
        
        # Rename controller widgets to reset the numbering
        for i, widget_name in enumerate(sorted(self.controller_widgets.keys()), start=1):
            new_name = f"Controller {i}"
            widget = self.controller_widgets.pop(widget_name)
            widget.name = new_name
            if not hasattr(widget, 'range_set_selected'):
                widget.range_set_selected = True
            # Update the widget's internal name label
            name_label = widget.findChild(QtWidgets.QLabel)
            if name_label and hasattr(name_label, 'setText'):
                name_label.setText(f"<b>{new_name}</b>")
            self.controller_widgets[new_name] = widget

            # Add controller widget name and settings to the table
            row_position = self.controller_table_widget.rowCount()
            self.controller_table_widget.insertRow(row_position)
            self.controller_table_widget.setRowHeight(row_position, 30)  # Set compact row height

            range_set_checkbox = QtWidgets.QCheckBox()
            range_set_checkbox.setChecked(widget.range_set_selected)
            range_set_checkbox.stateChanged.connect(
                lambda state, controller_widget=widget: setattr(controller_widget, 'range_set_selected', bool(state))
            )
            range_set_widget = QtWidgets.QWidget()
            range_set_layout = QtWidgets.QHBoxLayout(range_set_widget)
            range_set_layout.setContentsMargins(0, 0, 0, 0)
            range_set_layout.setAlignment(QtCore.Qt.AlignCenter)
            range_set_layout.addWidget(range_set_checkbox)
            self.controller_table_widget.setCellWidget(row_position, 0, range_set_widget)
            
            # Controller name (with remove button)
            name_widget = QtWidgets.QWidget()
            name_layout = QtWidgets.QHBoxLayout(name_widget)
            name_layout.setContentsMargins(2, 2, 2, 2)
            
            name_label = QtWidgets.QLabel(new_name)
            remove_button = QtWidgets.QPushButton("×")
            remove_button.setFixedSize(20, 20)
            remove_button.clicked.connect(lambda checked, name=new_name: self.remove_controller_widget(name))
            
            name_layout.addWidget(name_label)
            name_layout.addWidget(remove_button)
            name_layout.addStretch()
            
            self.controller_table_widget.setCellWidget(row_position, 1, name_widget)
            
            # Clone the comboboxes for the table
            controller_combobox = self.clone_combobox(widget.connection_layout.combobox_ovr_objects)
            midi_port_combobox = self.clone_combobox(widget.connection_layout.combobox_midi_ports)
            fileselect_combobox = self.clone_combobox(widget.settings_layout._fileselect_combo)

            self.controller_table_widget.setCellWidget(row_position, 2, fileselect_combobox)
            self.controller_table_widget.setCellWidget(row_position, 3, controller_combobox)
            self.controller_table_widget.setCellWidget(row_position, 4, midi_port_combobox)
            
            self.connect_comboboxes(widget.settings_layout._fileselect_combo, fileselect_combobox)
            self.connect_comboboxes(widget.connection_layout.combobox_ovr_objects, controller_combobox)
            self.connect_comboboxes(widget.connection_layout.combobox_midi_ports, midi_port_combobox)

            fileselect_comboboxes.append(fileselect_combobox)
            midi_port_comboboxes.append(midi_port_combobox)
            controller_comboboxes.append(controller_combobox)

        if hasattr(self.parent, 'distance_layout'):
            self.parent.distance_layout.update_window_comboboxes()

    def get_targeted_controller_widgets(self):
        return [
            widget for widget in self.controller_widgets.values()
            if getattr(widget, 'range_set_selected', True)
        ]
        

    def clone_combobox(self, original_combobox):
        combobox_clone = QtWidgets.QComboBox()
        combobox_clone.setMaximumHeight(25)  # Set compact height
        for index in range(original_combobox.count()):
            combobox_clone.addItem(original_combobox.itemText(index))
        combobox_clone.setCurrentIndex(original_combobox.currentIndex())
        return combobox_clone

    def connect_comboboxes(self, original_combobox, table_combobox):
        #TODO: we are not connecting original_combobox. this will keep adding connections from the comboboxes in subwidgets to non-existent comboboxes in the table
        # Need to figure out how to disconnect the previous connection
        def update_original_combobox(index):
            original_combobox.blockSignals(True)
            original_combobox.setCurrentIndex(index)
            original_combobox.blockSignals(False)
        table_combobox.currentIndexChanged.connect(update_original_combobox)


