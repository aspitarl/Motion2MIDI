import os
import logging

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon

from m2m.gui.layouts.distance_layout import DistanceLayout
from m2m.core.osc_handler import OSCPresetLayout
from m2m.gui.layouts.window_manager import WindowManagerLayout

script_path = os.path.dirname(os.path.realpath(__file__))

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.setWindowIcon(QIcon(os.path.join(script_path, 'icon/icon_multi.png')))
        # Create a central widget and set a vertical layout
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Add WindowManagerLayout at the top
        self.window_manager_layout = WindowManagerLayout(parent=self)
        layout.addLayout(self.window_manager_layout)

        # add splitter 
        layout.addWidget(QtWidgets.QSplitter())
        
        # Wrap DistanceLayout in a QWidget
        self.distance_widget = QtWidgets.QWidget()
        self.distance_layout = DistanceLayout(parent=self)
        self.distance_widget.setLayout(self.distance_layout)
        self.distance_widget.setVisible(False)  # Hide by default
        layout.addWidget(self.distance_widget)

        # Wrap OSC preset layout in a QWidget
        self.osc_widget = QtWidgets.QWidget()
        self.osc_preset_layout = OSCPresetLayout(parent=self)
        self.osc_widget.setLayout(self.osc_preset_layout)
        self.osc_widget.setVisible(False)  # Hide by default
        layout.addWidget(self.osc_widget)

        self.osc_preset_layout.osc_preset_table.itemSelectionChanged.connect(self.update_subwindow_settings)

        #TODO: cannot get width to follow the table correctly
        # Set initial width of the main window
        self.setMinimumWidth(380)

        # Create menu bar
        self.create_menu_bar()

    def update_subwindow_settings(self):
        selected_rows = self.osc_preset_layout.osc_preset_table.selectionModel().selectedRows()
        if len(selected_rows) > 0:
            selected_row = selected_rows[0].row()
            selected_preset = self.osc_preset_layout.osc_preset_table.item(selected_row, 0).text()
            logging.debug(f"Selected preset: {selected_preset}")
            for window_num, window in enumerate(self.window_manager_layout.windows.values()):
                fileselect_combobox = window.main_widget.settings_layout._fileselect_combo
                table_preset_name_for_window = self.osc_preset_layout.osc_preset_table.item(selected_row, window_num + 1).text()
                table_preset_name_for_window = table_preset_name_for_window.strip()
                # check if the preset name is in the fileselect_combobox
                if table_preset_name_for_window in [fileselect_combobox.itemText(i) for i in range(fileselect_combobox.count())]:
                    fileselect_combobox.setCurrentText(table_preset_name_for_window)
                    fileselect_combobox.currentIndexChanged.emit(fileselect_combobox.currentIndex())
                else:
                    logging.warning(f"Preset {table_preset_name_for_window} not found in fileselect_combobox for window {window_num + 1}")

    def create_menu_bar(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu('View')

        self.always_on_top_action = QtWidgets.QAction('Always on Top', self, checkable=True)
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)
        self.always_on_top_action.setShortcut('Ctrl+T')
        view_menu.addAction(self.always_on_top_action)

        self.show_distance_layout_action = QtWidgets.QAction('Show Distance Layout', self, checkable=True)
        self.show_distance_layout_action.triggered.connect(self.toggle_distance_layout)
        self.show_distance_layout_action.setChecked(False)  # Not checked by default
        self.show_distance_layout_action.setShortcut('Ctrl+D')  # Add keyboard shortcut
        view_menu.addAction(self.show_distance_layout_action)

        self.show_osc_layout_action = QtWidgets.QAction('Show OSC Layout', self, checkable=True)
        self.show_osc_layout_action.triggered.connect(self.toggle_osc_layout)
        self.show_osc_layout_action.setChecked(False)  # Not checked by default
        self.show_osc_layout_action.setShortcut('Ctrl+O')  # Add keyboard shortcut
        view_menu.addAction(self.show_osc_layout_action)

    #TODO: this is not behaving as expected under multiple toggles
    def toggle_distance_layout(self, checked):
        # get the current height of the main window and distance widget
        main_window_height = self.height()
        distance_widget_height = self.distance_widget.height() 
        self.distance_widget.setVisible(checked)
        # set the height of the main window to the main window height - distance widget height
        if checked:
            default_distance_widget_height = 200
            self.resize(self.width(), main_window_height + default_distance_widget_height)
            self.distance_widget.setMinimumHeight(default_distance_widget_height)
        else:
            self.resize(self.width(), main_window_height - distance_widget_height)

    def toggle_osc_layout(self, checked):
        # get the current height of the main window and osc widget
        main_window_height = self.height()
        osc_widget_height = self.osc_widget.height()
        self.osc_widget.setVisible(checked)
        # set the height of the main window to the main window height - osc widget height
        if checked:
            default_osc_widget_height = 200
            self.resize(self.width(), main_window_height + default_osc_widget_height)
            self.osc_widget.setMinimumHeight(default_osc_widget_height)
        else:
            self.resize(self.width(), main_window_height - osc_widget_height)

    def toggle_always_on_top(self, checked):
        if checked:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
        self.show()

    def closeEvent(self, event):
        QtWidgets.QApplication.quit()  # Ensure the program exits when the control window is closed
