from PyQt5 import QtCore, QtGui, QtWidgets
from .DialogColumnFeatureSelectionScheme import Ui_DialogColumnFeature
from .DataModelBank import ColumnSelectionModel

class DialogColumnFeatureSelection(QtWidgets.QDialog, Ui_DialogColumnFeature):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.column_selection_model = ColumnSelectionModel()
        self.listViewColumnFeature.setModel(self.column_selection_model)
        self.listViewColumnFeature.selectionModel().selectionChanged.connect(self.column_feature_selection_changed)

    def set_column_feature_selection(self, column_feature_selection):
        self.column_selection_model.set_data(column_feature_selection)
        self.column_selection_model.layoutChanged.emit()

    def get_column_feature_selection(self):
        return self.column_selection_model.get_data()

    def column_feature_selection_changed(self):
        column_feature_selection = self.column_selection_model.get_data()
        index = self.listViewColumnFeature.selectedIndexes()[0]
        row = index.row()
        status, column_feature = column_feature_selection[row]
        self.column_selection_model.set_row_data((not status, column_feature), row)
        self.column_selection_model.dataChanged.emit(index,index)

