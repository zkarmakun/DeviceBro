import socket
import sys
import os
from PySide2 import QtWidgets, QtCore, QtGui
import time
import struct

import threading
import uuid

from _pydev_bundle import pydev_monkey_qt
pydev_monkey_qt.patch_qt('auto')


PORT = 8080
win = 0

def recv_all(socket, n):
    data = bytearray()
    while len(data) < n:
        packet = None
        try:
            packet = socket.recv(n-len(data))
        except:
            break
        data.extend(packet)

    return data

def recv_message(socket):
    raw_len = recv_all(socket, 4)
    if not raw_len:
        return None
        
    msg_len = int.from_bytes(raw_len, byteorder="little")
    return recv_all(socket, msg_len)

def send_message(socket, message):
    msg_bytes = bytearray(len(message).to_bytes(4, byteorder="little"))
    msg_bytes.extend(message.encode())
    try:
        socket.send(msg_bytes)
        return True
    except:
        print("error sending message")
    return False

def pong(socket):
    msg = "hello world"
    msg_bytes = bytearray(len(msg).to_bytes(4, byteorder="little"))
    msg_bytes.extend(msg.encode())
    try:
        socket.send(msg_bytes)
    except:
        print("pong error?")

def get_local_ip_address():
    return socket.gethostbyname(socket.gethostname())

class CommClient(QtCore.QThread):

    on_message = QtCore.Signal(object, object, object) #return addr, id, data
    on_connection_lost = QtCore.Signal(object, object) #return addr, id
    on_connection_stablished = QtCore.Signal() #return server

    def __init__(self, newsocket = None, address = None, id = None, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.socket = newsocket
        self.addr = address
        self.id = id
        self._exiting = False

    def start_connection(self, ip_address):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip_address, PORT))
        if self.socket:
            self.addr = (ip_address, PORT)
            self.id = uuid.uuid1()
            self.on_connection_stablished.emit()
            self.start()
            print("client connected")

    def close_connection(self):
        self._exiting = True
        if self.socket:
            self.socket.close()
            self.socket = None
            print("closed connection: " + str(self.addr [0]) + ":" + str(self.addr [1]) )
    
    def run(self):
        while not self._exiting and self.socket:
            data = recv_message(self.socket)
            if data:
                pong(self.socket)
                self.on_message.emit(self.addr, self.id , data)
            else:
                self._exiting = True
                self.close_connection()
                self.on_connection_lost.emit(self.addr, self.id)
                self.terminate()

class CommServer(QtCore.QThread):

    on_server_connected = QtCore.Signal(bool) #status 
    on_client_connected = QtCore.Signal(object, object) #return addr & id
    on_client_disconnected = QtCore.Signal(object, object) #return addr & id
    on_client_message_recv = QtCore.Signal(object, object, object) #return addr, id, bytes
    
    def __init__(self, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.host = get_local_ip_address()
        self.port = PORT
        self.server = None
        self._exiting = False
        self.sockets_ids = []
        self.timeout = 2.0

    def run(self):
        while not self._exiting:
            client, addr = self.server.accept()
            new_id = uuid.uuid1()
            comm_client = CommClient(client, addr, new_id)
            comm_client.on_message.connect(self.on_client_recv)
            comm_client.on_connection_lost.connect(self.on_client_lost)
            comm_client.start()
            self.sockets_ids.append(new_id)
            self.on_client_connected.emit(addr, new_id)
            print("connection accepted: " + str(addr[0]) + ":" + str(addr[1]))
            time.sleep(self.timeout)

    @QtCore.Slot(object, object)
    def on_client_lost(self, addr, id):
        for c in self.sockets_ids:
            if c == id:
                self.sockets_ids.remove(c)
                self.on_client_disconnected.emit(addr, id)
                break

    @QtCore.Slot(object, object, object)
    def on_client_recv( self,addr, id, data):
        self.on_client_message_recv.emit(addr, id, data)

    def start_connection(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.server.listen()
            self.start()
            self.on_server_connected.emit(True)
            print("server on")
        except:
            self.on_server_connected.emit(False)

    def close_connection(self):
        self._exiting = True

        if self.server:
            self.server.close()
            self.server = None
            print("server off")


class CommAwaker(QtCore.QThread):

    on_message = QtCore.Signal(object) 

    def __init__(self, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.host = get_local_ip_address()
        self.port = 9090
        self._exiting = False
        self.listener_socket = None
        self.communication_socket = None
        self.start()
    
    def close_connection(self):
        self._exiting = True

        if self.listener_socket:
            self.listener_socket.close()
            self.listener_socket = None
            
        if self.communication_socket:
            self.communication_socket.close()
            self.communication_socket = None

        print("Awaker closed")

    def send_to(self, message, ip_address):
        if self.communication_socket:
            msg_bytes = bytearray(len(message).to_bytes(4, byteorder="little"))
            msg_bytes.extend(message.encode())
            self.communication_socket.sendto((msg_bytes, (ip_address, self.port)))

    def run(self):
        self.communication_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.listener_socket.bind((self.host, self.port))

        print("awaker activated: " + str(self.host) + ":" + str(self.port))
        while not self._exiting:
            try:
                data, addr = self.listener_socket.recvfrom(2048)
                self.on_message.emit(data)
                print(data)
            except:
                pass

