import os
import glob
import re
import pandas as pd
import numpy as np
from .SpikeAnalysisCore.module_bank import read_sorting_metadata

def dir_split(path):
    return re.split(r'[/\\]', path)[:-1]



class DataRouter(object):
    def __init__(self, root=''):
        self.set_root(root)
        self.experimenter_path_df = None
        self.system_path_df = None
        self.animal_id_path_df = None
        self.recording_time_path_df = None


    def set_root(self, root):
        if not root.endswith('/'):
            root = root + '/'
        else:
            root = root
        if os.path.isdir(root):
            self.root = root
            self.root_depth = len(dir_split(self.root))
        else:
            self.root = None
            self.root_depth = None
            print(root, ' is not a exist path for a folder. Root set to None.')

    def get_root(self):
        return self.root

    def route(self):
        if self.root is not None:
            self.recording_time_path_df = pd.DataFrame(map(dir_split, glob.glob(self.root+4*'*/')))
            self.recording_time_path_df = self.recording_time_path_df.loc[~self.recording_time_path_df.iloc[:, -4].isin(['#recycle'])]
            self.recording_time_path_df = self.recording_time_path_df.sort_values(self.recording_time_path_df.columns[-1])
            self.animal_id_path_df = self.recording_time_path_df.drop(self.recording_time_path_df.columns[-1],axis=1).drop_duplicates()
            self.animal_id_path_df = self.animal_id_path_df.iloc[np.argsort(self.animal_id_path_df.iloc[:, -1].astype(int)), :]
            # self.animal_id_path_df = self.animal_id_path_df.sort_values(self.animal_id_path_df.columns[-1])
            self.system_path_df = self.animal_id_path_df.drop(self.animal_id_path_df.columns[-1],
                                                                      axis=1).drop_duplicates()
            self.system_path_df = self.system_path_df.sort_values(self.system_path_df.columns[-1])
            self.experimenter_path_df = self.system_path_df.drop(self.system_path_df.columns[-1],
                                                                      axis=1).drop_duplicates()
            self.experimenter_path_df = self.experimenter_path_df.sort_values(self.experimenter_path_df.columns[-1])
        else:
            self.experimenter_path_df = None
            self.system_path_df = None
            self.animal_id_path_df = None
            self.recording_time_path_df = None

    def query_experimenter_list(self):
        experimenter_list = self.experimenter_path_df.iloc[:, -1].values
        return experimenter_list

    def query_system_list(self, experimenter_list):
        filtered_system_path_df = self.system_path_df.loc[self.system_path_df.iloc[:, -2].isin(experimenter_list)]
        system_list = filtered_system_path_df.iloc[:, -1].drop_duplicates().values
        return system_list

    def query_animal_id_list(self, experimenter_list, system_list):
        filtered_animal_id_path_df = self.animal_id_path_df.loc[
            self.animal_id_path_df.iloc[:, -3].isin(experimenter_list) & self.animal_id_path_df.iloc[:, -2].isin(
                system_list)]
        animal_id_list = filtered_animal_id_path_df.iloc[:, -1].drop_duplicates().values
        return animal_id_list

    def query_recording_time_list(self, experimenter_list, system_list, animal_id_list):
        filtered_recording_time_path_df = self.recording_time_path_df.loc[
            self.recording_time_path_df.iloc[:, -4].isin(experimenter_list) & self.recording_time_path_df.iloc[:,
                                                                              -3].isin(
                system_list) & self.recording_time_path_df.iloc[:, -2].isin(animal_id_list)]
        recording_time_list = filtered_recording_time_path_df.iloc[:, -1].drop_duplicates().values
        return recording_time_list

    def get_selected_dataset(self, experimenter_list, system_list, animal_id_list, recording_time_list):
        filtered_recording_time_path_df = self.recording_time_path_df.loc[
            self.recording_time_path_df.iloc[:, -4].isin(experimenter_list) & self.recording_time_path_df.iloc[:,
                                                                              -3].isin(
                system_list) & self.recording_time_path_df.iloc[:, -2].isin(
                animal_id_list) & self.recording_time_path_df.iloc[:, -1].isin(recording_time_list)]
        selected_dataset = filtered_recording_time_path_df.iloc[:, -4:]
        selected_dataset.columns = ['Experimenter', 'System', 'AnimalID', 'RecordingTime']
        selected_dataset = selected_dataset.reset_index(drop=True)
        return selected_dataset

