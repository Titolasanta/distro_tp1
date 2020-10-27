import socket
import logging
from queue import Queue
import time
import datetime

op_code_size = 2
save_code = "sa"
new_sc_max_lenght = 1024

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
        f = open("registro.txt","w")
        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection(client_sock,f)


    def __handle_client_connection(self, client_sock,f):

        try:
            msg = client_sock.recv(op_code_size).decode()

            logging.info(
                'Message received from connection {}. Msg: {}'
                .format(client_sock.getpeername(), msg))
            if (msg == save_code):
                msg = client_sock.recv(new_sc_max_lenght).decode().split(",")
                ip = msg[0]
                path = msg[1]
                f.write(datetime.datetime.now().strftime("%H:%M:%S")+": "+ip+" "+path)
                f.flush()
                logging.info("logging backup {}".format(ip+","+path))
        except OSError as e:
            logging.info("Error while reading socket {}, {}".format(client_sock,e))


    def __accept_new_connection(self):
        
        logging.info("Proceed to accept new connections")
        c, addr = self._server_socket.accept()
        logging.info('Got connection from {}'.format(addr))
        return c
