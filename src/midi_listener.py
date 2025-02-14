import sys
from PyQt5 import QtWidgets, QtCore
import mido

class MidiListenerThread(QtCore.QThread):
    cc_received = QtCore.pyqtSignal(int, int)  # Signal to emit CC number and value

    def __init__(self, cc_numbers, parent=None):
        super().__init__(parent)
        self.running = False
        self.midiin = None
        self.cc_numbers = cc_numbers

    def run(self):
        self.running = True
        while self.running:
            if self.midiin:
                for msg in self.midiin.iter_pending():
                    if msg.type == 'control_change' and msg.control in self.cc_numbers:
                        self.cc_received.emit(msg.control, msg.value)
            self.msleep(10)

    def stop(self):
        self.running = False
        if self.midiin:
            self.midiin.close()

    def set_midi_port(self, port_name):
        if self.midiin:
            self.midiin.close()
        self.midiin = mido.open_input(port_name)

    def update_cc_numbers(self, cc_numbers):
        self.cc_numbers = cc_numbers

class MidiListenerWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MidiListenerWindow, self).__init__(parent)
        self.setWindowTitle("MIDI Listener")
        self.resize(450, 300)  # Set default window size

        self.default_cc_numbers = list(range(22, 31))

        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        self.midi_port_combobox = QtWidgets.QComboBox()
        self.midi_port_combobox.addItems(mido.get_input_names())
        self.midi_port_combobox.currentTextChanged.connect(self.change_midi_port)
        layout.addWidget(self.midi_port_combobox)

        self.cc_spin_boxes = {}
        self.value_spin_boxes = {}
        for row, cc in enumerate(self.default_cc_numbers):
            cc_spin_box = QtWidgets.QSpinBox()
            cc_spin_box.setRange(0, 127)
            cc_spin_box.setValue(cc)
            cc_spin_box.valueChanged.connect(self.update_thread_cc_numbers)

            value_spin_box = QtWidgets.QSpinBox()
            value_spin_box.setRange(0, 127)
            value_spin_box.setReadOnly(True)
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 127)
            slider.valueChanged.connect(value_spin_box.setValue)
            value_spin_box.valueChanged.connect(slider.setValue)

            hlayout = QtWidgets.QHBoxLayout()
            hlayout.addWidget(QtWidgets.QLabel(f"CC: "))
            hlayout.addWidget(cc_spin_box)
            hlayout.addWidget(QtWidgets.QLabel(f"Val: "))
            hlayout.addWidget(value_spin_box)
            hlayout.addWidget(slider)
            layout.addLayout(hlayout)

            self.cc_spin_boxes[row] = cc_spin_box
            self.value_spin_boxes[row] = value_spin_box

        self.listener_thread = MidiListenerThread(cc_numbers=self.default_cc_numbers, parent=self)
        self.listener_thread.cc_received.connect(self.update_spin_box)

        self._table_model = parent.main_widget.settings_layout.CC_grid_widget._table_model
        self._table_model.dataChanged.connect(self.update_displayed_cc_numbers)


        # self.change_midi_port(self.midi_port_combobox.currentText())

    def change_midi_port(self, port_name):
        self.listener_thread.set_midi_port(port_name)
        if not self.listener_thread.isRunning():
            self.listener_thread.start()

    def update_spin_box(self, cc, value):
        for row, cc_spin_box in self.cc_spin_boxes.items():
            if cc_spin_box.value() == cc:
                self.value_spin_boxes[row].setValue(value)

    def update_displayed_cc_numbers(self, topLeft, bottomRight, roles):
        # stop spin box signals from triggering update_thread_cc_numbers
        for spin_box in self.cc_spin_boxes.values():
            spin_box.valueChanged.disconnect(self.update_thread_cc_numbers)
        
        df_table = self._table_model._data
        # iterate through df_table and update cc_spin_boxes
        for idx, row in df_table.iterrows():
            cc_val = row['CC']
            cc_spin_box = self.cc_spin_boxes[idx]
            cc_spin_box.setValue(int(cc_val))

        # for row, cc_spin_box in self.cc_spin_boxes.items():
        #     cc_val = df_table['CC'][row]
        #     cc_spin_box.setValue(int(cc_val))
        
        # reconnect signals
        for spin_box in self.cc_spin_boxes.values():
            spin_box.valueChanged.connect(self.update_thread_cc_numbers)

        self.update_thread_cc_numbers()

    def update_thread_cc_numbers(self):
        cc_numbers = [spin_box.value() for spin_box in self.cc_spin_boxes.values()]
        self.listener_thread.update_cc_numbers(cc_numbers)

    def closeEvent(self, event):
        print("Closing MIDI listener")
        self.listener_thread.stop()
        self.listener_thread.wait()
        super().closeEvent(event)

def main():
    app = QtWidgets.QApplication(sys.argv)
    listener_window = MidiListenerWindow()
    listener_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
