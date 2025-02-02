""" Chord DHT node implementation. """
import socket
import threading
import logging
import pickle
from utils import dht_hash, contains
import math


class FingerTable:
    """Finger Table."""

    def __init__(self, node_id, node_addr, m_bits=10):
        """ Initialize Finger Table."""

        self.node_id = node_id
        self.node_addr = node_addr
        self.m_bits = m_bits

        # Initialize the finger table with m_bits entries.
        # Each entry is a tuple (node_id, node_addr) initially pointing to the node itself.
        self.table = [(node_id, node_addr) for _ in range(m_bits)]


    def fill(self, node_id, node_addr):
        """ Fill all entries of the finger table with node_id, node_addr."""

        for i in range(self.m_bits):
            self.table[i] = (node_id, node_addr)

    def update(self, index, node_id, node_addr):
        """Update index of table with node_id and node_addr."""

        self.table[index-1] = (node_id, node_addr) # Adjust for 0-based indexing in Python lists


    def find(self, identification):
        """ Get node address of closest preceding node (in finger table) of identification. """

        # Iterate in reverse through the finger table to find the highest entry that precedes the given identification.
        for i in range(self.m_bits - 1, -1, -1):
            node_id, node_addr = self.table[i]

            if contains(node_id, self.node_id, identification):
                return node_addr
            
        return self.table[0][1]

    def refresh(self):
        """ Retrieve finger table entries requiring refresh. (ALL)"""
        refreshList = []

        for i in range(self.m_bits):
            index = i + 1 
            node = (self.node_id + 2 ** i) % (2 ** self.m_bits)
            address = self.table[i][1]
            refreshList.append((index,node,address))

        return refreshList

    def getIdxFromId(self, id):
        """Return index in the finger table by id."""

        temp = (id - self.node_id) % (2 ** self.m_bits)          
        return int(math.log2(temp)) + 1
         

    def __repr__(self):
        return str(self.as_list)

    @property
    def as_list(self):
        """return the finger table as a list of tuples: (identifier, (host, port)).
        NOTE: list index 0 corresponds to finger_table index 1
        """
         # Directly return the finger table as it matches the specified output format.
        return self.table

