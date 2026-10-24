import sys
import os
from PyQt5 import QtCore, QtWidgets, QtGui
from GUI_support.SpikeAnalysisController import MainWindow
from GUI_support.DialogLogin import DialogLogin

if __name__ == '__main__':

    server_ip = os.environ.get('SPIKE_SERVER_HOST', '127.0.0.1')
    app = QtWidgets.QApplication(sys.argv)
    dialog_login = DialogLogin(server_ip)
    dialog_login.show()
    if dialog_login.exec_() == QtWidgets.QMessageBox.Accepted:
        user_name = dialog_login.confirmed_user_name
        user_folder_name = dialog_login.confirmed_user_folder_name
        window = MainWindow(server_ip, user_name, user_folder_name)
        window.show()
        app.exec_()
