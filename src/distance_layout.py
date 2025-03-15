from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFrame
import mido
import numpy as np

# Configure logging
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')




class PollingThread(QtCore.QThread):
    def __init__(self, parent):
        super().__init__()
        self.running = False
        self.parent = parent
        self.midiout = None  # Initialize midiout as None
        self.main_window1 = None
        self.main_window2 = None

    def run(self):
        logging.debug("PollingThread started")
        self.running = True
        pose_dict1 = None
        pose_dict2 = None

        self.connect_midi_port()
        
        while self.running:
            if not self.main_window1 or not self.main_window2:
                logging.debug("Waiting for main windows to be set")
                self.msleep(100)
                continue
        
            input_dict1 = self.main_window1.main_widget.datathread.input_dict
            input_dict2 = self.main_window2.main_widget.datathread.input_dict

            if input_dict1 is None or input_dict2 is None:
                logging.debug("Input dictionaries are None, restarting loop")
                self.msleep(100)
                continue

            if input_dict1['enable_send'] or input_dict2['enable_send'] or not (self.parent.require_device1_checkbox.isChecked() and self.parent.require_device2_checkbox.isChecked()):
                temp_pose_dict1 = self.main_window1.main_widget.datathread.pose_dict
                temp_pose_dict2 = self.main_window2.main_widget.datathread.pose_dict

                if input_dict1['enable_send'] or not self.parent.require_device1_checkbox.isChecked(): 
                    pose_dict1 = temp_pose_dict1
                if input_dict2['enable_send'] or not self.parent.require_device2_checkbox.isChecked():
                    pose_dict2 = temp_pose_dict2

                if pose_dict1 is None or pose_dict2 is None:
                    logging.debug("Pose dictionaries are None, restarting loop")
                    self.msleep(100)
                    continue

                pose_diff = {dim: pose_dict1[dim] - pose_dict2[dim] for dim in pose_dict1 if dim in ['x', 'y', 'z']}
                distance = np.linalg.norm(list(pose_diff.values()))
                # logging.debug(f"Calculated distance: {distance}")
                self.parent.distance_label.setText(f"Distance: {distance:.2f}")

                dist_range = self.parent.range_spin_box.value()
                cc_value = self.parent.cc_number.value()
                invert = self.parent.invert_checkbox.isChecked()

                dist_norm = distance / dist_range
                cc_out = int(dist_norm * 127)
                cc_out = max(0, min(127, cc_out))

                if invert:
                    cc_out = 127 - cc_out

                cc = mido.Message('control_change', control=cc_value, value=cc_out, channel=3)
                if self.midiout:
                    # logging.debug(f"Sending MIDI message: {cc}")
                    self.midiout.send(cc)

                delay = self.parent.delay_spin_box.value()
                self.msleep(delay)

    def stop(self):
        logging.debug("Stopping PollingThread")
        self.running = False
        if self.midiout:
            self.midiout.close()

    def connect_midi_port(self):
        port_name = self.parent.midi_port_combobox.currentText()
        logging.debug(f"Setting MIDI port: {port_name}")
        if self.midiout:
            self.midiout.close()
        self.midiout = mido.open_output(port_name)

    def set_windows(self, main_window1, main_window2):
        logging.debug(f"Setting main windows: {main_window1}, {main_window2}")
        self.main_window1 = main_window1
        self.main_window2 = main_window2


