


import sys
import os
os.environ["FLASK_ENV"] = "testing"
os.environ["TESTING"] = "1"
os.environ["SOCKETIO_ASYNC_MODE"] = "threading"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from flask import Flask
from flask_socketio import SocketIO, emit

from app import create_app
from app.config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def socketio(app):
    return app.socketio

def test_join_leave_stream(app, socketio):
    stream_id = 'teststream123'
    namespace = '/live'
    client = socketio.test_client(app, namespace=namespace)
    assert client.is_connected(namespace)
    # Join
    client.emit('join_stream', {'stream_id': stream_id}, namespace=namespace)
    received = client.get_received(namespace)
    assert any(r['name'] == 'viewer_update' for r in received)
    # Leave (Event wird gesendet, aber Client empfängt es nicht mehr, weil er aus dem Room entfernt wurde)
    client.emit('leave_stream', {'stream_id': stream_id}, namespace=namespace)
    client.disconnect(namespace)

def test_send_message(app, socketio):
    stream_id = 'teststream456'
    namespace = '/live'
    message = 'Hello World!'
    client = socketio.test_client(app, namespace=namespace)
    assert client.is_connected(namespace)
    # Erst join_stream, dann send_message mit user_id und username
    client.emit('join_stream', {'stream_id': stream_id}, namespace=namespace)
    client.get_received(namespace)
    client.emit('send_message', {'stream_id': stream_id, 'message': message, 'user_id': 42, 'username': 'testuser'}, namespace=namespace)
    received = client.get_received(namespace)
    assert any(r['name'] == 'new_message' for r in received)
    client.disconnect(namespace)

def test_send_like(app, socketio):
    stream_id = 'teststream789'
    namespace = '/live'
    client = socketio.test_client(app, namespace=namespace)
    assert client.is_connected(namespace)
    client.emit('join_stream', {'stream_id': stream_id}, namespace=namespace)
    client.get_received(namespace)
    client.emit('send_like', {'stream_id': stream_id, 'user_id': 42}, namespace=namespace)
    received = client.get_received(namespace)
    assert any(r['name'] == 'new_like' for r in received)
    client.disconnect(namespace)

def test_send_gift(app, socketio):
    stream_id = 'teststream999'
    namespace = '/live'
    client = socketio.test_client(app, namespace=namespace)
    assert client.is_connected(namespace)
    client.emit('join_stream', {'stream_id': stream_id}, namespace=namespace)
    client.get_received(namespace)
    client.emit('send_gift', {'stream_id': stream_id, 'gift_type': 'rose', 'amount': 1, 'user_id': 42, 'username': 'testuser'}, namespace=namespace)
    received = client.get_received(namespace)
    assert any(r['name'] == 'new_gift' for r in received)
    client.disconnect(namespace)
