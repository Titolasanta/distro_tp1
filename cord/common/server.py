import socket
import logging
import time
import pickle

sc_id_size = 6
sl_id_size = 6
op_code_size = 2
sc_port = 10000
sl_port = 10000
sidecard_op_code = "sc"
slave_op_code = "sl"

number_sidecards = 2
number_slaves = 2


new_sc_code = "ns"
get_bu_code = "gb"
stop_bu_code = "st"

def _recv_until(socket,delimiter):
    return "not implemented"


class Server:
    def __init__(self, port, listen_backlog=0):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._sc_dic = {}
        self._sl_dic = {}
        self._slsc_dic = {}
    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        num_links = 0 # num_sc,num_sl
        next_slave_turn = 0
        while (num_links != number_slaves):
            client_sock = self.__accept_new_connection()
            num_links = self.__handle_client_connection_1(client_sock,num_links,next_slave_turn)
        
        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection_2(client_sock,num_links,next_slave_turn)


    def __handle_client_connection_1(self, client_sock,num_links,next_slave_turn):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """

        try:
            code = client_sock.recv(op_code_size).decode()
            logging.info(
                'Message received from connection {}. Msg: {}'
                    .format(client_sock.getpeername(), code))

            if (code == slave_op_code):
                num_links = num_links+1
                sl_id = client_sock.recv(sl_id_size).decode()
                self._sl_dic[sl_id] = client_sock.getpeername()[0];
                logging.info("#sl_saved {}".format(num_links))
            return num_links

        except OSError as e:
            logging.info("Error while reading socket {}, {}".format(client_sock,e))
        finally:
            client_sock.close()
    def __handle_client_connection_2(self, client_sock,num_links,next_slave_turn):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """

        try:
            code = client_sock.recv(op_code_size).decode()
            logging.info(
                'Message received from connection {}. Msg: {}'
                    .format(client_sock.getpeername(), code))
            splited = 0
            if (code == stop_bu_code or code == new_sc_code or code == get_bu_code):
                next_slave_turn = ((next_slave_turn)%num_links) + 1
                msg = client_sock.recv(1024)
                splited = msg.decode().split(",")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    logging.info(
                        'sending to {}.'
                            .format((self._sl_dic[str(next_slave_turn)],sl_port)))
                    s.connect((self._sl_dic[str(next_slave_turn)],sl_port))
                    s.sendall(code.encode())
                    s.sendall(msg)
                    if(code == get_bu_code):
                        client_sock.sendall(s.recv(2000))
                    s.shutdown(socket.SHUT_RDWR)
                if(code == new_sc_code):
                    ip = splited[0]
                    port = int(splited[1])
                    interval = int(splited[2])
                    path = splited[3]
                    self._slsc_dic[(ip,path)] = str(next_slave_turn)
                if(code == stop_bu_code):
                    ip = splited[0]
                    path = splited[1]
                    try:
                        del self._slsc_dic[(ip,path)]
                    except Error:
                        pass

        except OSError as e:
            logging.info("Error while reading socket {}, {}".format(client_sock,e))
        finally:
            client_sock.close()



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