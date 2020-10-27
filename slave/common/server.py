import socket
import logging
from queue import Queue
import time
from multiprocessing import Process, Lock, Queue, SimpleQueue
import tarfile
import os
import sys
import pickle
from datetime import datetime

op_code_size = 2
new_sc_code = "ns"
new_sc_max_lenght = 1024
get_bu_code = "gb"
stop_bu_code = "st"
save_code = "sa"
new_back_code = "nb"
retryinterval = 2

chunk_size = 950
max_chunk_size_in_digits = 4
uptodate_code = "up"
sendingbackup_code = "ok"

class Server:
    def __init__(self, port, monitor_ip, monitor_port, listen_backlog = 0):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._lock_dic = {}
        self._monitor_ip = monitor_ip
        self._monitor_port = monitor_port

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
               
        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection(client_sock)


    def __handle_client_connection(self, client_sock):

        try:
            msg = client_sock.recv(op_code_size).decode()

            logging.info(
                'Message received from connection {}. Msg: {}'
                .format(client_sock.getpeername(), msg))
            if (msg == new_sc_code):
                msg = client_sock.recv(new_sc_max_lenght).decode().split(",")
                ip = msg[0]
                port = int(msg[1])
                interval = int(msg[2])
                path = msg[3]
                logging.info("asked to backup {}".format(ip+","+str(port)+","+path))
                queue = Queue();
                lock = Lock()
                self._lock_dic[(ip,path)] = (lock,queue)
                Process(target=loop_backup, args=(queue,ip,port,interval,path,
                    lock,self._monitor_ip,self._monitor_port)).start()
            if (msg == get_bu_code):
                msg = client_sock.recv(new_sc_max_lenght).decode().split(",")
                ip = msg[0]
                path = msg[1]
                queue = SimpleQueue()
                queue.put(client_sock)
                Process(target=get_backup, args=(ip,path,self._lock_dic[(ip,path)][0],queue)).start()
            if (msg == stop_bu_code):
                msg = client_sock.recv(new_sc_max_lenght).decode().split(",")
                ip = msg[0]
                path = msg[1]
                self._lock_dic[(ip,path)][1].put(1)
                del self._lock_dic[(ip,path)]

        except OSError as e:
            logging.info("Error while reading socket {}, {}".format(client_sock,e))


    def __accept_new_connection(self):
        
        c, addr = self._server_socket.accept()
        logging.info('Got connection from {}'.format(addr))
        return c

def loop_backup(queue,ip,port,interval,path,lock,monitor_ip,monitor_port):
    """
    Accept new connections

    Function blocks until a connection to a client is made.
    Then connection created is printed and returned
    """
    last_v=-1
    # Connection arrived
    while queue.empty():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                s.sendall((new_back_code+path).encode('utf-8'))
                
                msg = s.recv(2).decode()
                if(msg == sendingbackup_code):
                    last_v = (last_v+1)%10
                    lock.acquire()
                    f = open(str(last_v)+ip+path+'.tar.gz',"wb")

                    logging.info('creando file {}'.format(str(last_v)+ip+path+'.tar.gz'))
                    msg = s.recv(1024)
                    while(msg != b""):
                        f.write(msg)
                        msg = s.recv(1024)
                    f.close()
                    lock.release()
                    logging.info('geting new backup \n')
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((monitor_ip, monitor_port))
                        s.sendall((save_code+ip+','+path).encode('utf-8'))
                        s.shutdown(socket.SHUT_RDWR)
            time.sleep(interval)
        except OSError as e:
            time.sleep(retryinterval)
            logging.info("error, reintentando")


def get_backup(ip,path,lock,queue):
    client_sock = queue.get()
    lock.acquire()
    files_found = 10
    data = {}
    for i in range(0,10):
        try:
            bu_path = str(i)+ip+path+'.tar.gz'
            data["mod"+str(i)] = datetime.fromtimestamp(os.path.getmtime(bu_path)).strftime('%Y-%m-%d %H:%M:%S')
            data["size"+str(i)] = os.path.getsize(bu_path)
        except OSError as e:
            files_found = files_found - 1
    logging.info("number files found: {}".format(files_found))
    lock.release()
    #client_sock.sendall(sys.getsizeof(data).zfill(6).encode())
    client_sock.sendall(pickle.dumps(data))
    client_sock.shutdown(socket.SHUT_RDWR)

