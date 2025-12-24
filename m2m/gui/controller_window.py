from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QSplitter, QMenuBar, QAction, QTextEdit, QSpinBox, QLabel, 
    QMainWindow, QDialog, QComboBox, QPushButton, QWidget, QFrame, QCheckBox, QFileDialog, QMessageBox
)
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QValidator, QCloseEvent, QIcon
import os
import sys
import mido
from mido.backends import rtmidi  # pyinstaller

# Import custom modules
from m2m.gui.widgets.controller_widget import ControllerWidget
from m2m.gui.widgets.midi_listener import MidiListenerWindow
from m2m.gui.widgets.debug_console import DebugConsoleWindow
from m2m.gui.widgets.error_dialog import ErrorLogger
from m2m.utils.about import show_about_dialog

script_path = os.path.dirname(os.path.realpath(__file__))

class ControllerWindow(QtWidgets.QMainWindow):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowIcon(QIcon(os.path.join(script_path, 'icon/icon.png')))

        self.main_widget = ControllerWidget(name=name, parent=self)
        self.setCentralWidget(self.main_widget)
        self.main_widget.connection_layout.combobox_selections_changed.connect(self.connections_changed)
        self.main_widget.title_update_requested.connect(self.update_title)

        self.name = name
        self.midi_listener_window = MidiListenerWindow(parent=self)
        self.midi_listener_window.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.midi_listener_window.hide()

        self.debug_console_window = DebugConsoleWindow(parent=self)
        self.debug_console_window.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.debug_console_window.hide()

        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)

        # Add 'View' menu
        viewMenu = menuBar.addMenu('View')

        # Add 'Always on Top' action
        self.always_on_top_action = QAction('Always on Top', self, checkable=True)
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)
        self.always_on_top_action.setShortcut('Ctrl+T')
        viewMenu.addAction(self.always_on_top_action)

        # Add 'Utility' menu
        utilityMenu = menuBar.addMenu('Utility')

        # Add 'Range Set Mode' action
        self.range_set_action = QAction('Range Set Mode', self, checkable=True)
        self.range_set_action.triggered.connect(self.toggle_range_set_mode)
        self.range_set_action.setShortcut('Ctrl+R')
        utilityMenu.addAction(self.range_set_action)

        self.toggle_midi_listener_action = QAction('Open/Close MIDI Listener', self)
        self.toggle_midi_listener_action.triggered.connect(self.toggle_midi_listener)
        self.toggle_midi_listener_action.setShortcut('Ctrl+M')
        utilityMenu.addAction(self.toggle_midi_listener_action)

        self.toggle_debug_console_action = QAction('Open/Close Debug Console', self)
        self.toggle_debug_console_action.triggered.connect(self.toggle_debug_console)
        self.toggle_debug_console_action.setShortcut('Ctrl+D')
        utilityMenu.addAction(self.toggle_debug_console_action)

        # Add 'Help' menu
        helpMenu = menuBar.addMenu('Help')

        # Add 'About' action
        about_action = QAction('About', self)
        about_action.triggered.connect(lambda: show_about_dialog(self))
        helpMenu.addAction(about_action)

        # Set up the error logger
        self.error_logger = ErrorLogger(always_on_top=self.always_on_top_action.isChecked())
        sys.excepthook = self.error_logger.handle_exception

        self.update_title()

    def connections_changed(self):
        # if connected then disconnect and reconnect
        if self.main_widget.connection_layout.checkbox_isconnected.isChecked():
            self.main_widget.disconnect_objects()
            self.main_widget.connect_object()
        self.update_title()

    def toggle_always_on_top(self, state):
        if self.always_on_top_action.isChecked():
            self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, False)
        self.show()
        self.error_logger.always_on_top = self.always_on_top_action.isChecked()

    def toggle_range_set_mode(self, state):
        if state:
            self.main_widget.datathread.active_mode_manual_bypass = True
            self.main_widget.datathread.manual_range_set = state
        else:
            self.main_widget.datathread.manual_range_set = state

    def toggle_midi_listener(self):
        if self.midi_listener_window.isVisible():
            self.midi_listener_window.close()
        else:
            self.midi_listener_window.show()
            current_output_port = self.main_widget.connection_layout.combobox_midi_ports.currentText()
            current_output_port_base = current_output_port.split(' ')[0]
            input_ports = mido.get_input_names()
            for port in input_ports:
                if port.startswith(current_output_port_base):
                    print(f"Found corresponding input port: {port}")
                    self.midi_listener_window.midi_port_combobox.setCurrentText(port)
            self.activateWindow()
            main_window_geometry = self.geometry()
            midi_listener_geometry = self.midi_listener_window.geometry()
            self.midi_listener_window.move(main_window_geometry.right(), main_window_geometry.top())

    def toggle_debug_console(self):
        if self.debug_console_window.isVisible():
            self.debug_console_window.close()
            self.main_widget.datathread.enable_debug = False
        else:
            self.debug_console_window.show()
            self.main_widget.datathread.debug_signal.connect(self.debug_console_window.setText)
            self.main_widget.datathread.enable_debug = True

    def closeEvent(self, a0: QCloseEvent) -> None:
        print('Received Close event, Disconnecting Objects')
        if self.main_widget.settings_layout.checkbox_invert_toggle.isChecked():
            self.main_widget.settings_layout.checkbox_invert_toggle.setChecked(False)
            self.main_widget.datathread.stop()
        self.main_widget.disconnect_objects()
        return super().closeEvent(a0)
    
    def update_title(self):
        contr = self.main_widget.datathread.contr
        if self.name == "Single":
            window_title = "Motion2MIDI"
        else:
            window_title = "{}: Motion2MIDI Multi".format(self.name)
        
        if contr:
            window_title = "{} - ".format(contr) + window_title      

        self.setWindowTitle(window_title)

from m2m.gui.theme import apply_dark_theme

def main():
    app = QtWidgets.QApplication(sys.argv)
    apply_dark_theme(app)
    main_window = ControllerWindow("Single")
    main_window.main_widget.main_window = main_window  # Weird way to allow main widget to change window title...
    main_window.resize(400, 200)  # Set initial window size small (smaller than widgets normally make it so smallest that is normally resized)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()