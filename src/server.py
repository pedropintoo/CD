#!/usr/bin/env python3
'''
 # @ Author: Pedro Pinto (pmap@ua.pt)
 # @ Create Time: 2024-02-26
 # @ Description: CD Chat server program.
 '''

import logging
import socket
import selectors

logging.basicConfig(filename="server.log", level=logging.DEBUG)

HOST = '' # symbolic name meaning all available interfaces
PORT = 8888 # arbitrary non-privileged port

class Server:
    """Chat Server process."""

    def accept(self):
        conn, addr = self.sock.accept()  # Should be ready
        print('accepted from:', addr)
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn):
        data = conn.recv(1000)  # Should be ready
        if data:
            print('echoing')
            conn.send(data)  # Hope it won't block
        else:
            print('closing')
            self.sel.unregister(conn)
            conn.close()

    def loop(self):
        """Loop indefinitely."""

        # Create the server Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) # Reuse address
        self.sock.bind((HOST,PORT)) # bind to port on this machine
        self.sock.listen(100)
        self.sock.setblocking(False)
        
        # Start the selector
        self.sel = selectors.DefaultSelector()
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)
        
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
