import os
import logging
import sys
import mido

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon

from m2m.gui.layouts.distance_layout import DistanceLayout
from m2m.core.osc_handler import OSCPresetLayout
from m2m.gui.layouts.window_manager import WindowManagerLayout
from m2m.gui.widgets.midi_listener import MidiListenerWindow
from m2m.gui.widgets.debug_console import DebugConsoleWindow
from m2m.gui.widgets.error_dialog import ErrorLogger
from m2m.utils.about import show_about_dialog

script_path = os.path.dirname(os.path.realpath(__file__))

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
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
        
        # Add horizontal layout for controller widgets with scroll support
        self.controllers_scroll = QtWidgets.QScrollArea()
        self.controllers_widget = QtWidgets.QWidget()
        self.controllers_layout = QtWidgets.QHBoxLayout(self.controllers_widget)
        self.controllers_layout.setContentsMargins(10, 10, 10, 10)  # Increased margins
        self.controllers_layout.setSpacing(15)  # Increased spacing between controllers
        
        self.controllers_scroll.setWidget(self.controllers_widget)
        self.controllers_scroll.setWidgetResizable(True)
        self.controllers_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.controllers_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.controllers_scroll.setMinimumHeight(400)  # Increased from 200
        
        layout.addWidget(self.controllers_scroll)
        
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


        # Create menu bar
        self.create_menu_bar()
        
        # Initialize utility windows
        self.midi_listener_window = MidiListenerWindow(parent=self)
        self.midi_listener_window.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.midi_listener_window.hide()

        self.debug_console_window = DebugConsoleWindow(parent=self)
        self.debug_console_window.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.debug_console_window.hide()
        
        # Set up the error logger
        self.error_logger = ErrorLogger(always_on_top=self.always_on_top_action.isChecked())
        sys.excepthook = self.error_logger.handle_exception

    def update_subwindow_settings(self):
        selected_rows = self.osc_preset_layout.osc_preset_table.selectionModel().selectedRows()
        if len(selected_rows) > 0:
            selected_row = selected_rows[0].row()
            selected_preset = self.osc_preset_layout.osc_preset_table.item(selected_row, 0).text()
            logging.debug(f"Selected preset: {selected_preset}")
            for widget_num, widget in enumerate(self.window_manager_layout.controller_widgets.values()):
                fileselect_combobox = widget.settings_layout._fileselect_combo
                table_preset_name_for_widget = self.osc_preset_layout.osc_preset_table.item(selected_row, widget_num + 1).text()
                table_preset_name_for_widget = table_preset_name_for_widget.strip()
                # check if the preset name is in the fileselect_combobox
                if table_preset_name_for_widget in [fileselect_combobox.itemText(i) for i in range(fileselect_combobox.count())]:
                    fileselect_combobox.setCurrentText(table_preset_name_for_widget)
                    fileselect_combobox.currentIndexChanged.emit(fileselect_combobox.currentIndex())
                else:
                    logging.warning(f"Preset {table_preset_name_for_widget} not found in fileselect_combobox for controller widget {widget_num + 1}")

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

        # Add Utility menu for controller-related features
        utility_menu = menubar.addMenu('Utility')
        
        # Add 'Range Set Mode' action - affects all controllers
        self.range_set_action = QtWidgets.QAction('Range Set Mode (All Controllers)', self, checkable=True)
        self.range_set_action.triggered.connect(self.toggle_range_set_mode)
        self.range_set_action.setShortcut('Ctrl+R')
        utility_menu.addAction(self.range_set_action)

        # Add MIDI Listener action
        self.toggle_midi_listener_action = QtWidgets.QAction('Open/Close MIDI Listener', self)
        self.toggle_midi_listener_action.triggered.connect(self.toggle_midi_listener)
        self.toggle_midi_listener_action.setShortcut('Ctrl+M')
        utility_menu.addAction(self.toggle_midi_listener_action)

        # Add Debug Console action
        self.toggle_debug_console_action = QtWidgets.QAction('Open/Close Debug Console', self)
        self.toggle_debug_console_action.triggered.connect(self.toggle_debug_console)
        self.toggle_debug_console_action.setShortcut('Ctrl+Shift+D')  # Changed shortcut to avoid conflict
        utility_menu.addAction(self.toggle_debug_console_action)

        # Add Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QtWidgets.QAction('About', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

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
        self.error_logger.always_on_top = checked

    def toggle_range_set_mode(self, checked):
        """Toggle range set mode for all controller widgets"""
        for widget in self.window_manager_layout.controller_widgets.values():
            if checked:
                widget.datathread.active_mode_manual_bypass = True
                widget.datathread.manual_range_set = checked
            else:
                widget.datathread.manual_range_set = checked

    def toggle_midi_listener(self):
        """Toggle the MIDI listener window"""
        if self.midi_listener_window.isVisible():
            self.midi_listener_window.close()
        else:
            # Update controller reference before showing
            self.midi_listener_window.update_controller_reference()
            self.midi_listener_window.show()
            # Try to find a corresponding input port for the first connected controller
            for widget in self.window_manager_layout.controller_widgets.values():
                if widget.is_connected():
                    current_output_port = widget.connection_layout.combobox_midi_ports.currentText()
                    current_output_port_base = current_output_port.split(' ')[0]
                    input_ports = mido.get_input_names()
                    for port in input_ports:
                        if port.startswith(current_output_port_base):
                            print(f"Found corresponding input port: {port}")
                            self.midi_listener_window.midi_port_combobox.setCurrentText(port)
                    break
            
            self.activateWindow()
            main_window_geometry = self.geometry()
            self.midi_listener_window.move(main_window_geometry.right(), main_window_geometry.top())

    def toggle_debug_console(self):
        """Toggle the debug console window"""
        if self.debug_console_window.isVisible():
            self.debug_console_window.close()
            # Disable debug for all controllers
            for widget in self.window_manager_layout.controller_widgets.values():
                widget.datathread.enable_debug = False
        else:
            self.debug_console_window.show()
            # Enable debug for all controllers
            for widget in self.window_manager_layout.controller_widgets.values():
                widget.datathread.debug_signal.connect(self.debug_console_window.setText)
                widget.datathread.enable_debug = True

    def show_about_dialog(self):
        """Show the about dialog"""
        show_about_dialog(self)

    def closeEvent(self, event):
        # Clean up all controller widgets before closing
        for i in range(self.controllers_layout.count()):
            widget = self.controllers_layout.itemAt(i).widget()
            if hasattr(widget, 'cleanup'):
                widget.cleanup()
        QtWidgets.QApplication.quit()  # Ensure the program exits when the control window is closed

    def add_controller_widget(self, name):
        """Add a new controller widget to the horizontal layout"""
        from m2m.gui.widgets.controller_widget import ControllerWidget
        controller_widget = ControllerWidget(name=name, parent=self)
        controller_widget.title_update_requested.connect(self.update_title)
        
        # Add vertical line separator if not the first widget
        if self.controllers_layout.count() > 0:
            separator = QtWidgets.QFrame()
            separator.setFrameShape(QtWidgets.QFrame.VLine)
            separator.setFrameShadow(QtWidgets.QFrame.Sunken)
            separator.setFixedWidth(2)
            self.controllers_layout.addWidget(separator)
        
        self.controllers_layout.addWidget(controller_widget)
        # Ensure the scroll area updates its size
        self.controllers_widget.updateGeometry()
        return controller_widget

    def remove_controller_widget(self, widget):
        """Remove a controller widget from the horizontal layout"""
        widget.cleanup()
        
        # Find and remove the widget and its separator
        index = -1
        for i in range(self.controllers_layout.count()):
            if self.controllers_layout.itemAt(i).widget() == widget:
                index = i
                break
        
        if index >= 0:
            # Remove the widget
            self.controllers_layout.removeWidget(widget)
            widget.deleteLater()
            
            # Remove separator if exists (either before or after)
            if index > 0:  # Remove separator before this widget
                separator = self.controllers_layout.itemAt(index - 1).widget()
                if isinstance(separator, QtWidgets.QFrame):
                    self.controllers_layout.removeWidget(separator)
                    separator.deleteLater()
            elif self.controllers_layout.count() > 0:  # Remove separator after if this was first
                separator = self.controllers_layout.itemAt(0).widget()
                if isinstance(separator, QtWidgets.QFrame):
                    self.controllers_layout.removeWidget(separator)
                    separator.deleteLater()
        
        # Ensure the scroll area updates its size
        self.controllers_widget.updateGeometry()

    def update_title(self):
        """Update the main window title based on connected controllers"""
        connected_controllers = []
        for i in range(self.controllers_layout.count()):
            widget = self.controllers_layout.itemAt(i).widget()
            if hasattr(widget, 'is_connected') and widget.is_connected():
                connected_controllers.append(widget.get_controller_name())
        
        if connected_controllers:
            title = f"Motion2MIDI Multi - {', '.join(connected_controllers)}"
        else:
            title = "Motion2MIDI Multi"
        
        self.setWindowTitle(title)
