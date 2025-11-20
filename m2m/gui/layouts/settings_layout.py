from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout

from PyQt5 import QtCore

import json
from m2m.gui.widgets.pandas_grid import PandasGridWidget
import pandas as pd
import os

script_dir = os.path.dirname(__file__)
settings_dir = os.path.join(script_dir, '..', '..', 'settings')

class SettingsLayout(QVBoxLayout):

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set compact spacing for this layout
        self.setSpacing(3)
        self.setContentsMargins(0, 0, 0, 0)

        self.parent = parent

        self.fileio_layout = QHBoxLayout()
        self.fileio_layout.setSpacing(3)


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
        extra_settings_layout.setSpacing(2)
        extra_settings_layout.setContentsMargins(0, 0, 0, 0)
        extra_settings_layout.addWidget(self.checkbox_ymode, 0, 0)
        extra_settings_layout.addWidget(self.checkbox_mobile_box_mode, 0, 1)
        extra_settings_layout.addWidget(self.checkbox_roll_x_factor, 1, 0)
        extra_settings_layout.addWidget(self.checkbox_roll_y_factor, 1, 1)
        extra_settings_layout.addWidget(self.checkbox_enable_haptic, 2, 0)
        extra_settings_layout.addWidget(self.checkbox_invert_toggle, 2, 1)

        self.addLayout(extra_settings_layout)

        # Sleep time widget
        sleep_time_layout = QHBoxLayout()
        sleep_time_layout.setSpacing(3)
        sleep_time_label = QLabel("Message Sleep Time (ms):")
        self.sleep_time_spinbox = QSpinBox()
        self.sleep_time_spinbox.setRange(1, 1000)
        self.sleep_time_spinbox.setValue(20)
        sleep_time_layout.addWidget(sleep_time_label)
        sleep_time_layout.addWidget(self.sleep_time_spinbox)
        self.addLayout(sleep_time_layout)

        # Tolerance slider and timeout spinbox
        tolerance_layout = QHBoxLayout()
        tolerance_layout.setSpacing(3)
        tolerance_label = QLabel("Timeout Tolerance:")
        self.tolerance_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.tolerance_slider.setMinimum(0)
        self.tolerance_slider.setMaximum(10)
        self.tolerance_slider.setValue(2)
        self.tolerance_slider.setSingleStep(1)
        self.tolerance_slider.setTickInterval(1)
        self.tolerance_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.tolerance_value_label = QLabel("0.02")
        tolerance_layout.addWidget(tolerance_label)
        tolerance_layout.addWidget(self.tolerance_slider)
        tolerance_layout.addWidget(self.tolerance_value_label)
        timeout_label = QLabel("Timeout (s):")
        tolerance_layout.addWidget(timeout_label)
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setMinimum(1)
        self.timeout_spinbox.setMaximum(120)
        self.timeout_spinbox.setValue(10)
        self.timeout_spinbox.setSuffix(" s")
        tolerance_layout.addWidget(self.timeout_spinbox)
        self.addLayout(tolerance_layout)

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
                'message_sleep_time': self.sleep_time_spinbox.value(),
                'timeout_tolerance': self.tolerance_slider.value() / 100.0,
                'timeout_time': self.timeout_spinbox.value()
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
            # Load sleep/tolerance/timeout if present
            self.sleep_time_spinbox.setValue(settings['message_sleep_time'])
            self.tolerance_slider.setValue(int(settings['timeout_tolerance'] * 100))
            self.timeout_spinbox.setValue(settings['timeout_time'])

