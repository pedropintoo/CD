<<<<<<< HEAD
"""Test simple consumer/producer interaction."""
import json
import pickle
import random
import string
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from src.clients import Consumer, Producer
from src.middleware import JSONQueue, PickleQueue, XMLQueue

TOPIC = "".join(random.sample(string.ascii_lowercase, 6))


def gen():
    while True:
        yield random.randint(0, 100)


@pytest.fixture
def consumer_JSON():
    consumer = Consumer(TOPIC, JSONQueue)

    thread = threading.Thread(target=consumer.run, daemon=True)
    thread.start()
    return consumer


@pytest.fixture
def consumer_Pickle():
    consumer = Consumer(TOPIC, PickleQueue)

    thread = threading.Thread(target=consumer.run, daemon=True)
    thread.start()
    return consumer


@pytest.fixture
def consumer_XML():
    consumer = Consumer(TOPIC, XMLQueue)

    thread = threading.Thread(target=consumer.run, daemon=True)
    thread.start()
    return consumer


@pytest.fixture
def producer_JSON():

    producer = Producer(TOPIC, gen, PickleQueue)

    producer.run(1)
    return producer


def test_simple_producer_consumer(consumer_JSON, broker):

    producer = Producer(TOPIC, gen, JSONQueue)

    with patch("json.dumps", MagicMock(side_effect=json.dumps)) as json_dump:
        with patch("pickle.dumps", MagicMock(side_effect=pickle.dumps)) as pickle_dump:

            producer.run(10)
            assert pickle_dump.call_count == 0
            assert json_dump.call_count >= 10  # at least 10 JSON messages

    time.sleep(0.1)  # wait for messages to propagate through the broker to the clients

    assert consumer_JSON.received == producer.produced

    assert broker.list_topics() == [TOPIC]


def test_multiple_consumers(consumer_JSON, consumer_Pickle, consumer_XML, broker):

    prev = list(consumer_JSON.received)  # consumer gets previously stored element

    producer = Producer(TOPIC, gen, PickleQueue)

    producer.run(9)  # iterate only 9 times, consumer iterates 9 + 1 historic
    time.sleep(0.1)  # wait for messages to propagate through the broker to the clients

    assert consumer_JSON.received == prev + producer.produced
    assert consumer_Pickle.received == consumer_JSON.received
    assert consumer_Pickle.received == [
        int(v) for v in consumer_XML.received
    ]  # XML only transfers strings, so we cast here into int for comparison

    assert broker.list_topics() == [TOPIC]


def test_broker(producer_JSON, broker):
    time.sleep(0.1)  # wait for messages to propagate through the broker to the clients

    assert broker.list_topics() == [TOPIC]

    assert broker.get_topic(TOPIC) == producer_JSON.produced[-1]
=======
"""Tests two clients."""
import pytest
<<<<<<< HEAD
from DHTClient import DHTClient


@pytest.fixture()
def client():
    return DHTClient(("localhost", 5000))


def test_put_local(client):
    """ add object to DHT (this key is in first node -> local search) """
    assert client.put("A", [0, 1, 2])


def test_get_local(client):
    """ retrieve from DHT (this key is in first node -> local search) """
    assert client.get("A") == [0, 1, 2]


def test_put_remote(client):
    """ add object to DHT (this key is not on the first node -> remote search) """
    assert client.put("2", ("xpto"))


def test_get_remote(client):
    """ retrieve from DHT (this key is not on the first node -> remote search) """
    assert client.get("2") == "xpto"
<<<<<<< HEAD
>>>>>>> dca85de (Initial commit)
=======
=======
import pexpect

TIMEOUT = 2


@pytest.fixture
def foo():
    foo = pexpect.spawnu("python3 foo.py")
    time.sleep(1)

    assert foo.isalive()
    yield foo

    if foo.isalive():
        foo.sendline("exit")
        foo.close()


@pytest.fixture
def bar():
    bar = pexpect.spawnu("python3 bar.py")
    time.sleep(1)

    assert bar.isalive()
    yield bar

    if bar.isalive():
        bar.sendline("exit")
        bar.close()


def test_hello(foo, bar):
    foo.sendline("Olá Mundo")

    bar.expect("Olá Mundo", timeout=TIMEOUT)
    bar.sendline("Hello World")

    foo.expect("Hello World", timeout=TIMEOUT)


def test_storm(foo, bar):
    foo.sendline("Olá Mundo")

    bar.expect("Olá Mundo", timeout=TIMEOUT)
    bar.sendline("Hello World")
    bar.sendline("How are you?")
    bar.sendline("Are you new around here?")
    bar.sendline("Hope you enjoy your stay")

    foo.expect("Hope you enjoy your stay", timeout=TIMEOUT)
    foo.sendline("You are awesome!")
    foo.expect("You are awesome!", timeout=TIMEOUT)

    bar.expect("You are awesome!", timeout=TIMEOUT)


def test_basic(foo, bar):
    foo.sendline("Hello!")
    bar.expect("Hello!", timeout=TIMEOUT)
    bar.sendline("Welcome aboard")
    bar.sendline("Who are you?")
    foo.expect("Who are you?", timeout=TIMEOUT)
    foo.sendline("I'm Joe")
    bar.expect("Joe", timeout=TIMEOUT)
    bar.sendline("Nice to meet you Joe")
    foo.sendline("Cya around")

    foo.expect("Cya around")
    bar.expect("Cya around")


def test_extra(foo, bar):
    foo.sendline("Hello!")
    bar.expect("Hello!", timeout=TIMEOUT)
    foo.sendline("/join #cd")
    foo.sendline("no one is here...")
    with pytest.raises(pexpect.exceptions.TIMEOUT):
        bar.expect("no one is here", timeout=TIMEOUT)


def test_channels(foo, bar):
    foo.sendline("/join #c1")
    bar.sendline("/join #c2")
    foo.sendline("Hello darkness, my old friend")
    foo.sendline("/join #c2")
    foo.sendline("I've come to talk with you again")
    bar.expect("I've come to talk with you again")
    foo.sendline("/join #c1")
    foo.sendline("Because a vision softly creeping")
    with pytest.raises(pexpect.exceptions.TIMEOUT):
        bar.expect("Because a vision softly creeping", timeout=TIMEOUT)
>>>>>>> bc77e07 (Initial commit)
>>>>>>> 6c5ad68 (Initial commit)
