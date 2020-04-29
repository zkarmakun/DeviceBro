import socket
import sys
import os
from win10toast import ToastNotifier
from PySide2 import QtWidgets, QtCore, QtGui
import WinSocket
import ctypes
import numpy
import pickle
import cv2
import WinSocket

def toast_connection(client):
    toaster = ToastNotifier()
    toaster.show_toast("New device connected",
                    "client description",
                    icon_path=None,
                    duration=5,
                    threaded=True)
                    

def toast_welcomer():
    toaster = ToastNotifier()
    toaster.show_toast("Staring Py Win Controller",
                    "have fun!!!!",
                    icon_path=None,
                    duration=5,
                    threaded=True)   

def get_resource_path():
    return os.path.dirname(os.path.realpath(__file__)).replace('\\',  '/') 

def get_save_path():
    path = get_resource_path() + "/Saved/"
    if not os.path.exists(path):
        os.mkdir(path)
    
    return path + "save.bro"

class ImageDescription(object):

    def __init__(self, data, width, height, stride):
        self.data = data
        self.width = width
        self.height = height
        self.stride = stride

def get_image_bytes(file_path, desired_size = None):
    img = cv2.imread(file_path)

    if desired_size:
        img = cv2.resize(img, desired_size)
        print("resize icon: " + file_path)

    cc = img.shape[1] * img.shape[2]
    return ImageDescription(img.data.tobytes(), img.shape[1], img.shape[0], cc )

    #return cv2.imencode('.bmp', output)[1]

class DeviceSaveObject(object):

    def __init__(self):
        self.devices = []


def save_options(obj, file_path):
    pickle.dump(obj, open(file_path, "wb"))
    print("save binary: " + file_path)

def load_options(file_path):
    if os.path.exists(file_path):
        return pickle.load(open(file_path, "rb"))
    return DeviceSaveObject()

class DeviceDescription(object):

    def __init__(self, name = "", ip = "127.0.0.1", icon_data = ""):
        self.name = name    
        self.ip = ip
        self.image = icon_data # image description

    def get_icon(self):
        image_profile = QtGui.QImage(self.image.data, self.image.width, self.image.height, self.image.stride, QtGui.QImage.Format_BGR888)
        picture = QtGui.QPixmap(image_profile)
        return QtGui.QIcon(picture)

class DeviceBro(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(DeviceBro, self).__init__(parent)

        self.setWindowTitle('Device Bro')
        self.resize(260,300)

        #remove minimize and max buttons
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint)
        
        #set icon
        self.setWindowIcon(QtGui.QIcon(self._get_icon()))
        self._setup()
        self._setup_tray_app()
        self.icon_size = (100,100)

        self.save = load_options(get_save_path())
        self.update_devices_list()
        self.awaker = WinSocket.CommAwaker()


    def _setup_tray_app(self):
        tray_icon = QtWidgets.QSystemTrayIcon(self)
        tray_icon.setIcon(QtGui.QIcon(self._get_icon())) 
        tray_icon.setToolTip('cool python communication')

        tray_menu = QtWidgets.QMenu(self)
        tray_menu.addAction('Open Options', self.show)
        tray_menu.addSeparator()
        tray_menu.addAction(QtWidgets.QAction('Quit', self, triggered=self._close))
        tray_icon.setContextMenu(tray_menu)
        tray_icon.show()

    def _get_icon(self):
        return get_resource_path() + "/icon_on.png"

    def _close(self):
        self.awaker.close_connection()
        QtWidgets.QApplication.instance().quit()

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def update_devices_list(self):
        for i in range(self.body_layout.count()): 
            self.body_layout.itemAt(i).widget().close()

        for device in self.save.devices:
            button = QtWidgets.QPushButton("")
            button.setFixedSize(70,70)
            icon = device.get_icon()
            button.setIconSize(QtCore.QSize(self.icon_size[0],self.icon_size[0]))
            button.setIcon(icon)
            self.body_layout.addWidget(button)

    def _setup(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)

        #workspaces options
        gb_header = QtWidgets.QGroupBox("Device brothers")
        self.main_layout.addWidget(gb_header)

        header_layout = QtWidgets.QHBoxLayout()
        gb_header.setLayout(header_layout)

        self.btn_register = QtWidgets.QPushButton("+ device")
        self.btn_register.clicked.connect(self._on_process_register)
        header_layout.addWidget(self.btn_register)

        self.tb_ip_adress = QtWidgets.QLineEdit('127.0.0.1')
        header_layout.addWidget(self.tb_ip_adress)

        gb_body = QtWidgets.QGroupBox("")
        self.main_layout.addWidget(gb_body)

        self.body_layout = QtWidgets.QGridLayout()
        gb_body.setLayout(self.body_layout)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.body_layout.addWidget(self.scroll)


        self.setLayout(self.main_layout)

    def _on_process_register(self):
        selected_file = QtWidgets.QFileDialog.getOpenFileName(self, "Select Icon", get_resource_path(), filter="Image Files (*.png *.jpg *.bmp)")
        if selected_file[0]:
            name = self.tb_ip_adress.text().replace(".","")
            img_data = get_image_bytes(selected_file[0], self.icon_size)
            new_device = DeviceDescription(name, self.tb_ip_adress.text(), img_data)
            self.save.devices.append(new_device)
            save_options(self.save, get_save_path())
            self.update_devices_list()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = DeviceBro()
    widget.show()
    sys.exit(app.exec_())