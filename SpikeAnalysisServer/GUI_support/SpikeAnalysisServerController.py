import time
import json
import os
import traceback
from pprint import pprint
import psutil
import spikeinterface.sorters as ss
from PyQt5 import QtCore, QtGui, QtWidgets
from .SpikeAnalysisServerControllerScheme import Ui_MainWindow
from .utils.NetworkUtils import pack, unpack, Envelope, MySocket
from .utils.ThreadUtils import ServerThread, ServerPackage
from threading import Event as threadEvent
from .utils.FunctionUtils import kill_process_tree
from .utils.PipelineUtils import server_main_thread
from .DataModelBank import TaskManagerModel, TaskManagerProxyModel




class SpikeAnalysisServer(QtWidgets.QMainWindow, Ui_MainWindow):
    package = ServerPackage()
    def __init__(self, server_ip):
        super().__init__()
        self.setupUi(self)
        if os.environ.get('KILOSORT3_PATH'):
            ss.Kilosort3Sorter.set_kilosort3_path(os.environ['KILOSORT3_PATH'])
        if os.environ.get('KILOSORT2_PATH'):
            ss.Kilosort2Sorter.set_kilosort2_path(os.environ['KILOSORT2_PATH'])
        if os.environ.get('KILOSORT_PATH'):
            ss.KilosortSorter.set_kilosort_path(os.environ['KILOSORT_PATH'])
        self.package.root = os.path.abspath(os.environ.get('SPIKE_DATA_ROOT', './data'))
        self.package.server_ip = server_ip
        self.package.port = 1113
        self.package.client_port = 2113
        self.package.client_ip_dict = {}
        self.thread_main = None
        self.package.run_stop_set = threadEvent()
        self.run_flag = False
        self.package.user_info = {}
        self.load_user_info()
        self.package.process_data_parameter_queue_dict = {}
        self.package.task_reply_buffer_dict = {}
        self.package.pid_dict = {}
        self.package.current_user_list = []

        self.task_manager_model = TaskManagerModel()
        self.task_manager_proxy_model = TaskManagerProxyModel()
        self.task_manager_proxy_model.setSourceModel(self.task_manager_model)
        self.tableViewTaskManager.setModel(self.task_manager_proxy_model)
        self.tableViewTaskManager.setSelectionBehavior(QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.tableViewTaskManager.verticalHeader().setVisible(False)


        self.pushButtonRun.clicked.connect(self.run_button_clicked)
        self.pushButtonShow.clicked.connect(self.show_all_dict_and_list)
        self.icon_run = QtGui.QIcon(os.path.dirname(os.path.realpath(__file__)) + "/resource/icons/control.png")
        self.icon_stop = QtGui.QIcon(
            os.path.dirname(os.path.realpath(__file__)) + '/resource/icons/control-stop-square.png')
        self.pushButtonRun.setIcon(self.icon_run)
        self.package.task_manager_update_signal.connect(self.update_user_task_on_task_manager)
        self.package.task_manager_clear_signal.connect(self.clear_user_task_on_task_manager)
        self.pushButtonShutdownUser.clicked.connect(self.shutdown_user_tasks)

    def show_all_dict_and_list(self):
        print('client_ip_dict')
        pprint(self.package.client_ip_dict)
        print('process_data_parameter_queue_dict')
        pprint(self.package.process_data_parameter_queue_dict)
        print('pid_dict')
        pprint(self.package.pid_dict)
        print('current_user_list')
        pprint(self.package.current_user_list)

    def update_user_task_on_task_manager(self, task_manager_info):
        [user_name, ip, pid, process, data_info] = task_manager_info
        self.task_manager_proxy_model = TaskManagerProxyModel()
        self.task_manager_proxy_model.setSourceModel(self.task_manager_model)
        self.tableViewTaskManager.setModel(self.task_manager_proxy_model)
        self.task_manager_model.update_user_task(user_name, ip, pid, process, data_info)
        self.task_manager_model.layoutChanged.emit()
        self.tableViewTaskManager.clearSelection()
        self.tableViewTaskManager.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def clear_user_task_on_task_manager(self, user_name):
        self.task_manager_proxy_model = TaskManagerProxyModel()
        self.task_manager_proxy_model.setSourceModel(self.task_manager_model)
        self.tableViewTaskManager.setModel(self.task_manager_proxy_model)
        self.task_manager_model.clear_user_task(user_name)
        self.task_manager_model.layoutChanged.emit()
        self.tableViewTaskManager.clearSelection()
        self.tableViewTaskManager.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)



    def run_button_clicked(self):
        if not self.run_flag:
            self.pushButtonRun.setIcon(self.icon_stop)
            self.run_flag = True
            self.run()
        else:
            self.pushButtonRun.setIcon(self.icon_run)
            self.run_flag = False
            self.stop()

    def run(self):
        print('Spike Analysis Server Start')
        self.package.run_stop_set.clear()
        self.thread_main = ServerThread(server_main_thread, self.package)
        self.thread_main.start()

    def stop(self):
        try:
            print('Spike Analysis Server Stop')
            self.package.run_stop_set.set()
            for key in self.package.process_data_parameter_queue_dict.keys():
                self.package.process_data_parameter_queue_dict[key] = []
            for pid in self.package.pid_dict.values():
                kill_process_tree(pid)
            try:
                temp = MySocket()
                temp.connect((self.package.server_ip, self.package.port))
                temp.close()
            except Exception:
                pass
            #self.package.process_data_parameter_queue_dict = {}
            #self.package.client_ip_dict = {}
            #self.package.task_reply_buffer_dict = {}
            #self.package.pid_dict = {}
        except Exception as e:
            traceback.print_exc()
            print(e)

    def shutdown_user_tasks(self):
        task_manager_inds = [self.task_manager_proxy_model.mapToSource(idx).row() for idx in
                         self.tableViewTaskManager.selectionModel().selectedRows()]
        task_manager_selected = self.task_manager_model.get_data().iloc[task_manager_inds, :]
        user_name_list = task_manager_selected['UserName'].to_list()
        try:
            print('Force shutting down all tasks for following users: ' + str(user_name_list))
            for user_name in user_name_list:
                if user_name in self.package.process_data_parameter_queue_dict.keys():
                    self.package.process_data_parameter_queue_dict[user_name] = []
                if user_name in self.package.pid_dict.keys():
                    kill_process_tree(self.package.pid_dict[user_name])
        except Exception as e:
            traceback.print_exc()
            print(e)


    def load_user_info(self):
        try:
            with open(os.path.dirname(
                    os.path.realpath(__file__)) + '/settings/user_info_data.json',
                      'r') as f:
                self.package.user_info = json.load(f)
        except Exception:
            self.package.user_info = {}
            print('Unable to read user_info_data.json, debug!')

    def display_thread_error_message(self, tuple_info):
        print('Thread failed, debug!')
        for i in tuple_info:
            print(i)







    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        try:
            if self.run_flag:
                self.pushButtonRun.setIcon(self.icon_run)
                self.run_flag = False
                self.stop()
        except Exception as e:
            traceback.print_exc()
            print(e)
        return super().closeEvent(a0)





