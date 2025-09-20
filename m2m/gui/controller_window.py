from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QSplitter, QMenuBar, QAction, QTextEdit, QSpinBox, QLabel, 
    QMainWindow, QDialog, QComboBox, QPushButton, QWidget, QFrame, QCheckBox, QFileDialog, QMessageBox
)
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QValidator, QCloseEvent, QIcon
import os
import sys
import mido
from mido.backends import rtmidi  # pyinstaller

# Import custom modules
from m2m.core.data_thread import DataThread
from m2m.gui.layouts.connection_layout import ConnectionLayout
from m2m.gui.layouts.settings_layout import SettingsLayout
from m2m.gui.widgets.midi_listener import MidiListenerWindow
from m2m.gui.widgets.debug_console import DebugConsoleWindow
from m2m.gui.widgets.error_dialog import ErrorLogger
from m2m.core.openvr_utils import DeviceCollection, NoDevice 
from m2m.utils.about import show_about_dialog

script_path = os.path.dirname(os.path.realpath(__file__))

class ControllerWidget(QtWidgets.QWidget):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.device_collection = DeviceCollection()
        layout = QVBoxLayout()

        # Connection layout with border
        self.connection_layout = ConnectionLayout(device_collection=self.device_collection)
        self.connection_layout.pushbutton_connect.clicked.connect(self.connect_object)
        self.connection_layout.pushbutton_disconnect.clicked.connect(self.disconnect_objects)
        connection_frame = QFrame()
        connection_frame.setLayout(self.connection_layout)
        layout.addWidget(connection_frame)
        self.connection_layout.discover_openvr_objects()

        # Settings layout with border
        all_settings_layout = QVBoxLayout()
        self.settings_layout = SettingsLayout(parent=self)
        self.settings_layout.checkbox_mobile_box_mode.stateChanged.connect(self.update_device_settings)
        self.settings_layout.checkbox_roll_x_factor.stateChanged.connect(self.update_device_settings)
        self.settings_layout.checkbox_roll_y_factor.stateChanged.connect(self.update_device_settings)
        self.settings_layout.checkbox_enable_haptic.stateChanged.connect(self.update_device_settings)
        self.settings_layout.checkbox_invert_toggle.stateChanged.connect(self.update_device_settings)
        self.settings_layout.checkbox_ymode.stateChanged.connect(self.update_device_settings)
        # Add valueChanged connections for sleep/tolerance widgets
        self.settings_layout.sleep_time_spinbox.valueChanged.connect(self.update_sleep_time)
        self.settings_layout.tolerance_slider.valueChanged.connect(self.update_active_mode_tolerance)
        self.settings_layout.timeout_spinbox.valueChanged.connect(self.update_active_mode_timeout)
        all_settings_layout.addLayout(self.settings_layout)
        settings_frame = QFrame()
        settings_frame.setLayout(all_settings_layout)
        layout.addWidget(settings_frame)

        # Thread for obtaining and sending out data
        self.datathread = DataThread(parent=self)
        self.update_sleep_time(self.settings_layout.sleep_time_spinbox.value())
        self.update_active_mode_tolerance(self.settings_layout.tolerance_slider.value())
        self.update_active_mode_timeout(self.settings_layout.timeout_spinbox.value())
        self.settings_layout.load_data()

        # Add status info display
        status_layout = QHBoxLayout()
        status_label = QLabel("Status messages:")
        status_layout.addWidget(status_label)
        self.status_text_edit = QTextEdit()
        self.status_text_edit.setReadOnly(True)
        self.status_text_edit.setFixedHeight(25)  # Set a fixed height
        status_layout.addWidget(self.status_text_edit)
        layout.addLayout(status_layout)
        self.status_text_edit.setText("Initialized")

        self.datathread.status_signal.connect(self.update_status_text_edit)
        self.datathread.exception_signal.connect(self.handle_datathread_exception)

        self.setLayout(layout)
    
    def update_device_settings(self):
        if self.datathread.contr:
            self.datathread.contr.mobile_box_mode = self.settings_layout.checkbox_mobile_box_mode.isChecked()
            self.datathread.contr.enable_half_y = self.settings_layout.checkbox_ymode.isChecked()
            self.datathread.contr.roll_x_factor = -1 if self.settings_layout.checkbox_roll_x_factor.isChecked() else 1
            self.datathread.contr.roll_y_factor = -1 if self.settings_layout.checkbox_roll_y_factor.isChecked() else 1
            self.datathread.contr.enable_haptic = self.settings_layout.checkbox_enable_haptic.isChecked()
            self.datathread.contr.invert_toggle = self.settings_layout.checkbox_invert_toggle.isChecked()

    def connect_object(self):
        if len(self.device_collection.present_devices) == 0:
            raise Exception("No devices found, cannot connect. Try refreshing the list.")

        controller_idx = self.connection_layout.combobox_ovr_objects.currentIndex()
        midi_port = self.connection_layout.combobox_midi_ports.currentText()

        self.datathread.contr = self.device_collection.present_devices[controller_idx]
        self.datathread.midiout = mido.open_output(midi_port)
        self.datathread.midi_channel = self.connection_layout.combobox_midi_channels.currentIndex()
        self.update_device_settings()
        self.datathread.update_dicts()  # TODO: remove and initialize device with range dict from table
        self.datathread.start()

        self.connection_layout.checkbox_isconnected.setChecked(True)
        self.parent.update_title()

    def disconnect_objects(self):
        if self.datathread.isRunning():
            self.datathread.stop()

        if self.datathread.midiout:
            self.datathread.midiout.close()

        self.datathread.midiout = None
        self.datathread.contr = NoDevice()
        self.connection_layout.checkbox_isconnected.setChecked(False)

        if self.settings_layout.checkbox_invert_toggle.isChecked():
            self.settings_layout.checkbox_invert_toggle.setChecked(False)

        self.parent.update_title()

    def closeEvent(self, event):
        super().closeEvent(event)

    def update_sleep_time(self, value):
        self.datathread.sleep_time = value / 1000.0  # Convert ms to seconds

    def update_active_mode_tolerance(self, value):
        tolerance = value / 100.0
        self.settings_layout.tolerance_value_label.setText(f"{tolerance:.2f}")
        self.datathread.active_mode_tolerance = tolerance
        if tolerance == 0.0:
            self.datathread.active_mode_timeout = None
            self.settings_layout.timeout_spinbox.setEnabled(False)
        else:
            self.settings_layout.timeout_spinbox.setEnabled(True)
            self.datathread.active_mode_timeout = self.settings_layout.timeout_spinbox.value()

    def update_active_mode_timeout(self, value):
        if self.datathread.active_mode_tolerance > 0.0:
            self.datathread.active_mode_timeout = value

    def update_status_text_edit(self, status):
        self.status_text_edit.setText(status)

    def handle_datathread_exception(self, exception):
        self.disconnect_objects()  # TODO: what happens when an exception is thrown here, could be confusing 
        raise exception

