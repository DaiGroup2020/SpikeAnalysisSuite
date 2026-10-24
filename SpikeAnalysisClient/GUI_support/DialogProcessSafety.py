from PyQt5 import QtCore, QtGui, QtWidgets
from .DialogProcessSafetyScheme import Ui_DialogProcessSafety
from .DataModelBank import ColumnSelectionModel

class DialogProcessSafety(QtWidgets.QDialog, Ui_DialogProcessSafety):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.process_safety_model = ColumnSelectionModel()
        self.listViewProcessSafety.setModel(self.process_safety_model)
        self.listViewProcessSafety.selectionModel().selectionChanged.connect(self.process_safety_changed)

    def set_feature_safety(self, process_safety):
        self.process_safety_model.set_data(process_safety)
        self.process_safety_model.layoutChanged.emit()

    def get_feature_safety(self):
        return self.process_safety_model.get_data()

    def process_safety_changed(self):
        process_safety = self.process_safety_model.get_data()
        index = self.listViewProcessSafety.selectedIndexes()[0]
        row = index.row()
        status, process = process_safety[row]
        self.process_safety_model.set_row_data((not status, process), row)
        self.process_safety_model.dataChanged.emit(index, index)


