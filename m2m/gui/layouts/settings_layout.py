from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout

from PyQt5 import QtCore

import json
from m2m.gui.widgets.pandas_grid import PandasGridWidget
from m2m.core.custom_mappings import STANDARD_DIMENSIONS, CUSTOM_EQUATIONS
import pandas as pd
import os

script_dir = os.path.dirname(__file__)
settings_root_dir = os.path.join(script_dir, '..', '..', 'settings')
preset_settings_dir = os.path.join(settings_root_dir, 'tracker_presets')
SNAPSHOT_FILE_SUFFIX = '.snapshot.json'


def _is_preset_json_file(file_name):
    return file_name.endswith('.json') and not file_name.endswith(SNAPSHOT_FILE_SUFFIX)


def _preset_name_from_file(file_name):
    return os.path.splitext(file_name)[0]

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

        self._load_button = QPushButton("Apply")
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

        file_path = os.path.join(preset_settings_dir, self._fileselect_combo.currentText() + ".json")
        if os.path.exists(file_path):
            # Read the settings dictionary from the JSON file
            with open(file_path, 'r') as f:
                settings = json.load(f)
            # Convert the DataFrame JSON string to a DataFrame
            # df_initial = pd.read_json(settings['dataframe'], orient='split')
            df_initial = pd.DataFrame(settings['dataframe'])
        else:
            df_initial = pd.DataFrame([])
        # use first file in settings directory as default 
        available_options = STANDARD_DIMENSIONS + list(CUSTOM_EQUATIONS.keys())
        self.CC_grid_widget = PandasGridWidget(df_initial, available_options=available_options)

        self.addWidget(self.CC_grid_widget)

        # Add Row button (rows can be removed inline via X buttons in the grid)
        row_buttons_layout = QHBoxLayout()
        self.add_row_button = QPushButton("Add Row")
        self.add_row_button.clicked.connect(self.CC_grid_widget.add_row)
        row_buttons_layout.addWidget(self.add_row_button)
        self.addLayout(row_buttons_layout)


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
        os.makedirs(preset_settings_dir, exist_ok=True)
        self._fileselect_combo.blockSignals(True)
        selected_text = self._fileselect_combo.currentText()
        self._fileselect_combo.clear()
        preset_names = sorted(
            [_preset_name_from_file(f) for f in os.listdir(preset_settings_dir) if _is_preset_json_file(f)]
        )
        self._fileselect_combo.addItems(preset_names)
        if selected_text:
            index = self._fileselect_combo.findText(selected_text)
            if index >= 0:
                self._fileselect_combo.setCurrentIndex(index)
        self._fileselect_combo.blockSignals(False)

    def get_state_dict(self):
        data = self.CC_grid_widget._table_model._data.copy()
        for column in ['solo', 'send', 'invert']:
            if column in data.columns:
                data[column] = data[column].astype(bool)

        return {
            'dataframe': data.to_dict('records'),
            'half_y_mode': self.checkbox_ymode.isChecked(),
            'roll_x_factor': self.checkbox_roll_x_factor.isChecked(),
            'roll_y_factor': self.checkbox_roll_y_factor.isChecked(),
            'haptic': self.checkbox_enable_haptic.isChecked(),
            'invert_toggle': self.checkbox_invert_toggle.isChecked(),
            'mobile_box_mode': self.checkbox_mobile_box_mode.isChecked(),
            'message_sleep_time': self.sleep_time_spinbox.value(),
            'timeout_tolerance': self.tolerance_slider.value() / 100.0,
            'timeout_time': self.timeout_spinbox.value(),
        }

    def apply_state_dict(self, settings):
        if not settings:
            return

        dataframe = settings.get('dataframe')
        if dataframe is not None:
            self._data = pd.DataFrame(dataframe)
            if not self._data.empty:
                self.CC_grid_widget.set_data(self._data)

        self.checkbox_ymode.setChecked(settings.get('half_y_mode', self.checkbox_ymode.isChecked()))
        self.checkbox_roll_x_factor.setChecked(settings.get('roll_x_factor', self.checkbox_roll_x_factor.isChecked()))
        self.checkbox_roll_y_factor.setChecked(settings.get('roll_y_factor', self.checkbox_roll_y_factor.isChecked()))
        self.checkbox_enable_haptic.setChecked(settings.get('haptic', self.checkbox_enable_haptic.isChecked()))
        self.checkbox_invert_toggle.setChecked(settings.get('invert_toggle', self.checkbox_invert_toggle.isChecked()))
        self.checkbox_mobile_box_mode.setChecked(settings.get('mobile_box_mode', self.checkbox_mobile_box_mode.isChecked()))
        self.sleep_time_spinbox.setValue(settings.get('message_sleep_time', self.sleep_time_spinbox.value()))
        self.tolerance_slider.setValue(int(settings.get('timeout_tolerance', self.tolerance_slider.value() / 100.0) * 100))
        self.timeout_spinbox.setValue(settings.get('timeout_time', self.timeout_spinbox.value()))

    def apply_preset_name(self, preset_name):
        if not preset_name:
            return False

        index = self._fileselect_combo.findText(preset_name)
        if index < 0:
            return False

        self._fileselect_combo.setCurrentIndex(index)
        self.load_data()
        return True

    def set_selected_preset_name(self, preset_name):
        if not preset_name:
            return False

        index = self._fileselect_combo.findText(preset_name)
        if index < 0:
            return False

        self._fileselect_combo.blockSignals(True)
        self._fileselect_combo.setCurrentIndex(index)
        self._fileselect_combo.blockSignals(False)
        return True

    def save_data(self):

        os.makedirs(preset_settings_dir, exist_ok=True)
        default_file_path = os.path.join(preset_settings_dir, self._fileselect_combo.currentText() + ".json")
        # open a file dialog with this as the default file name
        file_path, _ = QFileDialog.getSaveFileName(self.parent, 'Save Settings', default_file_path, 'JSON Files (*.json)')


        if file_path:
            settings = self.get_state_dict()

            # Write the settings dictionary to the JSON file
            with open(file_path, 'w') as f:
                json.dump(settings, f, indent=4)

            # set the combo box to the new file name
            self.update_file_list()
            self._fileselect_combo.setCurrentText(_preset_name_from_file(os.path.basename(file_path)))

    def load_data(self):
        selected_preset = self._fileselect_combo.currentText()
        if not selected_preset:
            return

        file_path = os.path.join(preset_settings_dir, selected_preset + ".json")
        if os.path.exists(file_path):

            # Read the settings dictionary from the JSON file
            with open(file_path, 'r') as f:
                settings = json.load(f)
            self.apply_state_dict(settings)

