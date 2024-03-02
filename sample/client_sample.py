#!/usr/bin/env python3
'''
 # @ Author: Pedro Pinto (pmap@ua.pt)
 # @ Create Time: 2024-02-26
 '''

# server.py
import socket

SERVER = "127.0.0.1" # localhost
PORT = 8888 # server port

def main():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER,PORT)) # connect to server (block until accepted)
    
    str_send = input("Message to send: ")

    s.send(str_send.encode("utf-8")) # send some data
    
    data = s.recv(1024) # receive the response
    print(data)

    s.close() 


if __name__ == "__main__" : 
    main()