class MetaDataBase(object):
    def __init__(self, root=''):
        self.set_root(root)
        self.columns = ['Experimenter', 'System', 'AnimalID', 'RecordingTime',
                                                                   'SortingSuccess', 'PostCurationFinish', 'WaveformExtraction',
                                                                   'FigureGeneration', 'ImpedanceThreshold', 'AllChannel',
                                                                   'BadChannel', 'Sorter', 'GoodUnit', 'TemplateFigure', 'PositionFigure',
                                                                   'ISIFigure', 'CorrelationFigure']
        self.metadata_df = None

    def set_root(self, root):
        if not root.endswith('/'):
            root = root + '/'
        else:
            root = root
        if os.path.isdir(root):
            self.root = root
            self.root_depth = len(dir_split(self.root))
        else:
            self.root = None
            self.root_depth = None
            print(root, ' is not a exist path for a folder. Root set to None.')

    def get_root(self):
        return self.root

    def search_metadata(self, selected_dataset):
        selected_dataset = selected_dataset.astype(str)
        [nrow, ncol] = selected_dataset.shape
        metadata_df = pd.DataFrame([], index=range(nrow), columns=self.columns)
        metadata_df[['Experimenter', 'System', 'AnimalID', 'RecordingTime']] = selected_dataset[['Experimenter', 'System', 'AnimalID', 'RecordingTime']]
        for row in range(nrow):
            data_info = selected_dataset.iloc[row, :]
            metadata_dict = read_sorting_metadata(self.root, data_info['Experimenter'], data_info['System'],
                                                  data_info['AnimalID'], data_info['RecordingTime'], display=False)
            if metadata_dict is not None:
                if 'sorting_success' in metadata_dict.keys():
                    metadata_df.at[row, 'SortingSuccess'] = metadata_dict['sorting_success']
                if 'post_curation_accomplished' in metadata_dict.keys():
                    metadata_df.at[row, 'PostCurationFinish'] = metadata_dict['post_curation_accomplished']
                if 'waveform_extraction_accomplished' in metadata_dict.keys():
                    metadata_df.at[row, 'WaveformExtraction'] = metadata_dict['waveform_extraction_accomplished']
                if 'single_recording_figure_generation_accomplished' in metadata_dict.keys():
                    metadata_df.at[row, 'FigureGeneration'] = metadata_dict['single_recording_figure_generation_accomplished']
                if 'impedance_threshold' in metadata_dict.keys():
                    metadata_df.at[row, 'ImpedanceThreshold'] = metadata_dict['impedance_threshold']
                if 'impedance' in metadata_dict.keys():
                    metadata_df.at[row, 'AllChannel'] = len(metadata_dict['impedance'])
                if 'bad_channel_number' in metadata_dict.keys():
                    metadata_df.at[row, 'BadChannel'] = metadata_dict['bad_channel_number']
                if 'sorter' in metadata_dict.keys():
                    metadata_df.at[row, 'Sorter'] = metadata_dict['sorter']
                if 'good_unit_number' in metadata_dict.keys():
                    metadata_df.at[row, 'GoodUnit'] = metadata_dict['good_unit_number']
                if 'single_recording_template_layout' in metadata_dict.keys():
                    metadata_df.at[row, 'TemplateFigure'] = metadata_dict['single_recording_template_layout']
                if 'single_recording_unit_position' in metadata_dict.keys():
                    metadata_df.at[row, 'PositionFigure'] = metadata_dict['single_recording_unit_position']
                if 'single_recording_isi' in metadata_dict.keys():
                    metadata_df.at[row, 'ISIFigure'] = metadata_dict['single_recording_isi']
                if 'single_recording_cross_correlation' in metadata_dict.keys():
                    metadata_df.at[row, 'CorrelationFigure'] = metadata_dict['single_recording_cross_correlation']

        self.metadata_df = metadata_df

    def get_metadata_df(self):
        return self.metadata_df











