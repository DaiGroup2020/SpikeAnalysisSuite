import traceback

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot
import sys


class WorkerSignals(QObject):
    progress = pyqtSignal(int)
    result = pyqtSignal(object)
    error = pyqtSignal(tuple)
    finished = pyqtSignal()


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class WorkerPackage(QObject):
    user_name = None
    spike_sorting_parameter = None
    post_curation_parameter = None
    waveform_extraction_parameter = None
    figure_generation_parameter = None
    client_ip = None
    client_port = None
    server_ip = None
    port = None
    root = None
    stop_timer_signal = pyqtSignal()
    start_timer_signal = pyqtSignal()
    update_progress_bar_signal = pyqtSignal()
    worker_pid = None
    server_working = None
    client_working = None
    task_finished_number = None
    task_total_number = None
    task_to_server_list = None
    task_wait_list = None
    task_queue = None
    thread_ending_display_flag = None



