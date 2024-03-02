#!/usr/bin/env python3
'''
 # @ Author: Pedro Pinto (pmap@ua.pt)
 # @ Create Time: 2024-02-26
 # @ Description: CD Chat server program.
 '''

import logging
import socket
import selectors

from .protocol import CDProto, CDProtoBadFormat, RegisterMessage

logging.basicConfig(filename="server.log", level=logging.DEBUG)

HOST = '' # symbolic name meaning all available interfaces
PORT = 8888 # arbitrary non-privileged port

class Server:
    """Chat Server process."""

    def __init__(self):
        """Initializes chat server."""
        
        # Channels data structure
        self.channels = {"main" : []}

        # Create the server Socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) # Reuse address
        sock.bind((HOST,PORT)) # bind to port on this machine
        sock.listen(100)
        sock.setblocking(False)

        # Start the selector
        self.sel = selectors.DefaultSelector()
        # Prepare for clients
        self.sel.register(sock, selectors.EVENT_READ, self.handle_new_connection)

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

    def handle_new_connection(self, sock, mask):
        """Handle new client connection."""
        conn, addr = sock.accept()
        print('accepted from:', addr)
        # Client socket
        conn.setblocking(False)
        # Receive Register Message from client     
        message = CDProto.recv_msg(conn)

        self.channels["main"].append(conn)

        # Handle future data from this client  
        self.sel.register(conn, mask, self.handle_receive_message)    

    def handle_receive_message(self, sock, mask):
        message = CDProto.recv_msg(sock)
        # Decide to whom we should send the message...
        if message.data["command"] == "message":
            for client_socket in self.channels["main"]:
                CDProto.send_msg(client_socket, message)
