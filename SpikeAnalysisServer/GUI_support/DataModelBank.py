import typing
import pandas as pd
from PyQt5 import QtCore
from PyQt5.QtCore import QModelIndex, Qt

class TaskManagerModel(QtCore.QAbstractTableModel):
    def __init__(self, *args, task_manager_df=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_manager_df = task_manager_df or pd.DataFrame([], columns=['UserName', 'IP', 'PID', 'Process',
                                                                            'DataInfo'])

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self.task_manager_df.iloc[index.row(), index.column()]
            return str(value)


    def rowCount(self, parent: QModelIndex = ...) -> int:
        return self.task_manager_df.shape[0]

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return  self.task_manager_df.shape[1]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self.task_manager_df.columns[section])
            if orientation == Qt.Vertical:
                return str(self.task_manager_df.index[section])

    def get_data(self):
        return self.task_manager_df

    def set_data(self, task_manager_df):
        self.task_manager_df = task_manager_df

    def update_user_task(self, user_name, ip, pid, process, data_info):
        if any(self.task_manager_df['UserName'].isin([user_name])):
            self.task_manager_df[self.task_manager_df['UserName'].isin([user_name])] = \
                [user_name, ip, pid, process, data_info]
            self.task_manager_df = self.task_manager_df.drop_duplicates()
        else:
            self.task_manager_df.loc[len(self.task_manager_df)] = [user_name, ip, pid, process, data_info]

    def clear_user_task(self, user_name):
        self.task_manager_df = self.task_manager_df[~self.task_manager_df['UserName'].isin([user_name])]






class TaskManagerProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



















