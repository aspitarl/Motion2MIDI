from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
import re

import mido
from PyQt5.QtCore import pyqtSignal

from . import midi_exclude_ports

class ConnectionLayout(QtWidgets.QVBoxLayout):

    combobox_selections_changed = pyqtSignal(name='combobox_selections_changed')

    def __init__(self, device_collection, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        # Set compact spacing for this layout
        self.setSpacing(3)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

        self.dc = device_collection
        self._openvr_device_metadata = []

        section_layout = QHBoxLayout()
        section_layout.setSpacing(3)

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

    def get_state_dict(self):
        selected_index = self.combobox_ovr_objects.currentIndex()
        selected_device_model = None
        selected_device_serial = None
        if 0 <= selected_index < len(self.dc.present_devices):
            selected_device = self.dc.present_devices[selected_index]
            selected_device_model = selected_device.get_model()
            selected_device_serial = selected_device.get_serial()

        return {
            'openvr_device': self.combobox_ovr_objects.currentText(),
            'openvr_device_model': selected_device_model,
            'openvr_device_serial': selected_device_serial,
            'midi_port': self.combobox_midi_ports.currentText(),
            'midi_channel': self.combobox_midi_channels.currentText(),
            'midi_channel_index': self.combobox_midi_channels.currentIndex(),
            'connected': self.checkbox_isconnected.isChecked(),
        }

    def apply_state_dict(self, state):
        state = state or {}
        self.discover_openvr_objects()
        self.refresh_midi_ports()

        requested_device = state.get('openvr_device')
        requested_device_model = state.get('openvr_device_model')
        requested_device_serial = state.get('openvr_device_serial')
        requested_midi_port = state.get('midi_port')

        result = {
            'device_matched': self._set_openvr_device(requested_device, requested_device_model, requested_device_serial),
            'midi_port_matched': self._set_combobox_text(self.combobox_midi_ports, requested_midi_port) if requested_midi_port else True,
            'channel_matched': True,
            'requested_device': requested_device,
            'requested_device_model': requested_device_model,
            'requested_device_serial': requested_device_serial,
            'requested_midi_port': requested_midi_port,
        }

        channel_index = state.get('midi_channel_index')
        channel_text = state.get('midi_channel')
        if channel_index is not None and 0 <= channel_index < self.combobox_midi_channels.count():
            self.combobox_midi_channels.setCurrentIndex(channel_index)
        elif channel_text:
            result['channel_matched'] = self._set_combobox_text(self.combobox_midi_channels, channel_text)

        return result

    def _set_combobox_text(self, combobox, text):
        if not text:
            return False
        index = combobox.findText(text)
        if index < 0:
            return False
        combobox.setCurrentIndex(index)
        return True

    def _normalize_device_text(self, text):
        if not text:
            return ''
        normalized = str(text).strip().lower()
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def _set_openvr_device(self, requested_device, requested_model=None, requested_serial=None):
        if self.combobox_ovr_objects.count() == 0:
            return False

        if requested_serial:
            for index, metadata in enumerate(self._openvr_device_metadata):
                if metadata.get('serial') == requested_serial:
                    self.combobox_ovr_objects.setCurrentIndex(index)
                    return True

        if requested_device and self._set_combobox_text(self.combobox_ovr_objects, requested_device):
            return True

        normalized_requested = self._normalize_device_text(requested_device)
        if normalized_requested:
            for index, metadata in enumerate(self._openvr_device_metadata):
                normalized_display = self._normalize_device_text(metadata.get('display'))
                if normalized_requested in normalized_display or normalized_display in normalized_requested:
                    self.combobox_ovr_objects.setCurrentIndex(index)
                    return True

        normalized_model = self._normalize_device_text(requested_model)
        if normalized_model:
            for index, metadata in enumerate(self._openvr_device_metadata):
                normalized_display = self._normalize_device_text(metadata.get('display'))
                normalized_device_model = self._normalize_device_text(metadata.get('model'))
                if normalized_model in normalized_display or normalized_model == normalized_device_model:
                    self.combobox_ovr_objects.setCurrentIndex(index)
                    return True

        return False

    def discover_openvr_objects(self):

        self.dc.refresh_present_devices()

        self.combobox_ovr_objects.clear()
        self._openvr_device_metadata = []
        display_text = []
        for device in self.dc.present_devices:
            display = str(device)
            display_text.append(display)
            self._openvr_device_metadata.append(
                {
                    'display': display,
                    'model': device.get_model(),
                    'serial': device.get_serial(),
                }
            )
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
