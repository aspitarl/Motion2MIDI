import os
import time
from PyQt5 import QtWidgets, QtCore
import pprint  
from m2m.core.openvr_utils import Device, NoDevice, RANGE_SET_BUTTON
import mido

class DataThread(QtCore.QThread):
    # https://stackoverflow.com/questions/9957195/updating-gui-elements-in-multithreaded-pyqt

    # Define custom signals
    data_obtained = QtCore.pyqtSignal(object, object)
    debug_signal = QtCore.pyqtSignal(str)
    status_signal = QtCore.pyqtSignal(str)
    exception_signal = QtCore.pyqtSignal(Exception)

    def __init__(self, parent, *args, **kwargs):
        QtCore.QThread.__init__(self, *args, **kwargs)
        self.contr = NoDevice()
        self.midiout = None
        self._table_model = parent.settings_layout.CC_grid_widget._table_model
        self._table_model.dataChanged.connect(self.update_dicts)

        # Running and bypass flags
        self.main_loop_running = False
        self.main_loop_manual_bypass = False  
        self.active_mode_manual_bypass = False 
        self.active_mode_running = False

        self.enable_debug = False
        self.manual_range_set = False
        self.mobile_box_mode = False
        self.midi_channel = 0

        self.input_dict = None
        self.pose_dict = None
        self.sleep_time = 20/1000  # Default sleep time in seconds

        self.update_dicts()
        self.pp = pprint.PrettyPrinter(indent=4)  # Add this line
        self.active_mode_timeout = 10  # seconds, default 1 min
        self.active_mode_tolerance = 0.02  # tolerance for value change

    def run(self):
        """Wrapper for main function with error handling"""
        if isinstance(self.contr, NoDevice):
            self.status_signal.emit("No controller found, Data thread not started")
            return
        self.main_loop_running = True
        self.main_loop_manual_bypass = False
        self.active_mode_manual_bypass = False
        self.active_mode_running = False

        self.status_signal.emit("Data thread started")

        try:
            self._run()
        except Exception as e:
            error_message = f"Error in data thread: {e}"
            new_exception = Exception(error_message)
            new_exception.__cause__ = e
            self.exception_signal.emit(e)
            self.stop(wait_loops_to_stop=False)

    def stop(self, wait_loops_to_stop=True):
        """Stop the data thread"""
        self.main_loop_manual_bypass = True  
        self.active_mode_manual_bypass = True  # Force exit from active mode

        if not wait_loops_to_stop:
            self.main_loop_running = False
            self.active_mode_running = False
            self.status_signal.emit("Data thread stopped without waiting for loops to finish")
            return

        timeout = 5  # seconds
        interval = 0.1  # seconds
        elapsed = 0
        while self.main_loop_running and elapsed < timeout:
            time.sleep(interval)
            elapsed += interval

        if self.main_loop_running:
            self.active_mode_running = False
            self.main_loop_running = False
            raise RuntimeError("Datathread loop didn't stop within the expected time.")

        self.status_signal.emit("Data thread stopped")

    def _run(self):
        """Main loop of the data thread"""
        while self.main_loop_running:
            if self.main_loop_manual_bypass:
                self.main_loop_manual_bypass = False
                self.main_loop_running = False
                self.status_signal.emit("Main loop exited with manual bypass")
                return

            start = time.time()
            self.input_dict = self.contr.get_controller_state_dict()
            self.pose_dict = self.contr.get_pose_dict()

            if self.enable_debug:
                debug_str = (
                    "Input Dictionary:\n" + self.pp.pformat(self.input_dict) + '\n\n' +
                    "Pose Dictionary:\n" + self.pp.pformat(self.pose_dict) + '\n\n' +
                    "Range Dictionary:\n" + self.pp.pformat(self.contr.range_dict)
                )
                self.debug_signal.emit(debug_str)
                time.sleep(0.1)

            if (self.input_dict['button'] == RANGE_SET_BUTTON or self.manual_range_set) and self.pose_dict is not None:
                self.range_set_mode(self.contr)
                self.update_table_model_range_dict()

            if self.pose_dict is not None:   
                if self.input_dict['enable_send']:                    
                    self.active_mode()
            
            sleep_time = self.sleep_time - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _data_changed(self, new_data, last_data):
        """Return True if new_data differs from last_data by more than tolerance for any key."""
        if last_data is None:
            return True
        for k in ['x','y','z']:
            if k not in last_data:
                return True
            try:
                diff_frac = abs(new_data[k] - last_data[k])/last_data[k]
                # print(f"{last_data[k]} {new_data[k]} {diff_frac}")
                if diff_frac > self.active_mode_tolerance:
                    return True
            except Exception:
                if new_data[k] != last_data[k]:
                    return True
        return False

    def active_mode(self):
        """Active mode for sending MIDI data with timeout on unchanged data"""
        self.active_mode_running = True
        self.status_signal.emit("Active mode enabled")

        if self.contr.mobile_box_mode and self.contr.last_pose_dict is not None:
            self.contr.update_range_center()

        last_sent_data = None
        last_change_time = time.time()
        sending_enabled = True

        while self.input_dict['enable_send']:
            start = time.time()

            if self.active_mode_manual_bypass:
                self.active_mode_manual_bypass = False
                self.active_mode_running = False
                self.status_signal.emit("Active mode exited with manual bypass")
                return

            new_pose_dict = self.contr.get_pose_dict()
            if new_pose_dict is None:
                continue
            self.pose_dict = new_pose_dict

            # Use helper function for data change check with tolerance
            if self._data_changed(self.pose_dict, last_sent_data):
                last_sent_data = self.pose_dict.copy()
                last_change_time = time.time()
                if not sending_enabled:
                    self.status_signal.emit("Data changed, resuming MIDI sending")
                sending_enabled = True

            # Check for timeout (only if timeout is enabled)
            if sending_enabled and self.active_mode_timeout is not None:
                elapsed = time.time() - last_change_time
                if elapsed > self.active_mode_timeout:
                    sending_enabled = False
                    self.status_signal.emit("No data change for timeout period, pausing MIDI sending")

            self.input_dict = self.contr.get_controller_state_dict()

            if sending_enabled:
                trigger = self.input_dict['trigger']
                scaled_data_dict = self.contr.get_scaled_data_dict(self.cc_dict, trigger, self.pose_dict)
                for dim in scaled_data_dict:
                    cc = mido.Message('control_change', control=self.cc_dict[dim], value=scaled_data_dict[dim], channel=self.midi_channel)
                    self.midiout.send(cc)

            sleep_time = self.sleep_time - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.contr.last_pose_dict = self.pose_dict
        self.active_mode_running = False
        self.status_signal.emit("Active mode disabled")

    def range_set_mode(self, contr: Device):
        """Range set mode for calibrating controller range"""
        self.status_signal.emit("Entering range set mode")
        start = time.time()
        contr.initialize_range_dict()

        while self.input_dict['button'] == RANGE_SET_BUTTON or self.manual_range_set:
            pose_dict = contr.get_pose_dict()
            self.input_dict = contr.get_controller_state_dict()
            if pose_dict is not None:
                contr.update_range_dict()

            sleep_time = self.sleep_time - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.status_signal.emit("Exiting range set mode")

    def update_dicts(self):
        """Update dictionaries based on table model data"""
        df_table = self._table_model._data
        df_table_enabled = df_table[df_table['send'].astype(bool) == True]
        self.cc_dict = dict(zip(df_table_enabled['dim'], df_table_enabled['CC']))

        if self.contr:
            if 'invert' in df_table_enabled.columns:
                self.contr.invert_dict = dict(zip(df_table_enabled['dim'], df_table_enabled['invert'].astype(bool)))
            else:
                self.contr.invert_dict = {}

            self.contr.range_dict = {   
                row['dim']: {'min': df_table['min_range'][idx].item(), 'max': df_table['max_range'][idx].item()} for idx, row in df_table.iterrows()
            }

    def update_table_model_range_dict(self):
        """Update table model with new range dictionary"""
        df_table = self._table_model._data
        for i, dim in enumerate(self.contr.range_dict):
            # find row number of the dimension
            matching_rows = df_table[df_table['dim'] == dim]
            if not matching_rows.empty:
                idx = matching_rows.index[0]
                df_table.loc[idx, 'min_range'] = self.contr.range_dict[dim]['min']
                df_table.loc[idx, 'max_range'] = self.contr.range_dict[dim]['max']

        self._table_model.set_new_data(df_table)