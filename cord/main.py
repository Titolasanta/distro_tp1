#!/usr/bin/env python3

import os
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
		with open('data1/test.json') as f:
			data = json.load(f)
		config_params["port"] = int(data["SERVER_PORT"])
		
	except OSError as e:
		try:
			config_params["port"] = int(os.environ["SERVER_PORT"])
		except KeyError as e:
			raise KeyError("Config file not found, nor config environment variables Error: {} .Aborting server".format(e))
		except ValueError as e:
			raise ValueError("Config file not found and Key could not be parsed. Error: {}. Aborting server".format(e))

	return config_params

def main():	
	import os




	initialize_log()
	config_params = parse_config_params()

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
