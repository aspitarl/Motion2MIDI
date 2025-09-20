from PyQt5.QtWidgets import QMainWindow, QTextEdit

class DebugConsoleWindow(QMainWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.setWindowTitle("Debug Console")
        self.setGeometry(100, 100, 600, 400)
        self.debug_console = QTextEdit()
        self.debug_console.setReadOnly(True)
        self.setCentralWidget(self.debug_console)

    def setText(self, text):
        self.debug_console.setText(text)

    def closeEvent(self, event):
        print("Closing debug console")
        self.hide()
        self.parent.main_widget.datathread.enable_debug = False
        super().closeEvent(event)