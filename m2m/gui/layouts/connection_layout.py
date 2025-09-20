from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout

import mido
from PyQt5.QtCore import pyqtSignal

from . import midi_exclude_ports

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
