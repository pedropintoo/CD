"""Message Broker"""
import enum
import socket
import selectors
import json
import pickle
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple


class Serializer(enum.Enum):
    """Possible message serializers."""
    JSON = 0
    XML = 1
    PICKLE = 2


class Broker:
    """Implementation of a PubSub Message Broker."""

    def __init__(self):
        """Initialize broker."""
        self.canceled = False
        # Start Socket
        self._host = "localhost"
        self._port = 5000
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) # Reuse address
        self._socket.bind((self._host, self._port))
        self._socket.listen(100)
        self._socket.setblocking(False)

        self.subscribers = {}
        self.lastValues = {}

        # Start selector
        self.sel = selectors.DefaultSelector()

        self.sel.register(self._socket, selectors.EVENT_READ, self.handle_new_connection)


    def list_topics(self) -> List[str]:
        """Returns a list of strings containing all topics containing values."""
        return [topic for topic in self.lastValues.keys() if self.lastValues[topic] is not None]

    def get_topic(self, topic):
        """Returns the currently stored value in topic."""
        return self.lastValues.get(topic)

    def put_topic(self, topic, value):
        """Store in topic the value."""
        if (self.subscribers.get(topic) is None):
            self.subscribers[topic] = []     

        self.lastValues[topic] = value  


    def list_subscriptions(self, topic: str) -> List[Tuple[socket.socket, Serializer]]:
        """Provide list of subscribers to a given topic."""
        return self.subscribers.get(topic)

    def subscribe(self, topic: str, address: socket.socket, _format: Serializer = None):
        """Subscribe to topic by client in address."""
        if (self.subscribers.get(topic) is None):
            self.subscribers[topic] = []
            self.lastValues[topic] = None

        for sub_topic in self.subscribers.keys():
            if sub_topic.startswith(topic):
                self.subscribers[sub_topic].append((address, _format)) 

        print(str(self.subscribers))                   

    def unsubscribe(self, topic, address):
        """Unsubscribe to topic by client in address."""

        if (self.subscribers.get(topic) is None):
            return
        
        for sub_topic in self.subscribers.keys():
            if sub_topic.startswith(topic):  
                consumer = None  
                for consumerInfo in self.subscribers[sub_topic]:
                    if consumerInfo[0] == address:
                        consumer = consumerInfo
                        break
                
                self.subscribers[sub_topic].remove(consumer)
            

    def run(self):
        """Run until canceled."""

        while not self.canceled:
            # Wait for events
            events = self.sel.select()
            # Handle events
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

    def send(self, conn: socket.socket, msg, _format: Serializer):
        
        data = None
        if (_format == Serializer.JSON.value):
            # encoding JSON
            data = json.dumps(msg).encode("utf-8")
        elif (_format == Serializer.PICKLE.value):
            # encoding PICKLE
            data = pickle.dumps(msg) 
        elif (_format == Serializer.XML.value):
            # encoding XML
            data = f"<message><topic>{msg['topic']}</topic><value>{msg['value']}</value></message>".encode("utf-8")
        
        if data is None:
            return

        size = len(data).to_bytes(2, "big")

        conn.send(size + data)


    ############## Handlers ##############      

    def handle_new_connection(self, sock, mask):
        """Handle new client connection."""
        conn, addr = sock.accept()
        # Client socket
        conn.setblocking(False)

        # Handle future data from this client  
        self.sel.register(conn, mask, self.handle_requests)    

    def handle_requests(self, conn, mask):
        
        size = int.from_bytes(conn.recv(2),'big')

        data = None

        if (size != 0):
            type_msg = int.from_bytes(conn.recv(1),'big')
            received = conn.recv(size)

            if not (type_msg == Serializer.PICKLE.value):
                received = received.decode('utf-8')

            if (type_msg == Serializer.JSON.value):
                # decoding JSON to Message
                data = json.loads(received) 
            elif (type_msg == Serializer.PICKLE.value):
                # decoding PICKLE to Message
                data = pickle.loads(received)
            elif (type_msg == Serializer.XML.value):
                # decoding XML to Message
                node = ET.fromstring(received)
                
                data = {}
                data['command'] = node.find('command').text
                data['topic'] = node.find('topic').text
                if (node.find('value') is not None):
                    data['value'] = node.find('value').text
            
        if (data is None):
            return
        
        command = data.get("command") 
        
        if command == "subscribe":
            topic = data.get("topic")
            self.subscribe(topic, conn, type_msg)
        elif command == "publish":
            topic = data.get("topic")
            value = data.get("value")
            self.put_topic(topic, value)

            for upper_topic in self.subscribers.keys():
                if topic.startswith(upper_topic):
                    for (conn, type_msg) in self.subscribers[upper_topic]:
                        message = {"topic": upper_topic, "value": value}
                        try:
                            self.send(conn, message, type_msg)
                        except:
                            print("Not found")    
                        
        elif command == "listTopics":
            pass
        elif command == "unsubscribe":
            topic = data.get("topic")
            self.unsubscribe(topic, conn)
        else:
            print("ERROR!")      
