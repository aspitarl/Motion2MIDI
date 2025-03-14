from PyQt5 import QtWidgets
import csv
import os
import threading
from pythonosc import dispatcher, osc_server

script_path = os.path.dirname(os.path.realpath(__file__))

class OSCPresetLayout(QtWidgets.QVBoxLayout):
    def __init__(self, parent):
        super(OSCPresetLayout, self).__init__(parent)
        self.parent = parent

        # Horizontal layout for OSC address and port
        self.osc_address_port_layout = QtWidgets.QHBoxLayout()
        self.osc_address_label = QtWidgets.QLabel("OSC Address:")
        self.osc_address_edit = QtWidgets.QLineEdit()
        self.osc_address_edit.setText("/song")
        self.osc_port_label = QtWidgets.QLabel("OSC Port:")
        self.osc_port_edit = QtWidgets.QLineEdit()
        self.osc_port_edit.setText("3000")


        # Toggle button for OSC listener
        self.osc_toggle_button = QtWidgets.QPushButton("Enable OSC Listener")
        self.osc_toggle_button.setCheckable(True)
        self.osc_toggle_button.toggled.connect(self.toggle_osc_listener)
        self.addWidget(self.osc_toggle_button)

        # OSC listener thread
        self.osc_thread = None
        self.osc_server = None
        
        self.osc_address_port_layout.addWidget(self.osc_address_label)
        self.osc_address_port_layout.addWidget(self.osc_address_edit)
        self.osc_address_port_layout.addWidget(self.osc_port_label)
        self.osc_address_port_layout.addWidget(self.osc_port_edit)
        self.osc_address_port_layout.addWidget(self.osc_toggle_button)

        
        self.addLayout(self.osc_address_port_layout)
        
        # Table widget for OSC presets
        self.osc_preset_table = QtWidgets.QTableWidget(0, 5)
        self.osc_preset_table.setHorizontalHeaderLabels(["Preset Name", "Window 1", "Window 2", "Window 3", "Window 4"])
        self.addWidget(self.osc_preset_table)

        # Buttons for loading and saving CSV
        self.button_layout = QtWidgets.QHBoxLayout()
        self.load_button = QtWidgets.QPushButton("Load CSV")
        self.save_button = QtWidgets.QPushButton("Save CSV")
        self.button_layout.addWidget(self.load_button)
        self.button_layout.addWidget(self.save_button)
        self.addLayout(self.button_layout)

        # Connect buttons to functions
        self.load_button.clicked.connect(self.load_csv_dialog)
        self.save_button.clicked.connect(self.save_csv_dialog)

        default_preset_file = os.path.join(script_path, 'settings', "multi_contr_presets.csv")
        self.load_csv(default_preset_file)

        self.osc_toggle_button.setChecked(True)


    def load_csv_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self.parent, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        self.load_csv(file_name)

    def load_csv(self, file_name=None):
        if file_name:
            with open(file_name, newline='') as csvfile:
                reader = csv.reader(csvfile)
                self.osc_preset_table.setRowCount(0)
                for row in reader:
                    row_position = self.osc_preset_table.rowCount()
                    self.osc_preset_table.insertRow(row_position)
                    for column, data in enumerate(row):
                        self.osc_preset_table.setItem(row_position, column, QtWidgets.QTableWidgetItem(data))

    def save_csv_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self.parent, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        self.save_csv(file_name)

    def save_csv(self, file_name=None):
        if file_name:
            with open(file_name, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for row in range(self.osc_preset_table.rowCount()):
                    row_data = []
                    for column in range(self.osc_preset_table.columnCount()):
                        item = self.osc_preset_table.item(row, column)
                        row_data.append(item.text() if item else '')
                    writer.writerow(row_data)

    def toggle_osc_listener(self, enabled):
        if enabled:
            self.osc_toggle_button.setText("Disable OSC Listener")
            self.start_osc_listener()
        else:
            self.osc_toggle_button.setText("Enable OSC Listener")
            self.stop_osc_listener()

    def start_osc_listener(self):
        if not self.osc_thread:
            osc_dispatcher = dispatcher.Dispatcher()
            osc_dispatcher.map(self.osc_address_edit.text(), self.osc_message_handler)
            self.osc_server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", int(self.osc_port_edit.text())), osc_dispatcher)
            self.osc_thread = threading.Thread(target=self.osc_server.serve_forever)
            self.osc_thread.daemon = True
            self.osc_thread.start()

    def stop_osc_listener(self):
        if self.osc_server:
            self.osc_server.shutdown()
            self.osc_server = None
            self.osc_thread = None

    def osc_message_handler(self, address, *args):
        message = args[0]
        for row in range(self.osc_preset_table.rowCount()):
            item = self.osc_preset_table.item(row, 0)
            if item and item.text() == message:
                self.osc_preset_table.selectRow(row)
                break

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QWidget()
    layout = OSCPresetLayout(window)
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())