from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QRegExpValidator, QIntValidator
from PyQt5.QtCore import QRegExp

midi_exclude_ports = ['Microsoft GS Wavetable Synth', 'Focusrite']

import mido
from PyQt5.QtCore import pyqtSignal

class ConnectionLayout(QtWidgets.QVBoxLayout):

    combobox_selections_changed = pyqtSignal(name='combobox_selections_changed')

    def __init__(self, device_collection, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.dc = device_collection

        section_layout = QHBoxLayout()

        #OpenVR layout
        openvr_hlayout = QVBoxLayout()
        self.pushbutton_discover = QPushButton('Refresh OpenVR Objects')
        self.pushbutton_discover.clicked.connect(self.discover_openvr_objects)

        self.combobox_ovr_objects = QComboBox()
        self.combobox_ovr_objects.currentIndexChanged.connect(self.select_midi_port_based_on_object)
        openvr_hlayout.addWidget(self.pushbutton_discover)
        openvr_hlayout.addWidget(self.combobox_ovr_objects)

        section_layout.addLayout(openvr_hlayout)

        # MIDI
        self.midi_layout = QVBoxLayout()

        self.pushbutton_refresh = QPushButton('Refresh MIDI Ports')
        self.pushbutton_refresh.clicked.connect(self.refresh_midi_ports)
        self.midi_layout.addWidget(self.pushbutton_refresh)

        midi_port_layout = QHBoxLayout()
        self.combobox_midi_ports = QComboBox()
        self.refresh_midi_ports()
        midi_port_layout.addWidget(QLabel("Port:"))
        midi_port_layout.addWidget(self.combobox_midi_ports)
        self.midi_layout.addLayout(midi_port_layout)

        # Add MIDI channel selection
        midi_channel_layout = QHBoxLayout()
        self.combobox_midi_channels = QComboBox()
        self.combobox_midi_channels.addItems([str(i) for i in range(1, 17)])
        midi_channel_layout.addWidget(QLabel("Channel:"))
        midi_channel_layout.addWidget(self.combobox_midi_channels)
        self.midi_layout.addLayout(midi_channel_layout)

        self.combobox_midi_ports.currentIndexChanged.connect(self.combobox_selections_changed.emit)
        self.combobox_ovr_objects.currentIndexChanged.connect(self.combobox_selections_changed.emit)
        self.combobox_midi_channels.currentIndexChanged.connect(self.combobox_selections_changed.emit)

        section_layout.addLayout(self.midi_layout)

        self.addLayout(section_layout)

        connect_hlayout = QHBoxLayout()

        # Connect midi and OpenVR
        self.pushbutton_connect = QPushButton('Connect')
        connect_hlayout.addWidget(self.pushbutton_connect)

        # Disconnect midi and OpenVR
        self.pushbutton_disconnect = QPushButton('Disconnect')
        connect_hlayout.addWidget(self.pushbutton_disconnect)

        self.checkbox_isconnected = QCheckBox('Connected?')
        self.checkbox_isconnected.setEnabled(False)
        # self.checkbox_isconnected.set
        connect_hlayout.addWidget(self.checkbox_isconnected)

        self.addLayout(connect_hlayout)

    def refresh_midi_ports(self):
        available_ports = mido.get_output_names()
        available_ports = [p for p in available_ports if not any([e in p for e in midi_exclude_ports])]
        self.combobox_midi_ports.clear()
        self.combobox_midi_ports.addItems(available_ports)

    def discover_openvr_objects(self):

        self.dc.refresh_present_devices()

        self.combobox_ovr_objects.clear()
        display_text = [str(c) for c in self.dc.present_devices]
        self.combobox_ovr_objects.addItems(display_text)

    def select_midi_port_based_on_object(self):
        # convienience function to select the first midi port that matches the selected object (left or right)
        selected_ovr_object = self.combobox_ovr_objects.currentText().lower()
        available_ports = mido.get_output_names()
        all_ports = [p for p in available_ports if not any([e in p for e in midi_exclude_ports])]

        #TODO: simplifty and  coordinate with default naming from serial number in Device class
        if 'left controller' in selected_ovr_object:
            filtered_ports = [p for p in all_ports if 'left controller' in p.lower()]
        elif 'right controller' in selected_ovr_object:
            filtered_ports = [p for p in all_ports if 'right controller' in p.lower()]
        elif 'left vive' in selected_ovr_object:
            filtered_ports = [p for p in all_ports if 'left vive' in p.lower()]
        elif 'right vive' in selected_ovr_object:
            filtered_ports = [p for p in all_ports if 'right vive' in p.lower()]
        else:
            filtered_ports = None

        # select the first port that matches the criteria
        print(filtered_ports)
        if filtered_ports:
            self.combobox_midi_ports.setCurrentText(filtered_ports[0])


import json
from pandas_grid import PandasGridWidget
import pandas as pd
import os

script_dir = os.path.dirname(__file__)
settings_dir = os.path.join(script_dir, 'settings')

class SettingsLayout(QVBoxLayout):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.parent = parent

        self.fileio_layout = QHBoxLayout()


        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.clicked.connect(self.update_file_list) 
        self.fileio_layout.addWidget(self._refresh_button)

        self._fileselect_combo = QComboBox()
        self.fileio_layout.addWidget(self._fileselect_combo)

        self._load_button = QPushButton("Load")
        self._load_button.clicked.connect(self.load_data)
        self.fileio_layout.addWidget(self._load_button)

        self._save_button = QPushButton("Save")
        self._save_button.clicked.connect(self.save_data)
        self.fileio_layout.addWidget(self._save_button)

        # add file list to combo box
        self.update_file_list()
        # Add all files in the settings directory to the combo box
        self._fileselect_combo.currentIndexChanged.connect(self.load_data)

        self.addLayout(self.fileio_layout)

        file_path = os.path.join(settings_dir, self._fileselect_combo.currentText() + ".json")
        # Read the settings dictionary from the JSON file
        with open(file_path, 'r') as f:
            settings = json.load(f)

        # Convert the DataFrame JSON string to a DataFrame
        # df_initial = pd.read_json(settings['dataframe'], orient='split')
        df_initial = pd.DataFrame(settings['dataframe'])
        # use first file in settings directory as default 
        self.CC_grid_widget = PandasGridWidget(df_initial)

        self.addWidget(self.CC_grid_widget)


        #TODO: these also are janky data communications between mainwidget and thread, like signal select layout. 
        self.checkbox_ymode = QCheckBox('Enable Half Y mode')
        self.checkbox_ymode.setChecked(False)

        # make a two checkboxes that set the yaw x and y factors to 1 or -1 depending on the state of the checkbox, setting the roll_x_factor and roll_y_factor variables in the data thread

        self.checkbox_roll_x_factor = QCheckBox('Roll X Flip')
        self.checkbox_roll_x_factor.setChecked(False)

        self.checkbox_roll_y_factor = QCheckBox('Roll Y Flip')
        self.checkbox_roll_y_factor.setChecked(False)

        # two more checkboxes for enable_haptic and invert_toggle in the data thread

        self.checkbox_enable_haptic = QCheckBox('Enable Haptic')
        self.checkbox_enable_haptic.setChecked(False)

        self.checkbox_invert_toggle = QCheckBox('Invert Toggle')
        self.checkbox_invert_toggle.setChecked(False)

        self.checkbox_mobile_box_mode = QCheckBox('Mobile Box Mode')
        self.checkbox_mobile_box_mode.setChecked(False)

        # Extra settings
        # make a grid layout for all extra settings checkboxes and add it to the main layout
        extra_settings_layout = QGridLayout()
        extra_settings_layout.addWidget(self.checkbox_ymode, 0, 0)
        extra_settings_layout.addWidget(self.checkbox_mobile_box_mode, 0, 1)
        extra_settings_layout.addWidget(self.checkbox_roll_x_factor, 1, 0)
        extra_settings_layout.addWidget(self.checkbox_roll_y_factor, 1, 1)
        extra_settings_layout.addWidget(self.checkbox_enable_haptic, 2, 0)
        extra_settings_layout.addWidget(self.checkbox_invert_toggle, 2, 1)

        self.addLayout(extra_settings_layout)

    def update_file_list(self):
        self._fileselect_combo.blockSignals(True)
        self._fileselect_combo.clear()
        self._fileselect_combo.addItems([f.split('.')[0] for f in os.listdir(settings_dir) if f.endswith('.json')])
        self._fileselect_combo.blockSignals(False)

    def save_data(self):

        default_file_path = os.path.join(settings_dir, self._fileselect_combo.currentText() + ".json")
        # open a file dialog with this as the default file name
        file_path, _ = QFileDialog.getSaveFileName(self.parent, 'Save Settings', default_file_path, 'JSON Files (*.json)')


        if file_path:
            self._data = self.CC_grid_widget._table_model._data

            # Make sure the solor and send data columns are bools
            self._data['solo'] = self._data['solo'].astype(bool)
            self._data['send'] = self._data['send'].astype(bool)

            # Convert the DataFrame to a JSON string
            df_dict = self._data.to_dict('records')

            # Create a settings dictionary
            settings = {
                'dataframe': df_dict,
                'half_y_mode': self.checkbox_ymode.isChecked(),
                'roll_x_factor': self.checkbox_roll_x_factor.isChecked(),
                'roll_y_factor': self.checkbox_roll_y_factor.isChecked(),
                'haptic': self.checkbox_enable_haptic.isChecked(),
                'invert_toggle': self.checkbox_invert_toggle.isChecked(),
                'mobile_box_mode': self.checkbox_mobile_box_mode.isChecked(),

            }

            # Write the settings dictionary to the JSON file
            with open(file_path, 'w') as f:
                json.dump(settings, f, indent=4)

            # set the combo box to the new file name
            self.update_file_list()
            self._fileselect_combo.setCurrentText(file_path.split('/')[-1].split('.')[0])

    def load_data(self):
        file_path = os.path.join(settings_dir, self._fileselect_combo.currentText() + ".json")  
        if os.path.exists(file_path):

            # Read the settings dictionary from the JSON file
            with open(file_path, 'r') as f:
                settings = json.load(f)

            # Convert the DataFrame JSON string to a DataFrame
            self._data = pd.DataFrame(settings['dataframe'])
            # self._data = pd.read_json(settings['dataframe'], orient='split')

            # Load the DataFrame into the grid widget
            self.CC_grid_widget.set_data(self._data)

            # # Load the other settings
            self.checkbox_ymode.setChecked(settings['half_y_mode'])
            self.checkbox_roll_x_factor.setChecked(settings['roll_x_factor'])
            self.checkbox_roll_y_factor.setChecked(settings['roll_y_factor'])
            self.checkbox_enable_haptic.setChecked(settings['haptic'])
            self.checkbox_invert_toggle.setChecked(settings['invert_toggle'])
            self.checkbox_mobile_box_mode.setChecked(settings['mobile_box_mode'])


