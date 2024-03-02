#!/usr/bin/env python3
'''
 # @ Author: Pedro Pinto (pmap@ua.pt)
 # @ Create Time: 2024-02-26
 # @ Description: CD Chat client program
 '''

import logging
import sys
import socket

from .protocol import CDProto, CDProtoBadFormat
logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)

SERVER = "127.0.0.1" # localhost
PORT = 8888 # server port

class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.sock.connect((SERVER,PORT)) # connect to server (block until accepted)
        self.loop()
        # Miss stdin flags

    def loop(self):
        """Loop indefinitely."""
        while (True):
            # send some data
            str_send = input(">")
            self.sock.send(str_send.encode("utf-8"))
            
            # receive the response
            data = self.sock.recv(1024)
            print(data)
