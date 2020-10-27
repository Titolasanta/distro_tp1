#!/usr/bin/env python3

import os
import socket
import time
import logging
import json
from common.server import Server


def parse_config_params():
	""" Parse env variables to find program config params

	Function that search and parse program configuration parameters in the
	program environment variables. If at least one of the config parameters
	is not found a KeyError exception is thrown. If a parameter could not
	be parsed, a ValueError is thrown. If parsing succeeded, the function
	returns a map with the env variables
	"""
	

	config_params = {}

	try:
		config_params["port"] = int(os.environ["PORT"])
		config_params["cord_ip"] = os.environ["TEST_IP"]
		config_params["cord_port"] = os.environ["TEST_PORT"]

		config_params["ID"] = os.environ["SC_ID"]

	except KeyError as e:
		raise KeyError("Config file not found, nor config environment variables Error: {} .Aborting server".format(e))
	except ValueError as e:
		raise ValueError("Config file not found and Key could not be parsed. Error: {}. Aborting server".format(e))

	return config_params

def main():	
	import os




	initialize_log()
	config_params = parse_config_params()

	hostname = socket.gethostname()
	IP = socket.gethostbyname(hostname)
	logging.info("my hostname is: {}. other ip is: {}".format(IP,config_params["cord_ip"]))


	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.connect((config_params["cord_ip"], int(config_params["cord_port"])))
		s.sendall(("sc"+config_params["ID"]).encode('utf-8'))
		s.close()

	# Initialize server and start server loop
	server = Server(config_params["port"])

	server.run()

def initialize_log():
	"""
	Python custom logging initialization

	Current timestamp is added to be able to identify in docker
	compose logs the date when the log has arrived
	"""
	
	logging.basicConfig(
		format='%(asctime)s %(levelname)-8s %(message)s',
		level=logging.INFO,
		datefmt='%Y-%m-%d %H:%M:%S',
	)


if __name__== "__main__":
	main()