class ControllerWindow(QtWidgets.QMainWindow):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowIcon(QIcon(os.path.join(script_path, 'icon/icon.png')))

        self.main_widget = ControllerWidget(self)
        self.setCentralWidget(self.main_widget)
        self.main_widget.connection_layout.combobox_selections_changed.connect(self.connections_changed)

        self.name = name
        self.midi_listener_window = MidiListenerWindow(parent=self)
        self.midi_listener_window.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.midi_listener_window.hide()

        self.debug_console_window = DebugConsoleWindow(parent=self)
        self.debug_console_window.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.debug_console_window.hide()

        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)

        # Add 'View' menu
        viewMenu = menuBar.addMenu('View')

        # Add 'Always on Top' action
        self.always_on_top_action = QAction('Always on Top', self, checkable=True)
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)
        self.always_on_top_action.setShortcut('Ctrl+T')
        viewMenu.addAction(self.always_on_top_action)

        # Add 'Utility' menu
        utilityMenu = menuBar.addMenu('Utility')

        # Add 'Range Set Mode' action
        self.range_set_action = QAction('Range Set Mode', self, checkable=True)
        self.range_set_action.triggered.connect(self.toggle_range_set_mode)
        self.range_set_action.setShortcut('Ctrl+R')
        utilityMenu.addAction(self.range_set_action)

        self.toggle_midi_listener_action = QAction('Open/Close MIDI Listener', self)
        self.toggle_midi_listener_action.triggered.connect(self.toggle_midi_listener)
        self.toggle_midi_listener_action.setShortcut('Ctrl+M')
        utilityMenu.addAction(self.toggle_midi_listener_action)

        self.toggle_debug_console_action = QAction('Open/Close Debug Console', self)
        self.toggle_debug_console_action.triggered.connect(self.toggle_debug_console)
        self.toggle_debug_console_action.setShortcut('Ctrl+D')
        utilityMenu.addAction(self.toggle_debug_console_action)

        # Add 'Help' menu
        helpMenu = menuBar.addMenu('Help')

        # Add 'About' action
        about_action = QAction('About', self)
        about_action.triggered.connect(lambda: show_about_dialog(self))
        helpMenu.addAction(about_action)

        # Set up the error logger
        self.error_logger = ErrorLogger(always_on_top=self.always_on_top_action.isChecked())
        sys.excepthook = self.error_logger.handle_exception

        self.update_title()

    def connections_changed(self):
        # if connected then disconnect and reconnect
        if self.main_widget.connection_layout.checkbox_isconnected.isChecked():
            self.main_widget.disconnect_objects()
            self.main_widget.connect_object()
        self.update_title()

    def toggle_always_on_top(self, state):
        if self.always_on_top_action.isChecked():
            self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, False)
        self.show()
        self.error_logger.always_on_top = self.always_on_top_action.isChecked()

    def toggle_range_set_mode(self, state):
        if state:
            self.main_widget.datathread.active_mode_manual_bypass = True
            self.main_widget.datathread.manual_range_set = state
        else:
            self.main_widget.datathread.manual_range_set = state

    def toggle_midi_listener(self):
        if self.midi_listener_window.isVisible():
            self.midi_listener_window.close()
        else:
            self.midi_listener_window.show()
            current_output_port = self.main_widget.connection_layout.combobox_midi_ports.currentText()
            current_output_port_base = current_output_port.split(' ')[0]
            input_ports = mido.get_input_names()
            for port in input_ports:
                if port.startswith(current_output_port_base):
                    print(f"Found corresponding input port: {port}")
                    self.midi_listener_window.midi_port_combobox.setCurrentText(port)
            self.activateWindow()
            main_window_geometry = self.geometry()
            midi_listener_geometry = self.midi_listener_window.geometry()
            self.midi_listener_window.move(main_window_geometry.right(), main_window_geometry.top())

    def toggle_debug_console(self):
        if self.debug_console_window.isVisible():
            self.debug_console_window.close()
            self.main_widget.datathread.enable_debug = False
        else:
            self.debug_console_window.show()
            self.main_widget.datathread.debug_signal.connect(self.debug_console_window.setText)
            self.main_widget.datathread.enable_debug = True

    def closeEvent(self, a0: QCloseEvent) -> None:
        print('Received Close event, Disconnecting Objects')
        if self.main_widget.settings_layout.checkbox_invert_toggle.isChecked():
            self.main_widget.settings_layout.checkbox_invert_toggle.setChecked(False)
            self.main_widget.datathread.stop()
        self.main_widget.disconnect_objects()
        return super().closeEvent(a0)
    
    def update_title(self):
        contr = self.main_widget.datathread.contr
        if self.name == "Single":
            window_title = "Motion2MIDI"
        else:
            window_title = "{}: Motion2MIDI Multi".format(self.name)
        
        if contr:
            window_title = "{} - ".format(contr) + window_title      

        self.setWindowTitle(window_title)

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("QFrame { border: 2px solid lightgray; } QLabel { border: none; }")
    main_window = ControllerWindow("Single")
    main_window.main_widget.main_window = main_window  # Weird way to allow main widget to change window title...
    main_window.resize(400, 200)  # Set initial window size small (smaller than widgets normally make it so smallest that is normally resized)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()