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
        """ Initialize Finger Table.
        
        Parameters:
        - node_id: The identifier of the node owning this FingerTable.
        - node_addr: The address of the node owning this FingerTable.
        - m_bits: The number of bits in the CHORD identifier space.
        """
        self.node_id = node_id
        self.node_addr = node_addr
        self.m_bits = m_bits

        # Initialize the finger table with m_bits entries.
        # Each entry is a tuple (node_id, node_addr) initially pointing to the node itself.
        self.table = [(node_id, node_addr) for _ in range(m_bits)]


    def fill(self, node_id, node_addr):
        """ Fill all entries of the finger table with node_id, node_addr.
        Parameters:
        - node_id: The identifier of a node.
        - node_addr: The address of a node.
        """
        for i in range(self.m_bits):
            self.table[i] = (node_id, node_addr)

    def update(self, index, node_id, node_addr):
        """Update index of table with node_id and node_addr.
            
            Parameters:
            - index: The 0-based index in the FingerTable to update.
            - node_id: The ID of the node to point this entry to.
            - node_addr: The address of the node to point this entry to.
            """

        if 1 <= index <= len(self.table):
            self.table[index-1] = (node_id, node_addr) # Adjust for 0-based indexing in Python lists
        else:
            raise IndexError("FingerTable index out of range.")

    def find(self, identification):
        """ Get node address of closest preceding node (in finger table) of identification. """
        # Iterate in reverse through the finger table to find the highest entry that precedes the given identification.

        for i in range(self.m_bits - 1, -1, -1):
            node_id, node_addr = self.table[i]
            # Check if the current finger entry's node id precedes the identification.
            # We use self.node_id as the start point to ensure the found node is preceding.
            if contains(node_id, self.node_id, identification):
                return node_addr
            
        # If no preceding node is found in the finger table (which is unlikely but could happen due to incomplete initialization or updates), default to returning the successor address.
        return self.table[0][1]

    def refresh(self):
        """ Retrieve finger table entries requiring refresh."""
        refreshList = []

        for i in range(self.m_bits):
            index = i + 1 
            node = (self.node_id + 2 ** i) % (2 ** self.m_bits)
            address = self.table[i][1]
            refreshList.append((index,node,address))

        return refreshList

    def getIdxFromId(self, id):
        """Return index in the finger table by id.
    
        This method searches for the first occurrence of the given node ID in the finger table
        and returns the index of that entry. If the ID is not found in the table, it returns None.

        Parameters:
        - id: The identifier of the node to search for in the finger table.
        
        Returns:
        The 0-based index of the finger table entry that contains the given node ID, or None if not found.
        """
        temp = (id - self.node_id) % (2 ** self.m_bits)
        # for index, (node_id, _) in enumerate(self.table):
        #     if node_id == id:
        #         return index + 1           
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
            # I have no predecessor! (it my cause an error...)
            self.predecessor_id = None
            self.predecessor_addr = None
        else:
            self.inside_dht = False
            self.successor_id = None
            self.successor_addr = None
            self.predecessor_id = None
            self.predecessor_addr = None

        self.finger_table = FingerTable(self.identification,self.addr)    #TODO create finger_table

        self.keystore = {}  # Where all data is stored
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.logger = logging.getLogger("Node {}".format(self.identification))

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
        if self.identification == self.successor_id:  # I'm the only node in the DHT
            self.successor_id = identification
            self.successor_addr = addr
            ########################################################################
            #TODO update finger table
            self.finger_table.fill(self.identification, self.addr)
            ########################################################################
            args = {"successor_id": self.identification, "successor_addr": self.addr}
            self.send(addr, {"method": "JOIN_REP", "args": args})
        elif contains(self.identification, self.successor_id, identification):
            args = {
                "successor_id": self.successor_id,
                "successor_addr": self.successor_addr,
            }
            self.successor_id = identification
            self.successor_addr = addr
            ########################################################################
            #TODO update finger table
            self.finger_table.fill(self.successor_id, self.successor_addr)
            ########################################################################
            self.send(addr, {"method": "JOIN_REP", "args": args})
        else:
            self.logger.debug("Find Successor(%d)", args["id"])
            self.send(self.successor_addr, {"method": "JOIN_REQ", "args": args})
        self.logger.info(self)

    def get_successor(self, args):
        """Process SUCCESSOR message.

        Parameters:
            args (dict): addr and id of the node asking
        """

        self.logger.debug("Get successor: %s", args)
        #TODO Implement processing of SUCCESSOR message
        
        if self.predecessor_id is None:
            self.logger.debug("Not stabilized yet!")
            return
        
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
            #TODO DON'T FORGOT TO MOVE THE DATA WHEN ADDING AN NEW NODE!
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
            self.table.update(2 ** 0, self.successor_id, self.successor_addr)
            #self.table.update(2 ** 0, self.successor_id, self.successor_addr) # fingerTable[0] -> sucessor

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
        if self.predecessor_id is None:
            self.logger.debug("Not stabilized yet!")
            self.send(address, {"method": "NACK"})
            return
        
        if contains(self.predecessor_id, self.identification , key_hash):
            # key_hash between me and my predecessor (i have responsibility to store)
            if key in self.keystore:
                self.logger.debug("Put-Error: %s %s", key, key_hash)
                self.send(address, {"method": "NACK"})
            else:
                self.keystore[key] = value
                self.logger.debug("Put-Done: %s %s", key, key_hash)
                self.send(address, {"method": "ACK"})
                
        else:
            # key_hash in one of the next nodes
            msg = {"method": "PUT", "args": {"key": key, "value": value, "from": address}}
            self.logger.debug("Put-Redirect: %s", msg["args"]) 
            self.send(self.finger_table.find(key_hash), msg)
              
                
             
        

    def get(self, key, address):
        """Retrieve value from DHT.

        Parameters:
        key: key of the data
        address: address where to send ack/nack
        """
        key_hash = dht_hash(key)
        self.logger.debug("Get: %s %s", key, key_hash)

        #TODO Replace next code:
        if self.predecessor_id is None:
            self.logger.debug("Not stabilized yet!")
            self.send(address, {"method": "NACK"})
            return
        
        if contains(self.predecessor_id, self.identification , key_hash):
            # key_hash between me and my predecessor (i have responsibility to store)
            if not key in self.keystore:
                self.logger.debug("Get-Error: %s %s", key, key_hash)
                self.send(address, {"method": "NACK"})
            else:
                value = self.keystore[key]
                self.logger.debug("Get-Done: %s %s", key, key_hash)
                self.send(address, {"method": "ACK", "args": value})
                
        else:
            # key_hash in one of the next nodes
            msg = {"method": "GET", "args": {"key": key, "from": address}}
            self.logger.debug("Get-Redirect: %s", msg["args"])   
            self.send(self.finger_table.find(key_hash), msg)
              

    def run(self):
        self.socket.bind(self.addr)

        # Loop until joining the DHT
        while not self.inside_dht: # Process of joining an existing DHT
            join_msg = {
                "method": "JOIN_REQ",
                "args": {"addr": self.addr, "id": self.identification},
            }
            self.send(self.dht_address, join_msg) # Send to initial node
            payload, addr = self.recv()
            if payload is not None:
                output = pickle.loads(payload)
                self.logger.debug("O: %s", output)
                if output["method"] == "JOIN_REP": # Joining the DHT
                    args = output["args"]
                    self.successor_id = args["successor_id"]
                    self.successor_addr = args["successor_addr"]
                    #TODO fill finger table
                    self.inside_dht = True
                    self.logger.info(self)

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
                     
                    pass
            else:  # timeout occurred, lets run the stabilize algorithm
                # Ask successor for predecessor, to start the stabilize process
                self.send(self.successor_addr, {"method": "PREDECESSOR"})

    def __str__(self):
        return "Node ID: {}; DHT: {}; Successor: {}; Predecessor: {}; FingerTable: {}".format(
            self.identification,
            self.inside_dht,
            self.successor_id,
            self.predecessor_id,
            self.finger_table,
        )

    def __repr__(self):
        return self.__str__()
