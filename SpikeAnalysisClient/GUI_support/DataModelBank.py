import typing
import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QModelIndex, Qt
import os
import ast

icon_tick = QtGui.QImage(os.path.dirname(os.path.realpath(__file__))+"/resource/icons/tick.png")
icon_cross = QtGui.QImage(os.path.dirname(os.path.realpath(__file__))+'/resource/icons/cross.png')

class ExperimenterModel(QtCore.QAbstractListModel):
    def __init__(self, *args, experimenter_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.experimenter_list = experimenter_list or []

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            experimenter = self.experimenter_list[index.row()]
            return experimenter

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.experimenter_list)

    def get_data(self):
        return self.experimenter_list

    def set_data(self, experimenter_list):
        self.experimenter_list = experimenter_list

class SystemModel(QtCore.QAbstractListModel):
    def __init__(self, *args, system_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.system_list = system_list or []

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            system = self.system_list[index.row()]
            return system

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.system_list)

    def get_data(self):
        return self.system_list

    def set_data(self, system_list):
        self.system_list = system_list

class AnimalIDModel(QtCore.QAbstractListModel):
    def __init__(self, *args, animal_id_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.animal_id_list = animal_id_list or []

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            animal_id = self.animal_id_list[index.row()]
            return animal_id

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.animal_id_list)

    def get_data(self):
        return self.animal_id_list

    def set_data(self, animal_id_list):
        self.animal_id_list = animal_id_list

class RecordingTimeModel(QtCore.QAbstractListModel):
    def __init__(self, *args, recording_time_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.recording_time_list = recording_time_list or []

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            recording_time = self.recording_time_list[index.row()]
            return recording_time

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.recording_time_list)

    def get_data(self):
        return self.recording_time_list

    def set_data(self, recording_time_list):
        self.recording_time_list = recording_time_list

class MetadataModel(QtCore.QAbstractTableModel):
    def __init__(self, *args, metadata_df=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata_df = metadata_df or pd.DataFrame([])

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self.metadata_df.iloc[index.row(), index.column()]
            return str(value)
        if role == Qt.BackgroundRole:
            value = self.metadata_df.iloc[index.row(), index.column()]
            if value in [None, np.nan]:
                return QtGui.QColor('red')


    def rowCount(self, parent: QModelIndex = ...) -> int:
        return self.metadata_df.shape[0]

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return  self.metadata_df.shape[1]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self.metadata_df.columns[section])
            if orientation == Qt.Vertical:
                return str(self.metadata_df.index[section])

    def get_data(self):
        return self.metadata_df

    def set_data(self, metadata_df):
        self.metadata_df = metadata_df

class MetadataProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ColumnSelectionModel(QtCore.QAbstractListModel):
    def __init__(self, *args, column_feature_selection=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_feature_selection = column_feature_selection or []

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            _, column_feature = self.column_feature_selection[index.row()]
            return column_feature
        if role == Qt.DecorationRole:
            status, _ = self.column_feature_selection[index.row()]
            if status:
                return icon_tick
            else:
                return icon_cross

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.column_feature_selection)

    def get_data(self):
        return self.column_feature_selection

    def set_data(self, column_feature_selection):
        self.column_feature_selection = column_feature_selection

    def set_row_data(self, row_data, row):
        self.column_feature_selection[row] = row_data

class ParameterSelectionModel(QtCore.QAbstractTableModel):
    def __init__(self, *args, parameter_df=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parameter_df = parameter_df or pd.DataFrame([])

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self.parameter_df.iloc[index.row(), index.column()]
            return str(value)
        if role == Qt.EditRole:
            value = self.parameter_df.iloc[index.row(), index.column()]
            return str(value)

    def setData(self, index: QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if role == Qt.EditRole:
            original_value = self.parameter_df.iloc[index.row(), index.column()]
            if type(original_value) == type(value):
                self.parameter_df.iloc[index.row(), index.column()] = value
                return True
            else:
                try:
                    value = ast.literal_eval(value)
                    if type(original_value) == type(value):
                        self.parameter_df.iloc[index.row(), index.column()] = value
                        return True
                    else:
                        print('edit failed')
                        return False
                except Exception:
                    print('edit failed')
                    return False


    def rowCount(self, parent: QModelIndex = ...) -> int:
        return self.parameter_df.shape[0]

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return  self.parameter_df.shape[1]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self.parameter_df.columns[section])
            if orientation == Qt.Vertical:
                return str(self.parameter_df.index[section])

    def get_data(self):
        return self.parameter_df

    def set_data(self, parameter_df):
        self.parameter_df = parameter_df

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if index.column() == 1:
            return QtCore.QAbstractTableModel.flags(self, index) | QtCore.Qt.ItemFlag.ItemIsEditable
        else:
            return QtCore.QAbstractTableModel.flags(self, index)

class ProcessSelectionModel(QtCore.QAbstractListModel):
    def __init__(self, *args, process_selection=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.process_selection = process_selection or []

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            _, process_selection = self.process_selection[index.row()]
            return process_selection
        if role == Qt.DecorationRole:
            status, _ = self.process_selection[index.row()]
            if status:
                return icon_tick
            else:
                return icon_cross

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.process_selection)

    def get_data(self):
        return self.process_selection

    def set_data(self, process_selection):
        self.process_selection = process_selection

    def set_row_data(self, row_data, row):
        self.process_selection[row] = row_data