class DistanceLayout(QtWidgets.QVBoxLayout):
    def __init__(self, parent):
        super(DistanceLayout, self).__init__(parent)

        self.parent = parent


        connection_vlayout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()
        # Create dropdown menus for selecting the windows
        self.window1_label = QtWidgets.QLabel("Window A:")
        self.window1_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        hlayout.addWidget(self.window1_label)

        self.window1_combobox = QtWidgets.QComboBox()
        self.window1_combobox.currentTextChanged.connect(self.change_windows)
        hlayout.addWidget(self.window1_combobox)

        self.require_device1_checkbox = QtWidgets.QCheckBox("Require Window A Toggle")
        self.require_device1_checkbox.setChecked(True)
        hlayout.addWidget(self.require_device1_checkbox)

        connection_vlayout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        self.window2_label = QtWidgets.QLabel("Window B:")
        self.window2_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        hlayout.addWidget(self.window2_label)

        self.window2_combobox = QtWidgets.QComboBox()
        self.window2_combobox.currentTextChanged.connect(self.change_windows)
        hlayout.addWidget(self.window2_combobox)

        self.require_device2_checkbox = QtWidgets.QCheckBox("Require Window B Toggle")
        self.require_device2_checkbox.setChecked(True)
        hlayout.addWidget(self.require_device2_checkbox)

        connection_vlayout.addLayout(hlayout)




        hlayout = QtWidgets.QHBoxLayout()
        # Create a dropdown menu for selecting the MIDI port
        self.midi_port_label = QtWidgets.QLabel("MIDI Port:")
        self.midi_port_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        hlayout.addWidget(self.midi_port_label)

        self.midi_port_combobox = QtWidgets.QComboBox()
        midi_port_names = mido.get_output_names()
        self.midi_port_combobox.addItems(mido.get_output_names())
        # if any port contain 'distance' in the name, select it
        for i, port_name in enumerate(midi_port_names):
            if 'distance' in port_name.lower():
                self.midi_port_combobox.setCurrentIndex(i)
            
        hlayout.addWidget(self.midi_port_combobox)


        self.cc_number_label = QtWidgets.QLabel("CC Number:")
        self.cc_number_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        hlayout.addWidget(self.cc_number_label)
        
        self.cc_number = QtWidgets.QSpinBox()
        self.cc_number.setRange(0, 127)
        self.cc_number.setValue(30)
        hlayout.addWidget(self.cc_number)

        connection_vlayout.addLayout(hlayout)



        connection_frame = QFrame()
        connection_frame.setLayout(connection_vlayout)
        self.addWidget(connection_frame)

        settings_layout = QtWidgets.QVBoxLayout()   

        hbox = QtWidgets.QHBoxLayout()  
        # Create a toggle button to start and stop the polling thread
        self.toggle_button = QtWidgets.QPushButton("Start Polling")
        self.toggle_button.setCheckable(True)
        self.toggle_button.toggled.connect(self.toggle_thread)
        hbox.addWidget(self.toggle_button)


        self.delay_label = QtWidgets.QLabel("Delay (ms):")
        self.delay_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        hbox.addWidget(self.delay_label)
        
        self.delay_spin_box = QtWidgets.QSpinBox()
        self.delay_spin_box.setRange(1, 1000)
        self.delay_spin_box.setValue(5)
        hbox.addWidget(self.delay_spin_box)

        settings_layout.addLayout(hbox)

        hbox = QtWidgets.QHBoxLayout()

        # Create a label to show the distance
        self.distance_label = QtWidgets.QLabel("Distance: ")
        hbox.addWidget(self.distance_label)

        # Create a slider to set the range from 0.0 to 5.0 with a display of 0.1
        self.range_label = QtWidgets.QLabel("Range:")
        self.range_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        hbox.addWidget(self.range_label)
        
        self.range_spin_box = QtWidgets.QDoubleSpinBox()
        self.range_spin_box.setRange(0.1, 5.0)
        self.range_spin_box.setSingleStep(0.1)
        self.range_spin_box.setValue(1.5)
        hbox.addWidget(self.range_spin_box)

        self.invert_checkbox = QtWidgets.QCheckBox("Invert")
        self.invert_checkbox.setChecked(True)
        hbox.addWidget(self.invert_checkbox)

        settings_layout.addLayout(hbox)

        hlayout = QtWidgets.QHBoxLayout()
        self.invert_toggles_checkbox = QtWidgets.QCheckBox("Switch Window Invert Toggles")
        self.invert_toggles_checkbox.stateChanged.connect(self.toggle_invert_toggles)
        hlayout.addWidget(self.invert_toggles_checkbox)
        settings_layout.addLayout(hlayout)

        settings_frame = QFrame()
        settings_frame.setLayout(settings_layout)
        self.addWidget(settings_frame)

        # Create the polling thread
        self.polling_thread = PollingThread(parent=self)
        self.midi_port_combobox.currentTextChanged.connect(self.polling_thread.connect_midi_port)

    def toggle_thread(self, checked):
        if checked:
            self.toggle_button.setText("Stop Polling")
            self.polling_thread.start()
        else:
            self.toggle_button.setText("Start Polling")
            self.polling_thread.stop()

    def change_windows(self):
        window1_name = self.window1_combobox.currentText()
        window2_name = self.window2_combobox.currentText()
        window1 = self.parent.window_manager_layout.windows.get(window1_name)
        window2 = self.parent.window_manager_layout.windows.get(window2_name)
        self.polling_thread.set_windows(window1, window2)

    def update_window_comboboxes(self):
        self.window1_combobox.clear()
        self.window2_combobox.clear()
        for window_name in self.parent.window_manager_layout.windows.keys():
            self.window1_combobox.addItem(window_name)
            self.window2_combobox.addItem(window_name)

    def toggle_invert_toggles(self, state):
        window_manager_layout = self.parent.window_manager_layout
        for window in window_manager_layout.windows.values():
            window.main_widget.settings_layout.checkbox_invert_toggle.setChecked(state == QtCore.Qt.Checked)
