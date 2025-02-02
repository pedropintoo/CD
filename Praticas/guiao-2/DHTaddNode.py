""" Chord DHT kill node implementation. """
import logging
import time
from os import sys
from utils import dht_hash, contains
from DHTNode import DHTNode

ROOT_NODE = 5000

def main():

    if len(sys.argv) != 3:
        print("Usage: python3 DHTkillNode.py <id_min> <id_max>")
        sys.exit(1)

    id_min = int(sys.argv[1]) 
    id_max = int(sys.argv[2]) 
    port = None

    for p in range(5100, 10000):
        if id_min < dht_hash(("localhost",p).__str__()) < id_max:
            port = p
            break
        
    if port is not None:
        generateNode(port)
    else:
        print("Cannot found... increase the range of ports.")    


def generateNode(port):
    """ Generate a DHT node with the given port. """

    # logger for the main
    logger = logging.getLogger("DHT") 

    node = DHTNode(("localhost", port), ("localhost", ROOT_NODE))
    node.start() # start function run()
    logger.info(f"Join Request: {node.identification}")


    node.join()
    
       



if __name__ == "__main__":
    main()