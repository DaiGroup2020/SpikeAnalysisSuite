import traceback

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import threading
import sys

class ServerSignal(QObject):
    progress = pyqtSignal(int)
    result = pyqtSignal(object)
    error = pyqtSignal(tuple)
    finished = pyqtSignal()

class ServerThread(threading.Thread):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = ServerSignal()

    @pyqtSlot()
    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            print(e)
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class ServerPackage(QObject):
    root = None
    server_ip = None
    port = None
    client_port = None
    user_info = None
    task_manager_update_signal = pyqtSignal(list)
    task_manager_clear_signal = pyqtSignal(str)
    lock = threading.Lock()

    process_data_parameter_queue_dict = None
    task_reply_buffer_dict = None
    client_ip_dict = None
    current_user_list = None
    pid_dict = None
    run_stop_set = None
