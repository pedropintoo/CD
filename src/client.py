#!/usr/bin/env python3
'''
 # @ Author: Pedro Pinto (pmap@ua.pt)
 # @ Create Time: 2024-02-26
 # @ Description: CD Chat client program
 '''

import logging
import sys
import socket
import selectors

from .protocol import CDProto, CDProtoBadFormat

logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)

SERVER = "127.0.0.1" # localhost
PORT = 8888 # server port

class Client:
    """Chat Client process."""

    def __init__(self, name: str = "Foo"):
        """Initializes chat client."""
        self.username = name

        # Start the selector
        self.sel = selectors.DefaultSelector()

    def connect(self):
        """Connect to chat server and setup stdin flags."""

        # Setup socket with server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((SERVER,PORT)) # connect to server (block until accepted)

        # Register Message
        CDProto.send_msg(self.sock,CDProto.register(self.username))

        # Handler to Receive Message from Server
        self.sel.register(self.sock, selectors.EVENT_READ, self.handle_receive_message)
        
        # Handler for Input
        self.sel.register(sys.stdin, selectors.EVENT_READ, self.handle_input_message)


    def loop(self):
        """Loop indefinitely."""
        while True:
            # Wait for events
            events = self.sel.select()
            # Handle events
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

    ############## Handlers ##############    

    def handle_input_message(self, stdin, mask):
        # Blocked until input is done
        str_send = input(">")
        # Send message (EXAMPLE - textMessage)
        textMessage = CDProto.message(str_send)       
        CDProto.send_msg(self.sock, textMessage) 

    def handle_receive_message(self, sock, mask):
        message = CDProto.recv_msg(sock)
        print("<"+message)
            
            
