#!/usr/bin/env python3
'''
 # @ Author: Pedro Pinto (pmap@ua.pt)
 # @ Create Time: 2024-02-26
 # @ Description: Protocol for chat server 
                  Computação Distribuida Assignment 1.
 '''

import json
from datetime import datetime
from socket import socket

class Message:
    """Message Type."""
    
    def __init__(self, command: str):
        self.data = {"command":command}

    def __repr__(self):
        return json.dumps(self.data)
    
class JoinMessage(Message):
    """Message to join a chat channel."""

    def __init__(self, channel: str):
        super().__init__("join")
        self.data["channel"] = channel

class RegisterMessage(Message):
    """Message to register username in the server."""

    def __init__(self, username: str):
        super().__init__("register")
        self.data["user"] = username
    
class TextMessage(Message):
    """Message to chat with other clients."""

    def __init__(self, message: str, channel: str):
        super().__init__("message")
        self.data["message"] = message
        if channel != None:
            self.data["channel"] = channel
        self.data["ts"] = int(round(datetime.now().timestamp())) # Integer timestamp of current datetime

class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage(username)

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage(channel)

    @classmethod
    def message(cls, message:str , channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        return TextMessage(message, channel)

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        
        # Object message -> Json -> Bytes
        message = repr(msg).encode('utf-8')

        # Create a header with the length
        header = len(message).to_bytes(2, byteorder='big')

        # Send through the connection
        connection.send(header + message)

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        
        # Receive message size
        size = int.from_bytes(connection.recv(2),'big')

        if (size == 0): return None # Client disconnect
        
        received = connection.recv(size).decode('utf-8')
        
        try:
            # decoding JSON to Message
            data = json.loads(received) 
        except Exception:
            raise CDProtoBadFormat(received) 

        command = data.get("command") 

        if command == "join":
            return JoinMessage(data["channel"])
        elif command == "register":
            return RegisterMessage(data["user"])
        elif command == "message":
            return TextMessage(data["message"],data.get("channel"))
        else:
            raise CDProtoBadFormat(received)  


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
