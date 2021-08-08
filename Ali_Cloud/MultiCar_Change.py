
import os
import time
from multiprocessing import Process
import socket
msg="ok"

def communction(a):
    while(1):
        data=a.recv(1024)
        print(data.decode())
        a.send(msg.encode())


def test1():
    server=socket.socket()
    server.bind(('127.0.0.1',8888))
    server.listen(5)

    while(1):
        a,b=server.accept()
        print(dir([a]))
        p = Process(target=communction,args=(a,))
        print(b)
        p.start()
if __name__ == '__main__':
    test1()



