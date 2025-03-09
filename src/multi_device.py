import os
import sys
import numpy as np
import logging  # Import logging module
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFrame
from main import MainWindow as SingleMainWindow
import mido

from midi_listener import MidiListenerWindow

script_path = os.path.dirname(os.path.realpath(__file__))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.midi_port_combobox.addItems(mido.get_output_names())
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

    def toggle_invert_toggles(self, state):
        for window in self.parent.windows.values():
            window.main_widget.settings_layout.checkbox_invert_toggle.setChecked(state == QtCore.Qt.Checked)

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

    def spawn_window(self):
        window_name = f"Window {len(self.windows) + 1}"
        window = SingleMainWindow(name=window_name)
        self.windows[window_name] = window

        self.parent.distance_layout.window1_combobox.addItem(window_name)
        self.parent.distance_layout.window2_combobox.addItem(window_name)

        window.show()
        
        # Position the new window to the side of the main window
        main_window_geometry = self.geometry()
        window.move(main_window_geometry.right() + 10, main_window_geometry.top())
        
        # Check if there are two windows and set the window B combo box to the second window
        if len(self.windows) == 2:
            window_names = list(self.windows.keys())
            self.parent.distance_layout.window2_combobox.setCurrentText(window_names[1])



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