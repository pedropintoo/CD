# coding: utf-8

import socket
import selectors
import signal
import logging
import argparse
import time

# configure logger output format
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Load Balancer')


# used to stop the infinity loop
done = False

sel = selectors.DefaultSelector()

policy = None
mapper = None


# implements a graceful shutdown
def graceful_shutdown(signalNumber, frame):  
    logger.debug('Graceful Shutdown...')
    global done
    done = True


# n to 1 policy
class N2One:
    def __init__(self, servers):
        self.servers = servers  

    def select_server(self):
        return self.servers[0]

    def update(self, *arg):
        pass


# round robin policy
class RoundRobin:
    def __init__(self, servers):
        self.servers = servers
        self.actual_index = -1
        self.number_of_servers = len(servers)

    def select_server(self):
        # Each request is sent to the next server in the list. Once it reaches the last one, it returns to the first.
        # We'll use arithmetical modulo to achieve this.
        self.actual_index = (self.actual_index + 1) % self.number_of_servers 
        server = self.servers[self.actual_index]
        return server
    
    def update(self, *arg):
        pass


# least connections policy
class LeastConnections:
    def __init__(self, servers):
        self.servers = servers
        self.connections = {server: 0 for server in servers} # dictionary to keep track of the number of active connections for each server

    def select_server(self):
        # Selects the next server that currently has the fewest active connections.
        server = min(self.connections, key=self.connections.get)
        self.connections[server] += 1 # increment the number of active connections for the selected server
        return server

    def update(self, *arg):
        if len(arg) < 1:
            raise ValueError("No server specified for update")
    
        # decrement the active connection count for the given server because the connection has been closed.
        server = arg[0]
        if self.connections[server] > 0:
            self.connections[server] -= 1  


# least response time
class LeastResponseTime:
    def __init__(self, servers):
        self.servers = servers
        
        # Dictionary to keep track of the average response time for each server
        self.average_response = {server: 0 for server in servers}
        
        # Dictionary to keep track of the initial time request for each server
        self.initial_time_request = {server: 0 for server in servers}
        
        # To keep track of the response times
        self.response_times = {server: [] for server in servers}


    def select_server(self):
        current_time = time.time()
        # Adjust the average response time dynamically based on the time elapsed since the last request
        for server in self.servers:
            elapsed_time = self.initial_time_request[server] - current_time
            self.average_response[server] = (sum(self.response_times[server]) + elapsed_time) / (len(self.response_times[server]) + 1)
        
        # Find the server with the minimum adjusted average response time
        server = min(self.average_response, key=self.average_response.get)
        self.initial_time_request[server] = time.time()  # Update the initial time for the chosen server
        return server

    def update(self, *arg):
        # Updates the average response time for the given server.
        if len(arg) < 1:
            raise ValueError("No server specified for update")

        server = arg[0]
        
        # Calculates the new response time
        response_time = time.time() - self.initial_time_request[server]
        self.response_times[server].append(response_time)  # Add the response time to the list

        # Update count and calculate new average response time
        count = len(self.response_times[server])
        self.average_response[server] = sum(self.response_times[server]) / count


POLICIES = {
    "N2One": N2One,
    "RoundRobin": RoundRobin,
    "LeastConnections": LeastConnections,
    "LeastResponseTime": LeastResponseTime
}

class SocketMapper:
    def __init__(self, policy):
        self.policy = policy
        self.map = {}

    def add(self, client_sock, upstream_server):
        client_sock.setblocking(False)
        sel.register(client_sock, selectors.EVENT_READ, read)
        upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream_sock.connect(upstream_server)
        upstream_sock.setblocking(False)
        sel.register(upstream_sock, selectors.EVENT_READ, read)
        logger.debug("Proxying to %s %s", *upstream_server)
        self.map[client_sock] =  upstream_sock

    def delete(self, sock):
        paired_sock = self.get_sock(sock)
        sel.unregister(sock)
        sock.close()
        sel.unregister(paired_sock)
        paired_sock.close()
        if sock in self.map:
            self.map.pop(sock)
        else:
            self.map.pop(paired_sock)

    def get_sock(self, sock):
        for client, upstream in self.map.items():
            if upstream == sock:
                return client
            if client == sock:
                return upstream
        return None
    
    def get_upstream_sock(self, sock):
        return self.map.get(sock)

    def get_all_socks(self):
        """ Flatten all sockets into a list"""
        return list(sum(self.map.items(), ())) 

def accept(sock, mask):
    client, addr = sock.accept()
    logger.debug("Accepted connection %s %s", *addr)
    mapper.add(client, policy.select_server())

def read(conn,mask):
    data = conn.recv(4096)
    if len(data) == 0: # No messages in socket, we can close down the socket
        mapper.delete(conn)
    else:
        mapper.get_sock(conn).send(data)


def main(addr, servers, policy_class):
    global policy
    global mapper

    # register handler for interruption 
    # it stops the infinite loop gracefully
    signal.signal(signal.SIGINT, graceful_shutdown)

    policy = policy_class(servers)
    mapper = SocketMapper(policy)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(addr)
    sock.listen()
    sock.setblocking(False)

    sel.register(sock, selectors.EVENT_READ, accept)

    try:
        logger.debug("Listening on %s %s", *addr)
        while not done:
            events = sel.select(timeout=1)
            for key, mask in events:
                if(key.fileobj.fileno()>0):
                    callback = key.data
                    callback(key.fileobj, mask)
                
    except Exception as err:
        logger.error(err)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pi HTTP server')
    parser.add_argument('-a', dest='policy', choices=POLICIES)
    parser.add_argument('-p', dest='port', type=int, help='load balancer port', default=8080)
    parser.add_argument('-s', dest='servers', nargs='+', type=int, help='list of servers ports')
    args = parser.parse_args()
    
    servers = [('localhost', p) for p in args.servers]
    
    main(('127.0.0.1', args.port), servers, POLICIES[args.policy])
