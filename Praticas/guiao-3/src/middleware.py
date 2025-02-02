"""Middleware to communicate with PubSub Message Broker."""
from collections.abc import Callable
from enum import Enum
from queue import LifoQueue, Empty
from typing import Any
import socket
import json
import pickle
import xml.etree.ElementTree as ET

JSON = 0
XML = 1
PICKLE = 2

class MiddlewareType(Enum):
    """Middleware Type."""

    CONSUMER = 1
    PRODUCER = 2


class Queue:
    """Representation of Queue interface for both Consumers and Producers."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        self.topic = topic
        self.type = _type
        
        # Socket connection to middleware
        self.socket_middleware = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_middleware.connect(("localhost", 5000))
        self.socket_middleware.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def push(self, value):
        """Sends data to broker."""
        # Add the size of the data to the message
        pass

    def pull(self) -> (str, Any):
        """Receives (topic, data) from broker.
        Should BLOCK the consumer!"""
        pass

    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        print("NOT IMPLEMENTED")
        pass
        # message = {"command": "list_topics"}
        # message_bytes = message.encode('utf-8')
        # size_message = len(message_bytes).to_bytes(2, "big")
        # self.socket_middleware.send( size_message + message_bytes)

    def cancel(self):
        """Cancel subscription."""
        pass


class JSONQueue(Queue):
    """Queue implementation with JSON based serialization."""
    
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        super().__init__(topic, _type)

        self.type_bytes = JSON.to_bytes(1, "big")
        
        # Send subscribe message to broker
        if _type == MiddlewareType.CONSUMER:
            message = json.dumps({"command": "subscribe", "topic": topic})
            message_bytes = message.encode('utf-8')
            size_message = len(message_bytes).to_bytes(2, "big")
            
            self.socket_middleware.send(size_message + self.type_bytes + message_bytes)
        
    def push(self, value):
        """Sends data to broker."""
        message = json.dumps({"command": "publish", "topic": self.topic, "value": value})
        message_bytes = message.encode('utf-8')

        size_message = len(message_bytes).to_bytes(2, "big")

        self.socket_middleware.send(size_message + self.type_bytes + message_bytes)

    def pull(self) -> (str, Any):
        """Receives (topic, data) from broker.
        Should BLOCK the consumer!"""
        #print(self.socket_middleware)
        size_message = int.from_bytes(self.socket_middleware.recv(2), 'big')
        
        if size_message != 0:
            data = json.loads(self.socket_middleware.recv(size_message))
            #print(data)
            return (data["topic"], data["value"])

        
        return (None, None)

    def cancel(self):
        """Cancel subscription."""
        message = json.dumps({"command": "unsubscribe", "topic": self.topic})
        message_bytes = message.encode('utf-8')
        size_message = len(message_bytes).to_bytes(2, "big")
        self.socket_middleware.send( size_message + self.type_bytes + message_bytes)        

class XMLQueue(Queue):
    """Queue implementation with XML based serialization."""
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        super().__init__(topic, _type)

        self.type_bytes = XML.to_bytes(1, "big")
        
        # Send subscribe message to broker
        if _type == MiddlewareType.CONSUMER:
            # XML format
            message = f"<message><command>subscribe</command><topic>{topic}</topic></message>"
            message_bytes = message.encode('utf-8') 
            size_message = len(message_bytes).to_bytes(2, "big")
            
            self.socket_middleware.send(size_message + self.type_bytes + message_bytes)

    def push(self, value):
        """Sends data to broker."""
        message = f"<message><command>publish</command><topic>{self.topic}</topic><value>{value}</value></message>"
        message_bytes = message.encode('utf-8')
    
        size_message = len(message_bytes).to_bytes(2, "big")

        self.socket_middleware.send(size_message + self.type_bytes + message_bytes)
    
    def pull(self) -> (str, Any):
        """Receives (topic, data) from broker.
        Should BLOCK the consumer!"""
        size_message = int.from_bytes(self.socket_middleware.recv(2), 'big')

        if size_message != 0:
            data = self.socket_middleware.recv(size_message)
            # Parsing XML
            root = ET.fromstring(data.decode('utf-8'))
            topic = root.find('topic').text
            value = root.find('value').text
            return (topic, value)

        return (None, None)

    def cancel(self):
        """Cancel subscription."""
        message = f"<message><command>unsubscribe</command><topic>{self.topic}</topic></message>"
        message_bytes = message.encode('utf-8')
        size_message = len(message_bytes).to_bytes(2, "big")

        self.socket_middleware.send(size_message + self.type_bytes + message_bytes)    
        
        
class PickleQueue(Queue):
    """Queue implementation with Pickle based serialization."""
    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        super().__init__(topic, _type)

        self.type_bytes = PICKLE.to_bytes(1, "big")
        
        # Send subscribe message to broker
        if _type == MiddlewareType.CONSUMER:
            message_bytes = pickle.dumps({"command": "subscribe", "topic": self.topic})
            size_message = len(message_bytes).to_bytes(2, "big")

            self.socket_middleware.send(size_message + self.type_bytes + message_bytes)
        
    def push(self, value):
        """Sends data to broker."""
        message_bytes = pickle.dumps({"command": "publish", "topic": self.topic, "value": value})
    
        size_message = len(message_bytes).to_bytes(2, "big")

        self.socket_middleware.send(size_message + self.type_bytes + message_bytes)

    def pull(self) -> (str, Any):
        """Receives (topic, data) from broker.
        Should BLOCK the consumer!"""
        size_message = int.from_bytes(self.socket_middleware.recv(2), 'big')

        if size_message != 0:
            data = pickle.loads(self.socket_middleware.recv(size_message))
            return (data["topic"], data["value"])

        return (None, None)

    def cancel(self):
        """Cancel subscription."""
        message_bytes = pickle.dumps({"command": "unsubscribe", "topic": self.topic})
        size_message = len(message_bytes).to_bytes(2, "big")

        self.socket_middleware.send( size_message + self.type_bytes + message_bytes)        