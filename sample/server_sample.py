#!/usr/bin/env python3
'''
 # @ Author: Pedro Pinto (pmap@ua.pt)
 # @ Create Time: 2024-02-26
 '''

# server.py
import socket
import selectors

sel = selectors.DefaultSelector()

HOST = '' # symbolic name meaning all available interfaces
PORT = 8888 # arbitrary non-privileged port

def accept(sock, mask):
    conn, addr = sock.accept()  # Should be ready
    print('accepted from:', addr)
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    data = conn.recv(1000)  # Should be ready
    if data:
        print('echoing')
        conn.send(data)  # Hope it won't block
    else:
        print('closing')
        sel.unregister(conn)
        conn.close()

def main():
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) # Reuse address
    s.bind((HOST,PORT)) # bind to port on this machine
    s.listen(100)
    s.setblocking(False)
    
    sel.register(s, selectors.EVENT_READ, accept)
    
    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
        


if __name__ == "__main__" : 
    main()