from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
from PyQt5 import QtCore
import sys
import traceback

class ErrorDialog(QDialog):
    def __init__(self, short_message, detailed_message, parent=None, always_on_top=False):
        super().__init__(parent)
        self.setWindowTitle("An Error Occurred")
        self.resize(600, 400)  # Set larger default size

        if always_on_top:
            self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)

        layout = QVBoxLayout()

        # Short message
        label = QLabel("An unexpected error occurred.")
        layout.addWidget(label)

        # Informative text
        informative_label = QLabel(short_message)
        layout.addWidget(informative_label)

        # Detailed text
        self.detailed_text = QTextEdit()
        self.detailed_text.setReadOnly(True)
        self.detailed_text.setText(detailed_message)
        layout.addWidget(self.detailed_text)

        # OK button
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

class ErrorLogger:
    def __init__(self, always_on_top=False):
        self.always_on_top = always_on_top

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        short_message = str(exc_value)

        # Create and show the custom error dialog
        error_dialog = ErrorDialog(short_message, error_message, always_on_top=self.always_on_top)
        error_dialog.exec_()