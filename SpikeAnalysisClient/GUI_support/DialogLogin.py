from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThreadPool
from .DialogLoginScheme import Ui_DialogLogin
from .utils.ThreadUtils import Worker
from .utils.NetworkUtils import pack, unpack, Envelope, MySocket
from .utils.FunctionUtils import get_host_ip
import os
import json

class DialogLogin(QtWidgets.QDialog, Ui_DialogLogin):
    def __init__(self, server_ip, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.server_ip = server_ip
        self.port = 1113
        self.client_ip = get_host_ip()
        self.client_port = 2113
        self.confirmed_user_folder_name = None
        self.confirmed_user_name = None
        self.load_info()
        self.buttonBoxLogin.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.reset)
        self.labelError.setStyleSheet("color: Red")
        self.threadpool = QThreadPool()

    def reset(self):
        self.lineEditUserName.clear()
        self.lineEditPassword.clear()

    def load_info(self):
        try:
            with open(os.path.dirname(
                    os.path.realpath(__file__)) + '/settings/user_info_data.json',
                      'r') as f:
                user_info_dict = json.load(f)
                self.lineEditUserName.setText(user_info_dict['UserName'])
                self.lineEditPassword.setText(user_info_dict['Password'])
                self.checkBoxSaveInfo.setChecked(True)
        except Exception:
            self.checkBoxSaveInfo.setChecked(False)

    def save_info(self):
        try:
            with open(os.path.dirname(os.path.realpath(__file__))+'/settings/user_info_data.json', 'w') as f:
                user_info_dict = {'UserName':self.lineEditUserName.text(), 'Password':self.lineEditPassword.text()}
                json.dump(user_info_dict, f)
        except Exception:
            print('Saving failed.')

    def remove_info(self):
        try:
            os.remove(os.path.dirname(os.path.realpath(__file__))+'/settings/user_info_data.json')
        except Exception:
            print('Deleting user info failed.')


    def validate_from_server(self, **kwargs):
        try:
            server_addr = (self.server_ip, self.port)
            client_addr = (self.client_ip, self.client_port)
            client = MySocket()
            client.bind(client_addr)
            client.settimeout(10)
            client.listen(1)
            client_sock = MySocket()
            client_sock.connect(server_addr)
            client_envelope = Envelope('LoginRequest', {'UserName': self.lineEditUserName.text(),
                                                        'Password': self.lineEditPassword.text()})
            client_sock.send(pack(client_envelope))
            client_sock.close()
            server_sock, _ = client.accept()
            server_envelope = unpack(server_sock.receive())
            server_sock.close()
            if server_envelope.get_title() == 'LoginReply':
                validate = server_envelope.get_message()['Validate']
                user_folder_name = server_envelope.get_message()['UserFolderName']
                return [validate, user_folder_name]
            else:
                return ['ConnectionFailed', None]
        except Exception:
            return ['ConnectionFailed', None]

    def start_thread_house_keeping(self):
        self.buttonBoxLogin.setDisabled(True)
        self.lineEditUserName.setDisabled(True)
        self.lineEditPassword.setDisabled(True)
        self.checkBoxSaveInfo.setDisabled(True)

    def end_thread_house_keeping(self):
        self.buttonBoxLogin.setDisabled(False)
        self.lineEditUserName.setDisabled(False)
        self.lineEditPassword.setDisabled(False)
        self.checkBoxSaveInfo.setDisabled(False)


    def handle_thread_error(self, tuple_info):
        print('Thread failed, debug!')
        for i in tuple_info:
            print(i)

    def handle_thread_result(self, result):
        [validate, user_folder_name] = result
        if validate == 'UserNotFound':
            self.labelError.setText('User Name not Found')
        elif validate == 'Unmatch':
            self.labelError.setText('User Name not Match with Password')
        elif validate == 'ConnectionFailed':
            self.labelError.setText('Could not Connect to Server, Try Again')
        elif validate == 'Success':
            self.confirmed_user_name = self.lineEditUserName.text()
            self.confirmed_user_folder_name = user_folder_name
            super().accept()
        else:
            print('Unknown validate, debug here!')



    def accept(self) -> None:
        self.start_thread_house_keeping()
        if self.checkBoxSaveInfo.checkState():
            self.save_info()
        else:
            self.remove_info()
        worker = Worker(self.validate_from_server)
        worker.signals.finished.connect(self.end_thread_house_keeping)
        worker.signals.error.connect(self.handle_thread_error)
        worker.signals.result.connect(self.handle_thread_result)
        self.threadpool.start(worker)

