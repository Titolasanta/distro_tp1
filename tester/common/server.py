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


new_sc_code = "ns"
get_bu_code = "gb"
stop_bu_code = "st"

def _recv_until(socket,delimiter):
    return "not implemented"


class Server:
    def __init__(self, port, cord_ip, cord_port, listen_backlog=0):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._cord_port = cord_port
        self._cord_ip = cord_ip
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
        while (num_links != number_sidecards):
            client_sock = self.__accept_new_connection()
            num_links = self.__handle_client_connection(client_sock,num_links)
        
        time.sleep(3)
        self._send_req((self._cord_ip,self._cord_port),
            (new_sc_code+self._sc_dic["1"]+","+str(sc_port)+","+"00005"+","+"data1"))
           
        self._send_req((self._cord_ip,self._cord_port),
            (new_sc_code+self._sc_dic["2"]+","+str(sc_port)+","+"00005"+","+"data1"))
           
        time.sleep(10)

        self._send_req((self._sc_dic["1"],sc_port),
            ("md"+"data1"))

        time.sleep(10)

        self._send_req_and_read_answer((self._cord_ip,self._cord_port),
            (get_bu_code+self._sc_dic["1"]+","+"data1"))


        time.sleep(10)

        self._send_req((self._cord_ip,self._cord_port),
            (stop_bu_code+self._sc_dic["1"]+","+"data1"))

        
    def __handle_client_connection(self, client_sock,num_links):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """

        try:
            msg = client_sock.recv(op_code_size).decode()
            logging.info(
                'Message received from connection {}. Msg: {}'
                    .format(client_sock.getpeername(), msg))
            if (msg == sidecard_op_code):
                num_links = num_links+1
                sc_id = client_sock.recv(sc_id_size).decode()
                self._sc_dic[sc_id] = client_sock.getpeername()[0];
                logging.info("#sc_saved {}".format(num_links))

        except OSError as e:
            logging.info("Error while reading socket {}, {}".format(client_sock,e))
        finally:
            client_sock.close()
        return num_links

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

    def _send_req(self, who, what):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(who)
            s.sendall((what).encode('utf-8'))

    def _send_req_and_read_answer(self, who, what):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(who)
            s.sendall((what).encode('utf-8'))
            #msg = s.recv(6).decode()
            msg = pickle.loads(s.recv(2000))
            logging.info("recv esto {}".format(msg))
            s.close() 