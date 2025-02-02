import logging
import time
import sys
import argparse
from DHTNode import DHTNode


def main(number_nodes, timeout):
    """ Script to launch several DHT nodes. """

    # logger for the main
    logger = logging.getLogger("DHT")
    # list with all the nodes
    dht = []
    # initial node on DHT
    node = DHTNode(("localhost", 5000))
    node.start() # start function run()
    dht.append(node)
    logger.info(f"Join Request: {node.identification}")

    for i in range(number_nodes - 1):
        time.sleep(0.2)
        # Create DHT_Node threads on ports 5001++ 
        # DHT_Node on port 5000 is the initial node !!
        node = DHTNode(("localhost", 5001 + i), ("localhost", 5000), timeout)
        node.start() # thread start
        dht.append(node)
        logger.info(f"Join Request: {node.identification}")

    # Await for DHT to get stable
    time.sleep(10)

    # Await for all nodes to stop
    for node in dht:
        node.join() # thread waiting



if __name__ == "__main__":
    # Launch DHT with 5 Nodes

    parser = argparse.ArgumentParser()
    parser.add_argument("--savelog", default=False, action="store_true")
    parser.add_argument("--nodes", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=3)
    args = parser.parse_args()

    logfile = {}
    if args.savelog:
        logfile = {"filename":"dht.txt", "filemode": "w"}

    logging.basicConfig(
            level=logging.DEBUG,
            format="\033[93m%(name)-10s %(levelname)-8s %(message)s\033[0m",
            datefmt="%m-%d %H:%M:%S",
            **logfile
        )


    main(args.nodes, timeout=args.timeout)
