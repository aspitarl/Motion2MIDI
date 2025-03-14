from PyQt5 import QtWidgets

class OSCPresetLayout(QtWidgets.QVBoxLayout):
    def __init__(self, parent):
        super(OSCPresetLayout, self).__init__(parent)
        self.parent = parent

        # Horizontal layout for OSC address and port
        self.osc_address_port_layout = QtWidgets.QHBoxLayout()
        self.osc_address_label = QtWidgets.QLabel("OSC Address:")
        self.osc_address_edit = QtWidgets.QLineEdit()
        self.osc_port_label = QtWidgets.QLabel("OSC Port:")
        self.osc_port_edit = QtWidgets.QLineEdit()
        
        self.osc_address_port_layout.addWidget(self.osc_address_label)
        self.osc_address_port_layout.addWidget(self.osc_address_edit)
        self.osc_address_port_layout.addWidget(self.osc_port_label)
        self.osc_address_port_layout.addWidget(self.osc_port_edit)
        
        self.addLayout(self.osc_address_port_layout)
        
        # Table widget for OSC presets
        self.osc_preset_table = QtWidgets.QTableWidget(0, 2)
        self.osc_preset_table.setHorizontalHeaderLabels(["Preset Name", "OSC Path"])
        self.addWidget(self.osc_preset_table)




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QWidget()
    layout = OSCPresetLayout(window)
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())