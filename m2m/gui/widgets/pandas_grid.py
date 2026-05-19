import sys
import pandas as pd
from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QHeaderView, QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QFileDialog, QGridLayout, QLabel, QSpinBox, QLineEdit, QComboBox, QCheckBox, QDateEdit, QDateTimeEdit, QTimeEdit, QDoubleSpinBox, QLayout
from PyQt5.QtCore import QModelIndex
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QFont

# missing imports

column_name_lookup = {
    'dim': 'Dimension',
    'CC': 'CC Number',
    'min_range': 'Min Range',
    'max_range': 'Max Range',
    'send': 'Send',
    'solo': 'Solo',
    'invert': 'Invert',
}

class PandasTableModel(QAbstractTableModel):

    _new_data = pyqtSignal(object) # this is a separate signal for when the data is changed from outside the model

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent):
        return self._data.shape[0]

    def columnCount(self, parent):
        return self._data.shape[1]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            return str(self._data.iloc[row, col])
        return QVariant()

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return QVariant()

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()
            self._data.iloc[row, col] = value
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        return False

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        
    def set_new_data(self, data):
        self._data = data
        self._new_data.emit(data)


class PandasGridWidget(QWidget):
    def __init__(self, data, parent=None, available_options=None):
        super().__init__(parent)
        self.available_options = available_options

        # Set size policy to prevent widget from changing size
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        self._current_solo_checkbox = None
        self._send_checkboxes = {}
        self._solo_checkboxes = {}

        #initialize to all true for case that solo is selected in preset
        self.presolo_send_states = [(i, True, True) for i in range(len(data))]

        self._table_model = PandasTableModel(data)
        self._table_model._new_data.connect(self._load_data)
        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(2)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSizeConstraint(QLayout.SetMinimumSize)
        self._widgets = []
        self._widget_types = {
            'int64': QSpinBox,
            'float64': QDoubleSpinBox,
            'object': QLineEdit,
            'category': QComboBox,
            'bool': QCheckBox,
            'datetime64[ns]': QDateTimeEdit,
            'timedelta64[ns]': QTimeEdit
        }
        self._load_data()
        self.setLayout(self._grid_layout)

    def _load_data(self):
        self._widgets = []
        self._send_checkboxes = {}
        self._solo_checkboxes = {}

        # Reset the layout
        if self.layout() is not None:
            QWidget().setLayout(self.layout())
        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(2)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.setLayout(self._grid_layout)

        data = self._table_model._data
        for i, col in enumerate(data.columns):
            label = QLabel(column_name_lookup[col])
            label.setSizePolicy(label.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
            label.setMaximumHeight(20)
            self._grid_layout.addWidget(label, 0, i)


            for j, val in enumerate(data[col]):
                if col == 'dim' and self.available_options:
                    widget = QComboBox()
                    widget.addItems(self.available_options)
                    widget.setCurrentText(str(val))
                    widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                    widget.setMaximumHeight(20)
                    widget.currentTextChanged.connect(lambda text, i=i, j=j: self._table_model.setData(self._table_model.index(j, i), text, Qt.EditRole))
                else:
                    widget_type = self._widget_types[str(data.dtypes[col])]
                    widget = widget_type()

                    # Set compact size policy and maximum height for all widgets
                    widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                    widget.setMaximumHeight(20)

                    if widget_type == QDoubleSpinBox:
                        widget.setDecimals(2)
                        widget.setSingleStep(0.1)
                        widget.setMaximum(999.99)
                        widget.setMinimum(-999.99)
                    elif widget_type == QSpinBox:
                        widget.setMaximum(127)
                        widget.setMinimum(0)
                    elif widget_type == QLineEdit:
                        widget.setMaximumWidth(80)
                        widget.setReadOnly(True)

                    widget = set_value_widget_type(widget, val)
                    signal = get_widget_change_signal(widget)

                    if widget_type == QCheckBox:
                        signal.connect(lambda state, i=i, j=j: self._table_model.setData(self._table_model.index(j, i), bool(state), Qt.EditRole))
                    else:
                        signal.connect(lambda value, i=i, j=j: self._table_model.setData(self._table_model.index(j, i), value, Qt.EditRole))

                if col == 'solo':
                    widget.stateChanged.connect(lambda state, row=j: self._disable_send_checkboxes(state, row))

                if col == 'send' and isinstance(widget, QCheckBox):
                    self._send_checkboxes[j] = widget
                elif col == 'solo' and isinstance(widget, QCheckBox):
                    self._solo_checkboxes[j] = widget

                self._grid_layout.addWidget(widget, j+1, i)
                self._widgets.append(widget)

        action_col = len(data.columns)
        action_label = QLabel('Action')
        action_label.setSizePolicy(action_label.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
        action_label.setMaximumHeight(20)
        self._grid_layout.addWidget(action_label, 0, action_col)

        for row in range(len(data)):
            remove_button = QPushButton('X')
            remove_button.setToolTip('Remove this row')
            remove_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            remove_button.setFixedSize(24, 20)
            remove_button.clicked.connect(lambda _, row=row: self.remove_row_at(row))
            self._grid_layout.addWidget(remove_button, row + 1, action_col)

        self._propagate_compact_resize()

    def _propagate_compact_resize(self):
        self.updateGeometry()
        self.adjustSize()

        parent = self.parentWidget()
        while parent is not None:
            parent.updateGeometry()
            if parent.layout() is not None:
                parent.layout().activate()
            if parent.isWindow():
                parent.adjustSize()
            parent = parent.parentWidget()

    def _disable_send_checkboxes(self, state, row):
        if state == Qt.Checked:
            current_row_solo = self._solo_checkboxes.get(row)
            if self._current_solo_checkbox is not None and self._current_solo_checkbox is not current_row_solo:
                self._current_solo_checkbox.blockSignals(True)
                self._current_solo_checkbox.setChecked(False)
                self._current_solo_checkbox.blockSignals(False)
            self._current_solo_checkbox = current_row_solo

            self.presolo_send_states = []
            for i in sorted(self._send_checkboxes):
                send_widget = self._send_checkboxes[i]
                self.presolo_send_states.append((i, send_widget.isChecked(), send_widget.isEnabled()))
                if i != row:
                    send_widget.setChecked(False)
                    send_widget.setEnabled(False)
                else:
                    # Make sure enabled is set to True for the solo row
                    send_widget.setChecked(True)
                    send_widget.setEnabled(True)
                    
        else:
            self._current_solo_checkbox = None
            for i, checked, enabled in self.presolo_send_states:
                if i not in self._send_checkboxes:
                    continue
                send_widget = self._send_checkboxes[i]
                send_widget.setEnabled(enabled)
                send_widget.setChecked(checked)


    def set_data(self, data):
        self._table_model._data = data

        # Emit dataChanged signal to update the table view
        # The dataChanged signal in Qt's model/view framework is designed to notify views and other interested parties that a portion of the model's data has changed.
        # If you emit the dataChanged signal without any parameters, it won't know which data has changed, and it may not trigger the expected updates in the views. This is why you need to provide the QModelIndex parameters.

        # Emit dataChanged signal to update the table view
        top_left = self._table_model.index(0, 0)
        parent = QModelIndex()  # Create an invalid QModelIndex
        bottom_right = self._table_model.index(self._table_model.rowCount(parent) - 1, self._table_model.columnCount(parent) - 1)

        self._table_model.dataChanged.emit(top_left, bottom_right)



        self._load_data()

    def add_row(self):
        new_row = pd.DataFrame([{
            'dim': self.available_options[0] if self.available_options else 'x',
            'CC': 0,
            'send': False,
            'solo': False,
            'min_range': 0.0,
            'max_range': 1.0,
            'invert': False
        }])
        self._table_model._data = pd.concat([self._table_model._data, new_row], ignore_index=True)
        self._load_data()

    def remove_row(self):
        if len(self._table_model._data) > 0:
            self.remove_row_at(len(self._table_model._data) - 1)

    def remove_row_at(self, row):
        if row < 0 or row >= len(self._table_model._data):
            return

        self._table_model._data = self._table_model._data.drop(self._table_model._data.index[row]).reset_index(drop=True)
        self._current_solo_checkbox = None
        self.presolo_send_states = [(i, True, True) for i in range(len(self._table_model._data))]
        self._load_data()
              



def get_widget_change_signal(widget):
    if isinstance(widget, QComboBox):
        return widget.currentIndexChanged
    elif isinstance(widget, QDateTimeEdit):
        return widget.dateTimeChanged
    elif isinstance(widget, QTimeEdit):
        return widget.timeChanged
    elif isinstance(widget, QDateEdit):
        return widget.dateChanged
    elif isinstance(widget, QCheckBox):
        return widget.stateChanged
    elif isinstance(widget, QLineEdit):
        return widget.textChanged
    else:
        return widget.valueChanged
    
def set_value_widget_type(widget, value):
    if isinstance(widget, QComboBox):
        widget.setCurrentIndex(value)
    elif isinstance(widget, QDateTimeEdit):
        widget.setDateTime(value)
    elif isinstance(widget, QTimeEdit):
        widget.setTime(value)
    elif isinstance(widget, QDateEdit):
        widget.setDate(value)
    elif isinstance(widget, QCheckBox):
        widget.setChecked(value)
    elif isinstance(widget, QLineEdit):
        widget.setText(value)
    else:
        widget.setValue(value)
    return widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = PandasGridWidget(pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6], 'C': [7, 8, 9]}))
    widget.show()
    sys.exit(app.exec_())