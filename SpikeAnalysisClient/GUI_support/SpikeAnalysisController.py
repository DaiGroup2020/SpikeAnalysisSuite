import json
import os.path
import os
import pprint
import traceback
import time

import psutil
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThreadPool, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from .SpikeAnalysisControllerScheme import Ui_MainWindow
from .DataModelBank import ExperimenterModel, SystemModel, AnimalIDModel, RecordingTimeModel, MetadataModel, MetadataProxyModel, ProcessSelectionModel
from .utils.DataUtils import DataRouter, MetaDataBase
from .DialogColumnFeatureSelection import DialogColumnFeatureSelection
from .DialogParameterSelection import DialogParameterSelection
from .DialogProcessSafety import DialogProcessSafety
from .utils.FunctionUtils import str2bool, get_host_ip, kill_process_tree
from .utils.ThreadUtils import Worker, WorkerPackage
from .utils.PipelineUtils import send_tasks_to_server, listen_tasks_from_server, do_tasks_on_client
from .utils.SpikeAnalysisUtils import task_separation
from .utils.NetworkUtils import pack, unpack, Envelope, MySocket
import pandas as pd
import numpy as np
from pprint import pprint







class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    package = WorkerPackage()
    def __init__(self, server_ip, user_name, user_folder_name):
        super().__init__()
        self.setupUi(self)
        self.package.root = 'Z:/'
        self.package.server_ip = server_ip
        self.package.port = 1113
        self.package.client_ip = get_host_ip()
        self.package.client_port = 2113
        self.package.user_name = user_name
        self.show_user_name()
        self.user_folder_name = user_folder_name
        self.package.task_wait_list = None
        self.package.task_queue = None
        self.package.task_to_server_list = None
        self.package.task_total_number = None
        self.package.task_finished_number = None
        self.package.server_working = None
        self.package.client_working = None
        # self.thread_lock = threading.Lock()
        self.package.thread_ending_display_flag = None
        self.wait_for_server_time = 2*3600*1000
        self.server_timer = QtCore.QTimer()
        self.server_timer.timeout.connect(self.server_time_out)
        self.package.start_timer_signal.connect(self.start_timer)
        self.package.stop_timer_signal.connect(self.stop_timer)
        self.package.update_progress_bar_signal.connect(self.update_progress_bar)
        self.package.worker_pid = None
        self.run_state = False

        self.data_router = DataRouter()
        self.data_router.set_root(self.package.root)
        self.data_router.route()
        self.metadatabase = MetaDataBase()
        self.metadatabase.set_root(self.package.root)
        self.column_feature_selection = None
        self.load_column_feature_selection_data()
        self.package.spike_sorting_parameter = None
        self.package.post_curation_parameter = None
        self.package.waveform_extraction_parameter = None
        self.package.figure_generation_parameter = None
        self.load_parameter_selection_data()
        self.process_selection = [(False, "SpikeSorting"), (False, "PostCuration"), (False, "WaveformExtraction"), (False, "FigureGeneration")]
        self.process_safety = [(True, "SpikeSorting"), (False, "PostCuration"), (True, "WaveformExtraction"), (False, "FigureGeneration")]
        self.threadpool = QThreadPool()

        self.experimenter_model = ExperimenterModel()
        self.listViewExperimenter.setModel(self.experimenter_model)
        self.listViewExperimenter.selectionModel().selectionChanged.connect(self.experimenter_selection_changed)
        self.system_model = SystemModel()
        self.listViewSystem.setModel(self.system_model)
        self.listViewSystem.selectionModel().selectionChanged.connect(self.system_selection_changed)
        self.animal_id_model = AnimalIDModel()
        self.listViewAnimalID.setModel(self.animal_id_model)
        self.listViewAnimalID.selectionModel().selectionChanged.connect(self.animal_id_selection_changed)
        self.recording_time_model = RecordingTimeModel()
        self.listViewRecordingTime.setModel(self.recording_time_model)
        self.listViewRecordingTime.selectionModel().selectionChanged.connect(self.recording_time_selection_changed)
        self.initiate_route_views()
        self.metadata_model = MetadataModel()
        self.metadata_proxy_model = MetadataProxyModel()
        self.metadata_proxy_model.setSourceModel(self.metadata_model)
        self.tableViewMetadata.setModel(self.metadata_proxy_model)
        # self.tableViewMetadata.setModel(self.metadata_model)
        self.set_metadata_column_visible()
        self.tableViewMetadata.setSelectionBehavior(QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.process_selection_model = ProcessSelectionModel()
        self.listViewProcess.setModel(self.process_selection_model)
        self.listViewProcess.selectionModel().selectionChanged.connect(self.process_selection_changed)
        self.set_process_selection(self.process_selection)
        self.progressBar.setValue(0)
        self.progressBar.setEnabled(False)

        self.pushButtonMetadata.clicked.connect(self.metadata_button_clicked)
        self.actionMetadataFeature.setStatusTip("Change Metadata Column Feature Displayed.")
        self.actionMetadataFeature.triggered.connect(self.metadata_column_feature_selected)
        self.actionProcessParameter.setStatusTip("Change Spike Analyzing Process Parameter Selection.")
        self.actionProcessParameter.triggered.connect(self.process_parameter_selected)
        self.actionProcessSafety.setStatusTip("Change Spike Analyzing Process Safety Mode.")
        self.actionProcessSafety.triggered.connect(self.process_safety_selected)
        self.pushButtonRun.clicked.connect(self.run_button_clicked)
        self.pushButtonAutoRun.clicked.connect(self.auto_run_button_clicked)

        self.icon_run = QtGui.QIcon(os.path.dirname(os.path.realpath(__file__)) + "/resource/icons/control.png")
        self.icon_stop = QtGui.QIcon(os.path.dirname(os.path.realpath(__file__)) + '/resource/icons/control-stop-square.png')
        self.pushButtonRun.setIcon(self.icon_run)
        self.pushButtonAutoRun.setIcon(self.icon_run)

    def set_user_name(self, user_name):
        self.package.user_name = user_name

    def get_user_name(self):
        return self.package.user_name

    def show_user_name(self):
        self.setWindowTitle(self.windowTitle() + '   (User: '+self.package.user_name+' )')

    def experimenter_selection_changed(self):
        experimenter_list = self.experimenter_model.get_data()
        selected_experimenter = [experimenter_list[idx.row()] for idx in self.listViewExperimenter.selectedIndexes()]
        self.system_model.set_data(self.data_router.query_system_list(selected_experimenter))
        self.system_model.layoutChanged.emit()
        self.listViewSystem.clearSelection()
        self.animal_id_model.set_data([])
        self.animal_id_model.layoutChanged.emit()
        self.listViewAnimalID.clearSelection()
        self.recording_time_model.set_data([])
        self.recording_time_model.layoutChanged.emit()
        self.listViewRecordingTime.clearSelection()

    def system_selection_changed(self):
        experimenter_list = self.experimenter_model.get_data()
        selected_experimenter = [experimenter_list[idx.row()] for idx in self.listViewExperimenter.selectedIndexes()]
        system_list = self.system_model.get_data()
        selected_system = [system_list[idx.row()] for idx in self.listViewSystem.selectedIndexes()]
        self.animal_id_model.set_data(self.data_router.query_animal_id_list(selected_experimenter, selected_system))
        self.animal_id_model.layoutChanged.emit()
        self.listViewAnimalID.clearSelection()
        self.recording_time_model.set_data([])
        self.recording_time_model.layoutChanged.emit()
        self.listViewRecordingTime.clearSelection()


    def animal_id_selection_changed(self):
        experimenter_list = self.experimenter_model.get_data()
        selected_experimenter = [experimenter_list[idx.row()] for idx in self.listViewExperimenter.selectedIndexes()]
        system_list = self.system_model.get_data()
        selected_system = [system_list[idx.row()] for idx in self.listViewSystem.selectedIndexes()]
        animal_id_list = self.animal_id_model.get_data()
        selected_animal_id = [animal_id_list[idx.row()] for idx in self.listViewAnimalID.selectedIndexes()]
        self.recording_time_model.set_data(self.data_router.query_recording_time_list(selected_experimenter,
                                                                                      selected_system,
                                                                                      selected_animal_id))
        self.recording_time_model.layoutChanged.emit()
        self.listViewRecordingTime.clearSelection()

    def recording_time_selection_changed(self):
        pass
        '''
        recording_time_list = self.recording_time_model.get_data()
        selected_recording_time = [recording_time_list[idx.row()] for idx in self.listViewRecordingTime.selectedIndexes()]
        print(selected_recording_time)
        '''

    def metadata_button_clicked(self):
        experimenter_list = self.experimenter_model.get_data()
        selected_experimenter = [experimenter_list[idx.row()] for idx in self.listViewExperimenter.selectedIndexes()]
        system_list = self.system_model.get_data()
        selected_system = [system_list[idx.row()] for idx in self.listViewSystem.selectedIndexes()]
        animal_id_list = self.animal_id_model.get_data()
        selected_animal_id = [animal_id_list[idx.row()] for idx in self.listViewAnimalID.selectedIndexes()]
        recording_time_list = self.recording_time_model.get_data()
        selected_recording_time = [recording_time_list[idx.row()] for idx in
                                   self.listViewRecordingTime.selectedIndexes()]
        selected_dataset = self.data_router.get_selected_dataset(selected_experimenter, selected_system,
                                                                 selected_animal_id, selected_recording_time)
        if not selected_dataset.empty:
            self.metadata_proxy_model = MetadataProxyModel()
            self.metadata_proxy_model.setSourceModel(self.metadata_model)
            self.tableViewMetadata.setModel(self.metadata_proxy_model)
            # self.metadata_proxy_mode.
            self.metadatabase.search_metadata(selected_dataset)
            self.metadata_model.set_data(self.metadatabase.get_metadata_df())
            self.metadata_model.layoutChanged.emit()
            self.tableViewMetadata.clearSelection()
            self.tableViewMetadata.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            self.set_metadata_column_visible()

    def metadata_column_feature_selected(self):
        dlg_column_feature_selection = DialogColumnFeatureSelection(self)
        dlg_column_feature_selection.set_column_feature_selection(self.column_feature_selection)
        result = dlg_column_feature_selection.exec_()
        if result == QMessageBox.Accepted:
            self.column_feature_selection = dlg_column_feature_selection.get_column_feature_selection()
            self.save_column_feature_selection_data()
            self.set_metadata_column_visible()


    def load_column_feature_selection_data(self):
        columns = self.metadatabase.columns
        try:
            with open(os.path.dirname(os.path.realpath(__file__))+'/settings/column_feature_selection_data.json', 'r') as f:
                column_feature_selected = json.load(f)
                column_loaded = np.array(list(map(list, column_feature_selected)))[:, 1].tolist()
                if columns == column_loaded:
                    self.column_feature_selection = list(map(tuple, column_feature_selected))
                else:
                    self.column_feature_selection = list(zip(len(columns)*[True], columns))
        except Exception:
            print('Unable to load column_feature_selection_data.json, set by default')
            self.column_feature_selection = list(zip(len(columns) * [True], columns))

    def save_column_feature_selection_data(self):
        try:
            with open(os.path.dirname(os.path.realpath(__file__))+'/settings/column_feature_selection_data.json', 'w') as f:
                json.dump(self.column_feature_selection, f)
        except Exception:
            print('Saving column_feature_selection failed')

    def set_metadata_column_visible(self):
        column_feature_selection = self.column_feature_selection
        if column_feature_selection is not None:
            visible_mask = np.array(list(map(list, column_feature_selection)))[:, 0].tolist()
            for i, status in enumerate(visible_mask):
                self.tableViewMetadata.setColumnHidden(i, not str2bool(status))

    def process_parameter_selected(self):
        dlg_parameter_selection = DialogParameterSelection(self)
        spike_sorting_parameter_df = pd.DataFrame(list(self.package.spike_sorting_parameter.items()),
                                                  columns=['Parameter', 'Value'])
        post_curation_parameter_df = pd.DataFrame(list(self.package.post_curation_parameter.items()),
                                                  columns=['Parameter', 'Value'])
        waveform_extraction_parameter_df = pd.DataFrame(list(self.package.waveform_extraction_parameter.items()),
                                                  columns=['Parameter', 'Value'])
        figure_generation_parameter_df = pd.DataFrame(list(self.package.figure_generation_parameter.items()),
                                                  columns=['Parameter', 'Value'])
        dlg_parameter_selection.set_parameter_selection(spike_sorting_parameter_df, post_curation_parameter_df,
                                                        waveform_extraction_parameter_df, figure_generation_parameter_df)
        result = dlg_parameter_selection.exec_()
        if result == QMessageBox.Accepted:
            [new_spike_sorting_parameter_df, new_post_curation_parameter_df, new_waveform_extraction_parameter_df,
             new_figure_generation_parameter_df] = dlg_parameter_selection.get_cparameter_selection()
            new_spike_sorting_parameter = new_spike_sorting_parameter_df.set_index('Parameter').T.to_dict('list')
            self.package.spike_sorting_parameter = {key:value[0] for (key, value) in new_spike_sorting_parameter.items()}
            new_post_curation_parameter = new_post_curation_parameter_df.set_index('Parameter').T.to_dict('list')
            self.package.post_curation_parameter = {key: value[0] for (key, value) in new_post_curation_parameter.items()}
            new_waveform_extraction_parameter = new_waveform_extraction_parameter_df.set_index('Parameter').T.to_dict('list')
            self.package.waveform_extraction_parameter = {key: value[0] for (key, value) in new_waveform_extraction_parameter.items()}
            new_figure_generation_parameter = new_figure_generation_parameter_df.set_index('Parameter').T.to_dict('list')
            self.package.figure_generation_parameter = {key: value[0] for (key, value) in new_figure_generation_parameter.items()}
            self.save_parameter_selection_data()

    def load_parameter_selection_data(self):
        try:
            with open(os.path.dirname(
                    os.path.realpath(__file__)) + '/settings/spike_sorting_parameters_data.json',
                      'r') as f:
                self.package.spike_sorting_parameter = json.load(f)
        except Exception:
            try:
                with open(os.path.dirname(
                        os.path.realpath(__file__)) + '/settings/default_spike_sorting_parameters_data.json',
                          'r') as f:
                    self.package.spike_sorting_parameter = json.load(f)
                print('Unable to read spike_sorting_parameters_data.json, use default')
            except Exception:
                self.package.spike_sorting_parameter = {}
                print('Unable to read any parameter for spike_sorting')
        try:
            with open(os.path.dirname(
                    os.path.realpath(__file__)) + '/settings/post_curation_parameters_data.json',
                      'r') as f:
                self.package.post_curation_parameter = json.load(f)
        except Exception:
            try:
                with open(os.path.dirname(
                        os.path.realpath(__file__)) + '/settings/default_post_curation_parameters_data.json',
                          'r') as f:
                    self.package.post_curation_parameter = json.load(f)
                print('Unable to read post_curation_parameters_data.json, use default')
            except Exception:
                self.package.post_curation_parameter = {}
                print('Unable to read any parameter for post_curation')
        try:
            with open(os.path.dirname(
                    os.path.realpath(__file__)) + '/settings/waveform_extraction_parameters_data.json',
                      'r') as f:
                self.package.waveform_extraction_parameter = json.load(f)
        except Exception:
            try:
                with open(os.path.dirname(
                        os.path.realpath(__file__)) + '/settings/default_waveform_extraction_parameters_data.json',
                          'r') as f:
                    self.package.waveform_extraction_parameter = json.load(f)
                print('Unable to read waveform_extraction_parameters_data.json, use default')
            except Exception:
                self.package.waveform_extraction_parameter = {}
                print('Unable to read any parameter for waveform_extraction')
        try:
            with open(os.path.dirname(
                    os.path.realpath(__file__)) + '/settings/figure_generation_parameters_data.json',
                      'r') as f:
                self.package.figure_generation_parameter = json.load(f)
        except Exception:
            try:
                with open(os.path.dirname(
                        os.path.realpath(__file__)) + '/settings/default_figure_generation_parameters_data.json',
                          'r') as f:
                    self.package.figure_generation_parameter = json.load(f)
                print('Unable to read figure_generation_parameters_data.json, use default')
            except Exception:
                self.package.figure_generation_parameter = {}
                print('Unable to read any parameter for figure_generation')

    def save_parameter_selection_data(self):
        try:
            with open(os.path.dirname(os.path.realpath(__file__))+'/settings/spike_sorting_parameters_data.json', 'w') as f:
                json.dump(self.package.spike_sorting_parameter, f)
        except Exception:
            print('Saving spike_sorting_parameter failed')
        try:
            with open(os.path.dirname(os.path.realpath(__file__))+'/settings/post_curation_parameters_data.json', 'w') as f:
                json.dump(self.package.post_curation_parameter, f)
        except Exception:
            print('Saving post_curation_parameter failed')
        try:
            with open(os.path.dirname(os.path.realpath(__file__))+'/settings/waveform_extraction_parameters_data.json', 'w') as f:
                json.dump(self.package.waveform_extraction_parameter, f)
        except Exception:
            print('Saving waveform_extraction_parameter failed')
        try:
            with open(os.path.dirname(os.path.realpath(__file__))+'/settings/figure_generation_parameters_data.json', 'w') as f:
                json.dump(self.package.figure_generation_parameter, f)
        except Exception:
            print('Saving figure_generation_parameter failed')

    def process_selection_changed(self):
        process_selection = self.process_selection_model.get_data()
        index = self.listViewProcess.selectedIndexes()[0]
        row = index.row()
        status, process_feature = process_selection[row]
        self.process_selection_model.set_row_data((not status, process_feature), row)
        self.process_selection_model.dataChanged.emit(index,index)
        self.process_selection = self.get_process_selection()

    def set_process_selection(self, process_selection):
        self.process_selection_model.set_data(process_selection)
        self.process_selection_model.layoutChanged.emit()

    def get_process_selection(self):
        return self.process_selection_model.get_data()

    def process_safety_selected(self):
        dlg_process_safety_selection = DialogProcessSafety(self)
        dlg_process_safety_selection.set_feature_safety(self.process_safety)
        result = dlg_process_safety_selection.exec_()
        if result == QMessageBox.Accepted:
            self.process_safety = dlg_process_safety_selection.get_feature_safety()


    def initiate_route_views(self):
        self.experimenter_model.set_data(self.data_router.query_experimenter_list())
        self.experimenter_model.layoutChanged.emit()
        self.listViewExperimenter.clearSelection()
        self.system_model.set_data([])
        self.system_model.layoutChanged.emit()
        self.listViewSystem.clearSelection()
        self.animal_id_model.set_data([])
        self.animal_id_model.layoutChanged.emit()
        self.listViewAnimalID.clearSelection()
        self.recording_time_model.set_data([])
        self.recording_time_model.layoutChanged.emit()
        self.listViewRecordingTime.clearSelection()

    def check_process_safety(self, process):
        process_list = np.array(list(map(list, self.process_safety)))[:, 1].tolist()
        assert process in process_list, process + ' is not in ' + process_list + ', debug!'
        status, _ = self.process_safety[process_list.index(process)]
        return status

    def check_process_done(self, process, one_metadata_df):
        if process == "SpikeSorting":
            return (one_metadata_df['SortingSuccess'] is not None) and (one_metadata_df['SortingSuccess'] is not np.nan)
        elif process == "PostCuration":
            return one_metadata_df['PostCurationFinish'] is True
        elif process == "WaveformExtraction":
            return one_metadata_df['WaveformExtraction'] is True
        elif process == "FigureGeneration":
            return one_metadata_df['FigureGeneration'] is True
        else:
            assert False, 'process name: '+process+' could not be understand, debug here!'

    def check_data_state(self, one_metadata_df):
        if one_metadata_df['FigureGeneration'] is True:
            return "completed"
        elif one_metadata_df['WaveformExtraction'] is True:
            return "to_be_figure_generated"
        elif one_metadata_df['PostCurationFinish'] is True:
            return "to_be_waveform_extracted"
        elif one_metadata_df['SortingSuccess'] is True:
            return "to_be_post_curated"
        elif one_metadata_df['SortingSuccess'] is False:
            return "unsuccessfully_sorted"
        elif (one_metadata_df['SortingSuccess'] is None) or (one_metadata_df['SortingSuccess'] is np.nan):
            return "to_be_spike_sorted"
        else:
            assert False, 'A data returns a unexpected state, debug here: '+str(one_metadata_df.tolist())

    def enable_analysis_button(self):
        self.pushButtonRun.setEnabled(True)
        self.pushButtonAutoRun.setEnabled(True)

    def disable_analysis_button(self):
        self.pushButtonRun.setEnabled(False)
        self.pushButtonAutoRun.setEnabled(False)
    '''
    def display_progress_bar(self, value):
        self.progressBar.setValue(value)
    '''

    def update_progress_bar(self):
        self.progressBar.setValue(int(100 * self.package.task_finished_number / self.package.task_total_number))

    def start_thread_house_keeping(self):
        self.disable_analysis_button()
        self.actionProcessSafety.setDisabled(True)
        self.actionProcessParameter.setDisabled(True)
        self.progressBar.setEnabled(True)
        self.progressBar.setValue(0)

    def end_thread_house_keeping(self):
        self.enable_analysis_button()
        self.actionProcessSafety.setDisabled(False)
        self.actionProcessParameter.setDisabled(False)
        self.progressBar.setEnabled(False)
        self.progressBar.setValue(100)

    def house_keeping(self):
        if not self.run_state:
            self.run_state = True
            self.pushButtonRun.setIcon(self.icon_stop)
            self.pushButtonRun.setText('Stop')
            self.pushButtonAutoRun.setIcon(self.icon_stop)
            self.pushButtonAutoRun.setText('Stop')
            self.progressBar.setEnabled(True)
            self.progressBar.setValue(0)
            self.actionProcessSafety.setEnabled(False)
            self.actionProcessParameter.setEnabled(False)
        else:
            self.run_state = False
            self.pushButtonRun.setIcon(self.icon_run)
            self.pushButtonRun.setText('RUN')
            self.pushButtonAutoRun.setIcon(self.icon_run)
            self.pushButtonAutoRun.setText('AutoRun')
            self.progressBar.setEnabled(False)
            self.progressBar.setValue(100)
            self.actionProcessSafety.setEnabled(True)
            self.actionProcessParameter.setEnabled(True)

    def display_thread_error_message(self, tuple_info):
        print('Thread failed, debug!')
        for i in tuple_info:
            print(i)

    def handle_spike_analysis_thread_result(self, failed_task_list):
        print('Analysis Finished')
        failed_number = len(failed_task_list)
        if failed_number == 0:
            print('All tasks succeed.')
        else:
            print(str(failed_number) + ' tasks failed:')
            pprint.pprint(failed_task_list)

    def check_user_permission(self, task_list):
        if self.user_folder_name == "ALLFOLDERS":
            return True
        else:
            for task in task_list:
                [_, data_info] = task
                experimentor = data_info.split(',')[0]
                if not experimentor == self.user_folder_name:
                    return False
            return True

    def run_button_clicked(self):
        if not self.run_state:
            metadata_inds = [self.metadata_proxy_model.mapToSource(idx).row() for idx in self.tableViewMetadata.selectionModel().selectedRows()]
            metadata_selected = self.metadata_model.get_data().iloc[metadata_inds, :]
            if metadata_selected.empty:
                print('Please select data on metadata window before running')
                return False
            process_selected = [process for status, process in self.process_selection if status]
            if not process_selected:
                print('Please select spike analyzing process on process window before running')
                return False
            task_list = []
            for process in process_selected:
                for row in range(metadata_selected.shape[0]):
                    one_metadata_df = metadata_selected.iloc[row, :]
                    data_info = one_metadata_df[['Experimenter', 'System', 'AnimalID', 'RecordingTime']].tolist()
                    if self.check_process_safety(process):
                        if self.check_process_done(process, one_metadata_df):
                            print(','.join(data_info)+' has already done '+process+', skipped.')
                        else:
                            task_list.append([process, ','.join(data_info)])
                    else:
                        task_list.append([process, ','.join(data_info)])
            if len(task_list) > 0:
                if self.check_user_permission(task_list):
                    self.package.task_finished_number = 0
                    self.package.task_total_number = len(task_list)
                    [tasks_to_server, tasks_to_wait, tasks_to_queue] = task_separation(task_list)
                    self.package.task_wait_list = tasks_to_wait
                    self.package.task_queue = tasks_to_queue
                    self.package.task_to_server_list = tasks_to_server
                    self.package.server_working = True
                    self.package.client_working = True
                    self.package.thread_ending_display_flag = False
                    self.package.start_timer_signal.emit()
                    self.house_keeping()
                    listen_worker = Worker(listen_tasks_from_server, self.package)
                    listen_worker.signals.error.connect(self.display_thread_error_message)
                    send_worker = Worker(send_tasks_to_server, self.package)
                    send_worker.signals.error.connect(self.display_thread_error_message)
                    post_curate_worker = Worker(do_tasks_on_client, self.package)
                    post_curate_worker.signals.error.connect(self.display_thread_error_message)
                    post_curate_worker.signals.finished.connect(self.house_keeping)
                    self.threadpool.start(listen_worker)
                    self.threadpool.start(send_worker)
                    self.threadpool.start(post_curate_worker)
                else:
                    print('You could only run your own data, please reselect data.')
            else:
                print('No further analysis could be done on selected data')
        else:
            print('Terminate Processes')
            try:
                server_addr = (self.package.server_ip, self.package.port)
                client_sock = MySocket()
                client_sock.connect(server_addr)
                client_envelope = Envelope('TerminationRequest', {'UserName': self.package.user_name})
                client_sock.send(pack(client_envelope))
                client_sock.close()
            except Exception:
                pass
            if self.package.task_queue is not None:
                for task in self.package.task_queue:
                    print('Terminated: ' + task[0] + ' ' + task[1])
                    print('Queue abandoned.')
            if self.package.task_wait_list is not None:
                for task in self.package.task_wait_list:
                    print('Terminated: ' + task[0] + ' ' + task[1])
                    print('Waiting list abandoned.')
            if self.package.task_to_server_list is not None:
                for task in self.package.task_to_server_list:
                    print('Terminated: ' + task[0] + ' ' + task[1])
                    print('Waiting sending to server list abandoned.')
            self.package.task_queue = []
            self.package.task_wait_list = []
            self.package.task_to_server_list = []
            if self.package.worker_pid is not None:
                kill_process_tree(self.package.worker_pid)
            self.package.server_working = False
            self.package.client_working = False
            self.package.stop_timer_signal.emit()
            try:
                client_addr = (self.package.client_ip, self.package.client_port)
                client_sock = MySocket()
                client_sock.connect(client_addr)
                client_envelope = Envelope('ServerTimeout', {'text': 'just to activate the next loop check'})
                client_sock.send(pack(client_envelope))
                client_sock.close()
            except Exception:
                pass




    def auto_run_button_clicked(self):
        if not self.run_state:
            metadata_inds = [self.metadata_proxy_model.mapToSource(idx).row() for idx in
                             self.tableViewMetadata.selectionModel().selectedRows()]
            metadata_selected = self.metadata_model.get_data().iloc[metadata_inds, :]
            if metadata_selected.empty:
                print('Please select data on metadata window before running')
                return False
            metadata_selected_state = metadata_selected.apply(self.check_data_state, axis=1)
            metadata_after_post_curation = metadata_selected.loc[
                np.array(metadata_selected_state == "to_be_figure_generated") | np.array(
                    metadata_selected_state == "to_be_waveform_extracted")]
            process_selected_after_post_curation = ['WaveformExtraction', 'FigureGeneration']
            metadata_before_post_curation = metadata_selected.loc[
                np.array(metadata_selected_state == "to_be_post_curated") | np.array(
                    metadata_selected_state == "to_be_spike_sorted")]
            process_selected_before_post_curation = ['SpikeSorting', 'PostCuration', 'WaveformExtraction', 'FigureGeneration']
            task_list = []
            # first finish processing data which has already done post curation
            for process in process_selected_after_post_curation:
                for row in range(metadata_after_post_curation.shape[0]):
                    one_metadata_df = metadata_after_post_curation.iloc[row, :]
                    data_info = one_metadata_df[['Experimenter', 'System', 'AnimalID', 'RecordingTime']].tolist()
                    if self.check_process_done(process, one_metadata_df):
                        print(','.join(data_info)+' has already done '+process+', skipped.')
                    else:
                        task_list.append([process, ','.join(data_info)])
            # second finish processing data which has not done post curation yet
            for process in process_selected_before_post_curation:
                for row in range(metadata_before_post_curation.shape[0]):
                    one_metadata_df = metadata_before_post_curation.iloc[row, :]
                    data_info = one_metadata_df[['Experimenter', 'System', 'AnimalID', 'RecordingTime']].tolist()
                    if self.check_process_done(process, one_metadata_df):
                        print(','.join(data_info)+' has already done '+process+', skipped.')
                    else:
                        task_list.append([process, ','.join(data_info)])
            if len(task_list) > 0:
                if self.check_user_permission(task_list):
                    self.package.task_finished_number = 0
                    self.package.task_total_number = len(task_list)
                    [tasks_to_server, tasks_to_wait, tasks_to_queue] = task_separation(task_list)
                    self.package.task_wait_list = tasks_to_wait
                    self.package.task_queue = tasks_to_queue
                    self.package.task_to_server_list = tasks_to_server
                    self.package.server_working = True
                    self.package.client_working = True
                    self.package.thread_ending_display_flag = False
                    self.package.start_timer_signal.emit()
                    self.house_keeping()
                    listen_worker = Worker(listen_tasks_from_server, self.package)
                    listen_worker.signals.error.connect(self.display_thread_error_message)
                    send_worker = Worker(send_tasks_to_server, self.package)
                    send_worker.signals.error.connect(self.display_thread_error_message)
                    post_curate_worker = Worker(do_tasks_on_client, self.package)
                    post_curate_worker.signals.error.connect(self.display_thread_error_message)
                    post_curate_worker.signals.finished.connect(self.house_keeping)
                    self.threadpool.start(listen_worker)
                    self.threadpool.start(send_worker)
                    self.threadpool.start(post_curate_worker)
                else:
                    print('You could only run your own data, please reselect data.')
            else:
                print('No further analysis could be done on selected data')
        else:
            print('Terminate Processes')
            try:
                server_addr = (self.package.server_ip, self.package.port)
                client_sock = MySocket()
                client_sock.connect(server_addr)
                client_envelope = Envelope('TerminationRequest', {'UserName': self.package.user_name})
                client_sock.send(pack(client_envelope))
                client_sock.close()
            except Exception:
                pass
            if self.package.task_queue is not None:
                for task in self.package.task_queue:
                    print('Terminated: ' + task[0] + ' ' + task[1])
                    print('Queue abandoned.')
            if self.package.task_wait_list is not None:
                for task in self.package.task_wait_list:
                    print('Terminated: ' + task[0] + ' ' + task[1])
                    print('Waiting list abandoned.')
            if self.package.task_to_server_list is not None:
                for task in self.package.task_to_server_list:
                    print('Terminated: ' + task[0] + ' ' + task[1])
                    print('Waiting sending to server list abandoned.')
            self.package.task_queue = []
            self.package.task_wait_list = []
            self.package.task_to_server_list = []
            if self.package.worker_pid is not None:
                kill_process_tree(self.package.worker_pid)
            self.package.server_working = False
            self.package.client_working = False
            self.package.stop_timer_signal.emit()
            try:
                client_addr = (self.package.client_ip, self.package.client_port)
                client_sock = MySocket()
                client_sock.connect(client_addr)
                client_envelope = Envelope('ServerTimeout', {'text': 'just to activate the next loop check'})
                client_sock.send(pack(client_envelope))
                client_sock.close()
            except Exception:
                pass



    def server_time_out(self):
        if not self.package.client_working:
            print('Server is not responding.')
            self.package.server_working = False
            for task in self.package.task_wait_list:
                print('Failed: ' + task[0] + ' ' + task[1])
                print('Waiting list abandoned because server is not responding.')
            for task in self.package.task_to_server_list:
                print('Failed: ' + task[0] + ' ' + task[1])
                print('Waiting sending to server list abandoned because server is not responding.')
            self.package.task_wait_list = []
            self.package.task_to_server_list = []
            self.package.stop_timer_signal.emit()
            try:
                client_addr = (self.package.client_ip, self.package.client_port)
                client_sock = MySocket()
                client_sock.connect(client_addr)
                client_envelope = Envelope('ServerTimeout', {'text': 'just to activate the next loop check'})
                client_sock.send(pack(client_envelope))
                client_sock.close()
            except Exception:
                print('Error in server_time_out, debug here!')
        else:
            self.package.start_timer_signal.emit()

    def start_timer(self):
        self.server_timer.start(self.wait_for_server_time)

    def stop_timer(self):
        self.server_timer.stop()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        try:
            if self.package.task_queue is not None:
                for task in self.package.task_queue:
                    print('Terminated: ' + task[0] + ' ' + task[1])
                    print('Queue abandoned.')
            if self.package.task_wait_list is not None:
                for task in self.package.task_wait_list:
                    print('Terminated: ' + task[0] + ' ' + task[1])
                    print('Waiting list abandoned.')
            if self.package.task_to_server_list is not None:
                for task in self.package.task_to_server_list:
                    print('Terminated: ' + task[0] + ' ' + task[1])
                    print('Waiting sending to server list abandoned.')
            self.package.task_queue = []
            self.package.task_wait_list = []
            self.package.task_to_server_list = []
            if self.package.worker_pid is not None:
                kill_process_tree(self.package.worker_pid)
            self.package.server_working = False
            self.package.client_working = False
            self.package.stop_timer_signal.emit()
            try:
                client_addr = (self.package.client_ip, self.package.client_port)
                client_sock = MySocket()
                client_sock.connect(client_addr)
                client_envelope = Envelope('ServerTimeout', {'text': 'just to activate the next loop check'})
                client_sock.send(pack(client_envelope))
                client_sock.close()
            except Exception:
                pass
        except Exception as e:
            traceback.print_exc()
            print(e)






















