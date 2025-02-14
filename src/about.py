import os
from PyQt5.QtWidgets import QMessageBox, QPushButton, QVBoxLayout, QDialog, QLabel, QTextEdit
from PyQt5.QtCore import Qt

from version import VERSION

script_path = os.path.dirname(os.path.realpath(__file__))
license_path = os.path.join(script_path, '..', 'LICENSE')

def show_about_dialog(parent):
    about_text = [
        "Motion2MIDI",
        f"Version: {VERSION}",
        "",
        "Copyright (C) 2025 Lee Aspitarte",
    ]

    about_dialog = QDialog(parent)
    about_dialog.setWindowTitle("About Motion2MIDI")
    layout = QVBoxLayout()

    for line in about_text:
        label = QLabel(line)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

    license_button = QPushButton("License")
    license_button.clicked.connect(lambda: show_license_dialog(parent))
    layout.addWidget(license_button)

    about_dialog.setLayout(layout)
    about_dialog.exec_()

def show_license_dialog(parent):
    with open(license_path, 'r') as file:
        license_text = file.read()

    license_dialog = QDialog(parent)
    license_dialog.setWindowTitle("License")
    layout = QVBoxLayout()

    license_text_edit = QTextEdit()
    license_text_edit.setReadOnly(True)
    license_text_edit.setText(license_text)
    layout.addWidget(license_text_edit)

    license_dialog.setLayout(layout)
    license_dialog.exec_()