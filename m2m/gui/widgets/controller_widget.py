from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QWidget, QFrame
)
from PyQt5 import QtCore, QtWidgets
import mido

# Import custom modules
from m2m.core.data_thread import DataThread
from m2m.gui.layouts.connection_layout import ConnectionLayout
from m2m.gui.layouts.settings_layout import SettingsLayout
from m2m.core.openvr_utils import DeviceCollection, NoDevice 


class ControllerWidget(QtWidgets.QWidget):
    # Signal emitted when title should be updated (for parent to handle)
    title_update_requested = QtCore.pyqtSignal()
    
    def __init__(self, name="Controller", parent=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.name = name
        self.device_collection = DeviceCollection()
        layout = QVBoxLayout()
        layout.setSpacing(3)  # Add spacing between sections
        layout.setContentsMargins(5, 5, 5, 5)  # Add margins around the widget
        
        # Set minimum and maximum width for better horizontal layout
        self.setMinimumWidth(450)  # Increased from 300
        self.setMaximumWidth(600)  # Increased from 400
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)

        # Add name label at the top
        name_label = QLabel(f"<b>{self.name}</b>")
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setStyleSheet("QLabel { background-color: lightblue; padding: 2px; margin-bottom: 2px; }")
        layout.addWidget(name_label)

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
        status_label = QLabel("Status:")
        status_label.setFixedWidth(50)  # Fixed width to prevent compression
        status_layout.addWidget(status_label)
        self.status_text_edit = QTextEdit()
        self.status_text_edit.setReadOnly(True)
        self.status_text_edit.setFixedHeight(20)  # Compact height
        self.status_text_edit.setMinimumWidth(200)  # Ensure minimum width
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
        self.title_update_requested.emit()

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

        self.title_update_requested.emit()

    def closeEvent(self, event):
        super().closeEvent(event)

    def cleanup(self):
        """Clean up resources when widget is being removed"""
        if self.datathread.isRunning():
            self.datathread.stop()
        if self.datathread.midiout:
            self.datathread.midiout.close()

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

    def get_controller_name(self):
        """Get the name of the connected controller for display purposes"""
        if self.datathread.contr and hasattr(self.datathread.contr, '__str__'):
            return str(self.datathread.contr)
        return "No Controller"

    def is_connected(self):
        """Check if this widget is currently connected to a controller"""
        return self.connection_layout.checkbox_isconnected.isChecked()