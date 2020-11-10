import socket
import logging
from queue import Queue
import time
from multiprocessing import Process, Lock, Queue, SimpleQueue, Manager
import tarfile
import os
import sys
import pickle
from datetime import datetime
from datetime import timedelta

op_code_size = 2
new_sc_code = "ns"
new_sc_max_lenght = 1024
get_bu_code = "gb"
stop_bu_code = "st"
save_code = "sa"
new_back_code = "nb"
done_op_code = "dn"
retryinterval = 2
number_sub_slaves = 2

chunk_size = 950
max_chunk_size_in_digits = 4
uptodate_code = "up"
sendingbackup_code = "ok"

wait_time_between_busy = 5

class Server:
    def __init__(self, port, monitor_ip, monitor_port, listen_backlog = 0):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._lock_dic = {}
        self._monitor_ip = monitor_ip
        self._monitor_port = monitor_port
        self._last_slave_tasked = -1
        self._sub_dic = {}

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        done = "no"
        for i in range(0,number_sub_slaves):
            self._create_sub()
        while done != "done":
            client_sock = self.__accept_new_connection()
            done = self.__handle_client_connection(client_sock)
        for key in self._sub_dic:
            self._close_sub(key)


    def __handle_client_connection(self, client_sock):

        try:
            msg = client_sock.recv(op_code_size).decode()

            logging.info(
                'Message received from connection {}. Msg: {}'
                .format(client_sock.getpeername(), msg))
            
            if (msg == done_op_code):
                return "done"


            if (msg == new_sc_code):
                self._last_slave_tasked = (self._last_slave_tasked + 1) % number_sub_slaves
                elements_of_procces_to_task = self._sub_dic[self._last_slave_tasked]
                
                msg = client_sock.recv(new_sc_max_lenght).decode().split(",")
                ip = msg[0]
                port = int(msg[1])
                interval = int(msg[2])
                path = msg[3]
                logging.info("asked to backup {}".format(ip+","+str(port)+","+path))
                
                task_list = elements_of_procces_to_task[0]
                task_to_do = (ip,port,path,interval)
                task_list.append((datetime.now(),task_to_do))

                list_of_ip_port = elements_of_procces_to_task[1]
                list_of_ip_port.append((ip,path))

                lock_of_procces = elements_of_procces_to_task[2]
                self._lock_dic[(ip,path)] = lock_of_procces



            if (msg == get_bu_code):
                msg = client_sock.recv(new_sc_max_lenght).decode().split(",")
                ip = msg[0]
                path = msg[1]
                queue = SimpleQueue()
                queue.put(client_sock)
                Process(target=get_backup, args=(ip,path,self._lock_dic[(ip,path)],queue)).start()

            if (msg == stop_bu_code):
                msg = client_sock.recv(new_sc_max_lenght).decode().split(",")
                ip = msg[0]
                path = msg[1]
               

                procces_number = self._get_procces_for_task(ip,path)
                if(procces_number or procces_number ==0):
                    elements_of_procces_to_task = self._sub_dic[procces_number]
                    task_list = elements_of_procces_to_task[0]
                    task_to_do = (ip,0,path,-1)
                    task_list.append((datetime.now(),task_to_do))

                
        except OSError as e:
            logging.info("Error while reading socket {}, {}".format(client_sock,e))


    def __accept_new_connection(self):
        
        c, addr = self._server_socket.accept()
        logging.info('Got connection from {}'.format(addr))
        return c

    def _get_procces_for_task(self,ip,path):

        for i in range(0,number_sub_slaves):
            list_of_ip_port = self._sub_dic[i][1]
            if( (ip,path) in list_of_ip_port ):
                return i
        return None

    def _create_sub(self):
        task_list = Manager().list()
        stop_queue = SimpleQueue()
        lock = Lock()
        elements_of_procces = (task_list,[],lock,stop_queue)

        self._last_slave_tasked = (self._last_slave_tasked + 1) % number_sub_slaves
        self._sub_dic[self._last_slave_tasked] = elements_of_procces 

        Process(target=loop_backup, args=(stop_queue,task_list,
            lock,self._monitor_ip,self._monitor_port,self._last_slave_tasked)).start()

    def _close_sub(self,key):
        elements_of_procces = self._sub_dic[key]
        elements_of_procces[3].put("done")
        




def loop_backup(stop_queue,task_list,lock,monitor_ip,monitor_port,id):
    """
    Accept new connections

    Function blocks until a connection to a client is made.
    Then connection created is printed and returned
    """
    last_v=-1
    drop_task_dic = {}
    task_to_do = 0
    # Connection arrived
    while stop_queue.empty():
        try:
            task_to_do = get_ip_port_to_backup(task_list)
            ip = task_to_do[0]
            port = task_to_do[1]
            path = task_to_do[2]
            interval = task_to_do[3]

            if(ip==0 and port == 0):
                time.sleep(wait_time_between_busy)
                continue

            if(interval==-1):
                drop_task_dic[(ip,path)] = 1
                continue

            if((ip,path) in drop_task_dic):
                del drop_task_dic[(ip,path)]
                continue

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                s.settimeout(10)
                s.sendall((new_back_code+path).encode('utf-8'))
                
                
                msg = s.recv(2).decode()
                
                if(msg == sendingbackup_code):
                    last_v = (last_v+1)%10
                    f=open(str(id),"wb")

                    logging.info('creando file {}'.format(str(last_v)+ip+path+'.tar.gz'))
                    msg = s.recv(1024)
                    while(msg != b""):
                        f.write(msg)
                        msg = s.recv(1024)
                    f.close()
                    s.shutdown(socket.SHUT_RDWR)
                    s.close()

                    lock.acquire()
                    backufile = open(str(last_v)+ip+path+'.tar.gz',"wb")
                    f = open(str(id),"rb")
                    msg = f.read(1024)
                    while(msg != b""):
                        backufile.write(msg)
                        msg = f.read(1024)

                    lock.release()
                    f.close()
                    backufile.close()

                    logging.info('geting new backup \n')
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((monitor_ip, monitor_port))
                        s.sendall((save_code+ip+','+path).encode('utf-8'))
                        s.shutdown(socket.SHUT_RDWR)
            
            task_for_later = (datetime.now()+timedelta(0,interval),(ip,port,path,interval)) 
            task_list.append(task_for_later)

        except OSError as e:
            task_list.append((datetime.now(),task_to_do))
            logging.info("(Subproces)Error while reading socket {}, {}".format(e))

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

#task_list (tasks_due,(ip,port,path,interval))

def get_ip_port_to_backup(task_list):

    ordered_list = []
    for task in task_list:
        ordered_list.append(task)
    ordered_list.sort(key = lambda a: a[0])

    if(not ordered_list):
        return (0,0,0,0)

    task_list.remove(ordered_list[0])
    list_result = ordered_list[0]

    tasks_due = list_result[0]
    if(tasks_due < datetime.now()):
        return (list_result[1][0],list_result[1][1],list_result[1][2],list_result[1][3]) 
    else:
        task_list.append(list_result)
        return (0,0,0,0)