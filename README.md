<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
# Load Balancer

Very simples HTTP/TCP Load Balancer.
Implemented in Python3, single thread, using OS selector.
The code contains 4 classes that implement different strategies to select the next back-end server:

1. **N to 1:** all the requests are routed to a single server
2. **Round Robin:** the requests are routed to all servers in sequence
3. **Least Connections:** the request is routed to the server with fewer active connections
4. **Least Response Time:** the request is routed to the server with less average execution time

At the moment only the first strategy is fully implemented.

## Back-end server

The back-end server was implemented with [flask](http://flask.pocoo.org/).
It provides a simple service that computes the number Pi with a certain precision.

## Prerequisites

```console
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r requirements.txt
```

## How to run

```console
$ source venv/bin/activate
$ ./setup.sh
```

In another terminal
```console
$ curl -s http://localhost:8080/10
```

Or use a browser to open
```console
http://localhost:8080/10
```


## How to access the load balancer

Go to a browser and open this [link](http://localhost:8080/100).
The number after the URL specifies the precision of the computation.

## How to Stress Test

```console
$ ./stress_test.sh
```

Alternative
```console
$ httperf --server=localhost --port=8080 --uri=/100 --num-conns=100 --rate=5
```

## Git Upstream

```console
$ git remote add upstream git@github.com:detiuaveiro/load-balancer.git
$ git fetch upstream
$ git checkout master
$ git merge upstream/master
```

## Authors

* **Mário Antunes** - [mariolpantunes](https://github.com/mariolpantunes)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
=======
=======
=======
>>>>>>> cecd2bc (Initial commit)
=======
>>>>>>> b7420fd (add deadline)
[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/EhIYAyWc)
>>>>>>> 2332a21 (add deadline)
## Tests:

run `pytest`


## Diagram:

```https://www.websequencediagrams.com
title Message Broker

note left of Consumer: Connection estabilished
Consumer->Broker: Announce Serialization Mechanism

note left of Consumer: Can subscribe to topics any time

Consumer->Broker: Subscribe to topic X
Broker->Consumer: Send Last saved message in X

note right of Broker: List just the topic names

Consumer->Broker: Request list of all topics
Broker->Consumer: Response list of all topics

note left of Producer: Connection estabilished

Producer -> Broker: Announce Serialization Mechanism
Producer -> Broker: Publish message to topic X

Broker ->Consumer: Send message to consumer
Consumer -> Broker: Cancel topic X subscription

Producer -> Broker: Publish message to topic X
note left of Consumer: Doesn't receive last message
```



<<<<<<< HEAD
>>>>>>> 4333182 (Initial commit)
=======
=======
=======
[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/YQHnUjoB)
>>>>>>> 4a055c8 (add deadline)
# CHORD (DHT)

This repository implement a simple version of the [CHORD](https://en.wikipedia.org/wiki/Chord_(peer-to-peer)) algorithm.
The provided code already setups the ring network properly.
1. Supports Node Joins
2. Finds the correct successor for a node
3. Run Stabilize periodically to correct the network


## Running the example
Run in two different terminal:

DHT (setups a CHORD DHT):
```console
$ python3 DHT.py
```
example (put and get objects from the DHT):
```console
$ python3 DHTClient.py
```

## References

[original paper](https://pdos.csail.mit.edu/papers/ton:chord/paper-ton.pdf)

## Authors

* **Mário Antunes** - [mariolpantunes](https://github.com/mariolpantunes)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
>>>>>>> dca85de (Initial commit)
>>>>>>> cecd2bc (Initial commit)
