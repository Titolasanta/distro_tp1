import socket
import logging
import tarfile
import sys
import os
from datetime import datetime

chunk_size = 950
max_chunk_size_in_digits = 4
uptodate_code = "up"
sendingbackup_code = "ok"
op_code_size = 2
new_back_code = "nb"
mod_data_code = "md"


class Server:
    def __init__(self, port, listen_backlog = 0):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        old_time = {" ": "dumy"}    
        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection(client_sock,old_time)


    def __handle_client_connection(self, client_sock,old_time):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """

        try:
            code = client_sock.recv(op_code_size).rstrip().decode()
            logging.info(
                'Message received from connection {}. Msg: {}'
                    .format(client_sock.getpeername(), code))
            if(code == new_back_code):
                path = client_sock.recv(1024).rstrip().decode()

                logging.info(
                    'Message received from connection {}. Msg: {}'
                        .format(client_sock.getpeername(), path))
                try:
                    new_time =max(os.path.getmtime(root) for root,_,_ in os.walk(path))
                except:
                    logging.info("invalid req")
                    return
                
               
                if((path not in old_time) or (new_time != old_time[path])):
                    logging.info("sending new backup")
                    with tarfile.open(path+'backup' + '.tar.gz', mode='w:gz') as archive:
                        archive.add(path)
                        archive.close()
                    client_sock.sendall(sendingbackup_code.encode())
                    f = open(path+'backup' + '.tar.gz', "rb")
                    chunk = f.read(chunk_size).rstrip()
                    while(chunk):
                        client_sock.sendall(chunk) 
                        chunk = f.read(chunk_size).rstrip()
                    f.close()
                    client_sock.shutdown(socket.SHUT_RDWR)
                    client_sock.close()
                    old_time[path] = new_time
                else:
                    client_sock.sendall(uptodate_code.encode()) 


            if(code == mod_data_code):
                path = client_sock.recv(1024).rstrip().decode()

                f = open(path+'/' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "w")
                f.write("123")
                f.flush()
                f.close()
                
        except OSError as e:
            logging.info("Error {}".format(e))


    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        c, addr = self._server_socket.accept()
        logging.info('Got connection from {}'.format(addr))
        return c