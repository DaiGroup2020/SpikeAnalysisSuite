import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from GUI_support.SpikeAnalysisServerController import SpikeAnalysisServer
from GUI_support.utils.FunctionUtils import get_host_ip

if __name__ == '__main__':
    server_ip = get_host_ip()
    print('server ip is: ', server_ip)
    app = QtWidgets.QApplication(sys.argv)
    window = SpikeAnalysisServer(server_ip)
    window.show()
    app.exec_()
