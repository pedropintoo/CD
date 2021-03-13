"""Tests for the chat client."""
import pytest
from src.client import Client


def test_send_single_message():
    c = Client()
    assert c._host == "localhost"

    assert c.send_single_message() == "ECHO Hello, world"
