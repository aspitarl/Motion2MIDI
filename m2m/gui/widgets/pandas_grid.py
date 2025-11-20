import sys
import pandas as pd
from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QHeaderView, QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QFileDialog, QGridLayout, QLabel, QSpinBox, QLineEdit, QComboBox, QCheckBox, QDateEdit, QDateTimeEdit, QTimeEdit, QDoubleSpinBox
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
    def __init__(self, data, parent=None):
        super().__init__(parent)

        # Set size policy to prevent widget from changing size
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        self._current_solo_checkbox = None

        #initialize to all true for case that solo is selected in preset
        self.presolo_send_states = [(i, True, True) for i in range(len(data))]

        self._table_model = PandasTableModel(data)
        self._table_model._new_data.connect(self._load_data)
        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(2)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
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

        # Reset the layout
        if self.layout() is not None:
            QWidget().setLayout(self.layout())
        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(2)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._grid_layout)

        data = self._table_model._data
        for i, col in enumerate(data.columns):
            label = QLabel(column_name_lookup[col])
            label.setSizePolicy(label.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
            label.setMaximumHeight(20)
            self._grid_layout.addWidget(label, 0, i)


            for j, val in enumerate(data[col]):
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

                widget = set_value_widget_type(widget, val)
                signal = get_widget_change_signal(widget)

                if widget_type == QCheckBox:
                    signal.connect(lambda state, i=i, j=j: self._table_model.setData(self._table_model.index(j, i), bool(state), Qt.EditRole))
                else:
                    signal.connect(lambda value, i=i, j=j: self._table_model.setData(self._table_model.index(j, i), value, Qt.EditRole))

                if col == 'solo':
                    widget.stateChanged.connect(lambda state, row=j: self._disable_send_checkboxes(state, row))

                self._grid_layout.addWidget(widget, j+1, i)
                self._widgets.append(widget)

    def _disable_send_checkboxes(self, state, row):
        send_checkbox_column = 2
        send_column_offset = send_checkbox_column*len(self._table_model._data)

        solo_checkbox_column = 3
        solo_column_offset = solo_checkbox_column*len(self._table_model._data)
        if state == Qt.Checked:
            if self._current_solo_checkbox is not None:
                self._current_solo_checkbox.setChecked(False)
            self._current_solo_checkbox = self._widgets[row+solo_column_offset]

            self.presolo_send_states = []
            for i in range(len(self._table_model._data)):
                send_widget = self._widgets[i+send_column_offset]
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
                send_widget = self._widgets[i+send_column_offset]
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