class DHTNode(threading.Thread):
    """ DHT Node Agent. """

    def __init__(self, address, dht_address=None, timeout=3):
        """Constructor

        Parameters:
            address: self's address
            dht_address: address of a node in the DHT
            timeout: impacts how often stabilize algorithm is carried out
        """
        threading.Thread.__init__(self) # each node is a new thread
        self.done = False
        self.identification = dht_hash(address.__str__())
        self.addr = address  # My address
        self.dht_address = dht_address  # Address of the initial Node
        if dht_address is None:
            self.inside_dht = True
            # I'm my own successor
            self.successor_id = self.identification
            self.successor_addr = address
            # I have no predecessor! (I'm the only one in the DHT)
            self.predecessor_id = self.identification   # REFACTORED
            self.predecessor_addr = address             # REFACTORED
        else:
            self.inside_dht = False
            # Start from knowing nothing about the DHT
            self.successor_id = None
            self.successor_addr = None
            self.predecessor_id = None
            self.predecessor_addr = None

        # Each node will have his own finger table
        self.finger_table = FingerTable(self.identification,self.addr)    #TODO create finger_table
        self.keystore = {}  # Where node data is stored

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        
        # Logging
        self.logger = logging.getLogger("Node [{}]".format(self.identification)) # REFACTORED
        # create console handler with a higher log level        
        CustomFormatter().setup(self.logger) # REFACTORED

    def send(self, address, msg):
        """ Send msg to address. """
        payload = pickle.dumps(msg)
        self.socket.sendto(payload, address)

    def recv(self):
        """ Retrieve msg payload and from address."""
        try:
            payload, addr = self.socket.recvfrom(1024)
        except socket.timeout:
            return None, None

        if len(payload) == 0:
            return None, addr
        return payload, addr

    def node_join(self, args):
        """Process JOIN_REQ message.

        Parameters:
            args (dict): addr and id of the node trying to join
        """

        self.logger.debug("Node join: %s", args)
        addr = args["addr"]
        identification = args["id"]
        if self.identification == self.successor_id: # Now the node is not alone!")
            self.successor_id = identification
            self.successor_addr = addr
            self.predecessor_id = identification    # REFACTORED
            self.predecessor_addr = addr            # REFACTORED
            #TODO update finger table
            self.finger_table.update(1, identification, addr)
            args = {"successor_id": self.identification, "successor_addr": self.addr}
            self.send(addr, {"method": "JOIN_REP", "args": args})

        elif contains(self.identification, self.successor_id, identification): # he will be my successor
            # I need to send him my successor and change it to him
            args = {
                "successor_id": self.successor_id,
                "successor_addr": self.successor_addr,
            }
            self.successor_id = identification
            self.successor_addr = addr
            #TODO update finger table
            self.finger_table.update(1, identification, addr)
            self.send(addr, {"method": "JOIN_REP", "args": args})
        
        else: # REFACTORED
            # Redirect to the closest preceding node
            nextNode_address = self.finger_table.find(identification)
            self.logger.debug("Find Successor of (%d) - Redirect", identification)
            self.logger.debug(self)
            self.send(nextNode_address, {"method": "JOIN_REQ", "args": args})     
            
        self.logger.info(self)

    def get_successor(self, args):
        """Process SUCCESSOR message.

        Parameters:
            args (dict): addr and id of the node asking
        """

        self.logger.debug("Get successor: %s", args)
        #TODO Implement processing of SUCCESSOR message
        
        if contains(self.predecessor_id, self.identification, args["id"]):
            msg = {"method": "SUCCESSOR_REP", 
                   "args": {
                       "req_id": args["id"],
                       "successor_id": self.identification,
                       "successor_addr": self.addr
                       }
                    }
            self.logger.debug("Get successor - Done: "+ str(msg["args"]))
            self.send(args["from"], msg)
        else:
            msg = {"method": "SUCCESSOR", 
                   "args": {
                       "id": args["id"],
                       "from": args["from"]
                       }
                    }
            self.logger.debug("Get successor - Redirect: "+ str(msg["args"]))
            self.send(self.successor_addr, msg)
            self.logger.debug(self)
                
    def notify(self, args):
        """Process NOTIFY message.
            Updates predecessor pointers.

        Parameters:
            args (dict): id and addr of the predecessor node
        """

        self.logger.debug("Notify: %s", args)
        if self.predecessor_id is None or contains(
            self.predecessor_id, self.identification, args["predecessor_id"]
        ):
            # new predecessor
            self.predecessor_id = args["predecessor_id"]
            self.predecessor_addr = args["predecessor_addr"]
            # REFACTORED - Move data to new predecessor
            for key, value in list(self.keystore.items()):
                hash_key = dht_hash(key)
                if not contains(self.predecessor_id, self.identification, dht_hash(key)):
                    self.logger.info("Required - Move data: %s", hash_key)
                    msg = {"method": "PUT", "args": {"key": key, "value": value}}
                    self.send(self.predecessor_addr, msg)
                    payload, addr = self.recv()
                    if payload is not None:
                        out = pickle.loads(payload)
                        if out["method"] == "ACK":
                            self.keystore.pop(key)
                            self.logger.critical("Moved data: %s [%s -> %s]", hash_key, self.identification, self.predecessor_id)

        self.logger.info(self)

    def stabilize(self, from_id, addr):
        """Process STABILIZE protocol.
            Updates all successor pointers.

        Parameters:
            from_id: id of the predecessor of node with address addr
            addr: address of the node sending stabilize message
        """

        self.logger.debug("Stabilize: %s %s", from_id, addr)
        # from_id is the id of the predecessor of node with address addr, it must be me...
        if from_id is not None and contains(
            self.identification, self.successor_id, from_id
        ):  
            # Not me ..., update our successor
            self.successor_id = from_id
            self.successor_addr = addr
            #TODO update finger table
            self.finger_table.update(1, self.successor_id, self.successor_addr)

        # notify successor of our existence (the correct one!), so it can update its predecessor record
        args = {"predecessor_id": self.identification, "predecessor_addr": self.addr}
        self.send(self.successor_addr, {"method": "NOTIFY", "args": args})

        # TODO refresh finger_table
        refreshed_list = self.finger_table.refresh()
        for node in refreshed_list:
            self.send(node[2],{"method": "SUCCESSOR", 'args': {"id": node[1], "from": self.addr}})

    def put(self, key, value, address):
        """Store value in DHT.

        Parameters:
        key: key of the data
        value: data to be stored
        address: address where to send ack/nack
        """
        key_hash = dht_hash(key)
        self.logger.debug("Put: %s %s", key, key_hash)

        #TODO Replace next code:
        
        if contains(self.predecessor_id, self.identification , key_hash):
            # key_hash between me and my predecessor (i have responsibility to store)
            if key in self.keystore:
                self.logger.error("Put-Error: %s %s", key, key_hash)
                self.send(address, {"method": "NACK"})
                self.logger.debug(self)
            else:
                self.keystore[key] = value
                self.logger.debug("Put-Done: %s %s", key, key_hash)
                self.send(address, {"method": "ACK"})
                self.logger.debug(self)
                
        else:
            # key_hash in one of the next nodes
            msg = {"method": "PUT", "args": {"key": key, "value": value, "from": address}}
            self.logger.debug("Put-Redirect: %s", msg["args"]) 
            self.send(self.finger_table.find(key_hash), msg)
            self.logger.debug(self)
              
                
             
        

    def get(self, key, address):
        """Retrieve value from DHT.

        Parameters:
        key: key of the data
        address: address where to send ack/nack
        """
        key_hash = dht_hash(key)
        self.logger.debug("Get: %s %s", key, key_hash)

        #TODO Replace next code:
        
        if contains(self.predecessor_id, self.identification , key_hash):
            # key_hash between me and my predecessor (i have responsibility to store)
            if not key in self.keystore:
                self.logger.error("Get-Error: %s %s", key, key_hash)
                self.send(address, {"method": "NACK"})
                self.logger.debug(self)
            else:
                value = self.keystore[key]
                self.logger.debug("Get-Done: %s %s", key, key_hash)
                self.send(address, {"method": "ACK", "args": value})
                self.logger.debug(self)
                
        else:
            # key_hash in one of the next nodes
            msg = {"method": "GET", "args": {"key": key, "from": address}}
            self.logger.debug("Get-Redirect: %s", msg["args"])   
            self.send(self.finger_table.find(key_hash), msg)
            self.logger.debug(self)

    def leave(self):
        """Leave the DHT."""
        self.logger.critical("Node leaving")
        for key, value in list(self.keystore.items()):
            hash_key = dht_hash(key)
            self.logger.info("Required - Move data: %s", hash_key)
            msg = {"method": "PUT", "args": {"key": key, "value": value}}
            self.send(self.predecessor_addr, msg)
            payload, addr = self.recv()
            if payload is not None:
                out = pickle.loads(payload)
                if out["method"] == "ACK":
                    self.keystore.pop(key)
                    self.logger.critical("Moved data: %s [%s -> %s]", hash_key, self.identification, self.predecessor_id)
        self.done = True

    def run(self):
        self.socket.bind(self.addr)

        # Loop until joining the DHT
        while not self.inside_dht: # Process of joining an existing DHT
            join_msg = {
                "method": "JOIN_REQ",
                "args": {"addr": self.addr, "id": self.identification},
            }
            self.send(self.dht_address, join_msg) # Send to root node
            payload, addr = self.recv()
            if payload is not None:
                output = pickle.loads(payload)
                self.logger.debug("O: %s", output)
                if output["method"] == "JOIN_REP": # Joining the DHT
                    args = output["args"]
                    self.successor_id = args["successor_id"]
                    self.successor_addr = args["successor_addr"]
                    self.predecessor_id = args["successor_id"]      # REFACTORED
                    self.predecessor_addr = args["successor_addr"]  # REFACTORED
                    self.logger.debug(f"Joined DHT: {self.identification}")
                    self.inside_dht = True
                    #TODO fill finger table       
                    self.finger_table.fill(self.successor_id, self.successor_addr)             
                    args = {"predecessor_id": self.identification, "predecessor_addr": self.addr}
                    self.send(self.successor_addr, {"method": "NOTIFY", "args": args})
                    

        # Enter the DHT
        while not self.done:
            payload, addr = self.recv()
            if payload is not None:
                output = pickle.loads(payload)
                self.logger.info("O: %s", output)
                if output["method"] == "JOIN_REQ":
                    self.node_join(output["args"])
                elif output["method"] == "NOTIFY":
                    self.notify(output["args"])
                elif output["method"] == "PUT":
                    self.put(
                        output["args"]["key"],
                        output["args"]["value"],
                        output["args"].get("from", addr),
                    )
                elif output["method"] == "GET":
                    self.get(output["args"]["key"], output["args"].get("from", addr))
                elif output["method"] == "PREDECESSOR":
                    # Reply with predecessor id
                    self.send(
                        addr, {"method": "STABILIZE", "args": self.predecessor_id}
                    )
                elif output["method"] == "SUCCESSOR":
                    # Reply with successor of id
                    self.get_successor(output["args"])
                elif output["method"] == "STABILIZE":
                    # Initiate stabilize protocol
                    self.stabilize(output["args"], addr)
                elif output["method"] == "SUCCESSOR_REP":
                    #TODO Implement processing of SUCCESSOR_REP
                    request_id = output["args"]["req_id"]
                    successor_id = output["args"]["successor_id"]
                    successor_addr = output["args"]["successor_addr"]

                    index = self.finger_table.getIdxFromId(request_id)
                    self.finger_table.update(index, successor_id, successor_addr)

            else:  # timeout occurred, lets run the stabilize algorithm
                # Ask successor for predecessor, to start the stabilize process
                self.send(self.successor_addr, {"method": "PREDECESSOR"})
                self.logger.debug(self)

    def __str__(self): # REFACTORED
        ft = self.finger_table.table
        if (ft is not None):
            ft = [item[0] for item in self.finger_table.table]
        return "ID: {}; Successor: {}; Predecessor: {}; FingerTable: {}".format(
            self.identification,
            self.successor_id,
            self.predecessor_id,
            ft,
        )

    def __repr__(self):
        return self.__str__()


# REFACTORED
# Custom logging formatter
class CustomFormatter(logging.Formatter):

    colors = {
        'DEBUG': '\x1b[38;20m',   # Gray
        'INFO': '\x1b[38;20m',    # Gray
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[1;31m'  # Dark Red
    }

    reset = '\033[0m'
    fmt = '%(name)s %(levelname)-8s %(message)s'

    def format(self, record):
        color = self.colors.get(record.levelname, self.reset)
        formatter = logging.Formatter(color + self.fmt + self.reset)
        return formatter.format(record)

    def setup(self, logger):
        logger.propagate = False
        
        if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(self)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(console_handler)