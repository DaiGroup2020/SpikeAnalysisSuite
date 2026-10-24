import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from .DialogParameterSelectionScheme import Ui_DialogSpikeAnalysisParameter
from .DataModelBank import ParameterSelectionModel
import json
import os

class DialogParameterSelection(QtWidgets.QDialog, Ui_DialogSpikeAnalysisParameter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.tableViewSpikeSorting.verticalHeader().setVisible(False)
        self.tableViewPostCuratoin.verticalHeader().setVisible(False)
        self.tableViewWaveformExtraction.verticalHeader().setVisible(False)
        self.tableViewFigureGeneration.verticalHeader().setVisible(False)

        self.spike_sorting_model = ParameterSelectionModel()
        self.tableViewSpikeSorting.setModel(self.spike_sorting_model)
        self.post_curation_model = ParameterSelectionModel()
        self.tableViewPostCuratoin.setModel(self.post_curation_model)
        self.waveform_extraction_model = ParameterSelectionModel()
        self.tableViewWaveformExtraction.setModel(self.waveform_extraction_model)
        self.figure_generation_model = ParameterSelectionModel()
        self.tableViewFigureGeneration.setModel(self.figure_generation_model)

        self.pushButtonSpikeSorting.clicked.connect(self.spike_sorting_reset_button_clicked)
        self.pushButtonPostCuratoin.clicked.connect(self.post_curation_reset_button_clicked)
        self.pushButtonWaveformExtraction.clicked.connect(self.waveform_extraction_reset_button_clicked)
        self.pushButtonFigureGeneration.clicked.connect(self.figure_generation_reset_button_clicked)

    def set_parameter_selection(self, spike_sorting_parameter, post_curation_parameter,
                                waveform_extraction_parameter, figure_generation_parameter):
        self.spike_sorting_model.set_data(spike_sorting_parameter)
        self.post_curation_model.set_data(post_curation_parameter)
        self.waveform_extraction_model.set_data(waveform_extraction_parameter)
        self.figure_generation_model.set_data(figure_generation_parameter)
        self.spike_sorting_model.layoutChanged.emit()
        self.post_curation_model.layoutChanged.emit()
        self.waveform_extraction_model.layoutChanged.emit()
        self.figure_generation_model.layoutChanged.emit()

    def get_cparameter_selection(self):
        return [self.spike_sorting_model.get_data(), self.post_curation_model.get_data(),
                self.waveform_extraction_model.get_data(), self.figure_generation_model.get_data()]

    def spike_sorting_reset_button_clicked(self):
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/settings/default_spike_sorting_parameters_data.json',
                      'r') as f:
                default_spike_sorting_parameter = json.load(f)
                self.spike_sorting_model.set_data(pd.DataFrame(list(default_spike_sorting_parameter.items()), columns=['Parameter', 'Value']))
                self.spike_sorting_model.layoutChanged.emit()
        except Exception:
            print('reset failed unable to read default_spike_sorting_parameters_data.json as a dictionary')

    def post_curation_reset_button_clicked(self):
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/settings/default_post_curation_parameters_data.json',
                      'r') as f:
                default_post_curation_parameter = json.load(f)
                self.post_curation_model.set_data(pd.DataFrame(list(default_post_curation_parameter.items()), columns=['Parameter', 'Value']))
                self.post_curation_model.layoutChanged.emit()
        except Exception:
            print('reset failed unable to read default_post_curation_parameters_data.json as a dictionary')

    def waveform_extraction_reset_button_clicked(self):
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/settings/default_waveform_extraction_parameters_data.json',
                      'r') as f:
                default_waveform_extraction_parameter = json.load(f)
                self.waveform_extraction_model.set_data(pd.DataFrame(list(default_waveform_extraction_parameter.items()), columns=['Parameter', 'Value']))
                self.waveform_extraction_model.layoutChanged.emit()
        except Exception:
            print('reset failed unable to read default_waveform_extraction_parameters_data.json as a dictionary')

    def figure_generation_reset_button_clicked(self):
        try:
            with open(os.path.dirname(os.path.realpath(__file__)) + '/settings/default_figure_generation_parameters_data.json',
                      'r') as f:
                default_figure_generation_parameter = json.load(f)
                self.figure_generation_model.set_data(pd.DataFrame(list(default_figure_generation_parameter.items()), columns=['Parameter', 'Value']))
                self.figure_generation_model.layoutChanged.emit()
        except Exception:
            print('reset failed unable to read default_figure_generation_parameters_data.json as a dictionary')

