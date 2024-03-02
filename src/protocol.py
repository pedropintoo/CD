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
        self.command = command
    
class JoinMessage(Message):
    """Message to join a chat channel."""

    def __init__(self, channel: str):
        super().__init__("join")
        self.channel = channel


class RegisterMessage(Message):
    """Message to register username in the server."""

    def __init__(self, username: str):
        super().__init__("register")
        self.user = username
    
class TextMessage(Message):
    """Message to chat with other clients."""

    def __init__(self, message: str, channel: str):
        super().__init__("message")
        self.message = message
        self.channel = channel
        self.ts = int(round(datetime.now().timestamp())) # Integer timestamp of current datetime


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
        # Algorithm to send by groups...
        connection.send(b"Ola")


    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        # Algorithm to check length...
        return connection.recv(1024)


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
