import pickle
import socket


def pack(envelope):
    return pickle.dumps(envelope)

def unpack(packed_envelope):
    return pickle.loads(packed_envelope)

class Envelope(object):
    def __init__(self, title=None, message=None):
        if message is None:
            message = {}
        self.title = title
        self.message = message

    def set_title(self, title):
        self.title = title

    def get_title(self):
        return self.title

    def set_message(self, message):
        self.message = message

    def get_message(self):
        return self.message

class MySocket(object):
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, addr):
        self.sock.connect(addr)

    def send(self, msg):
        self.sock.sendall(msg)

    def receive(self):
        data_chunk_list = []
        while True:
            data_chunk = self.sock.recv(1024)
            if data_chunk:
                data_chunk_list.append(data_chunk)
            else:
                break
        data = b''.join(data_chunk_list)
        return data

    def bind(self, addr):
        self.sock.bind(addr)

    def listen(self, number):
        self.sock.listen(number)

    def accept(self):
        sock, addr = self.sock.accept()
        return MySocket(sock), addr

    def close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        finally:
            self.sock.close()

    def settimeout(self, n):
        self.sock.settimeout(n)









