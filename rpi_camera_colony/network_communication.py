# -*- coding: utf-8 -*-
#
# Author: Lars B. Rollik <L.B.Rollik@protonmail.com>
# License: BSD 3-Clause
import logging
from threading import Thread

import numpy as np
import zmq
from tornado import ioloop
from zmq.eventloop.zmqstream import ZMQStream
from zmq.utils.strtypes import b

allowed_zmq_patterns = {
    "REQ": zmq.REQ,
    "REP": zmq.REP,
    "PUB": zmq.PUB,
    "SUB": zmq.SUB,
}


def find_available_port(
    start_port=None,
    ip_address=None,
    protocol="tcp",
    allowed_port_range=10,
    pattern="PUB",
):
    """Check safely if chosen port range is available."""
    start_port = int(start_port)
    c = zmq.Context()

    available_port = None
    while available_port is None and start_port <= start_port + allowed_port_range:
        try:
            s = c.socket(allowed_zmq_patterns[pattern])
            s.bind(f"{protocol}://{ip_address}:{start_port}")
            available_port = start_port
            s.close()
        except zmq.ZMQError:
            start_port += 1
            continue

    c.term()
    return available_port


class SocketCommunication:
    """ZMQ command_socket wrapper that offers multiple patterns and high-level interfaces to message serialisation."""

    context = None
    socket = None

    full_address = None
    pattern = "PUB"
    bind_bool = True
    subscribe_to = ""

    def __init__(
        self,
        protocol="tcp",
        address="127.0.0.1",
        port=12345,
        pattern="PUB",
        bind=True,
        subscribe_to="",
        auto_open=True,
    ):
        """
        :param protocol: protocols accepted by ZMQ, e.g. TCP
        :param address: IP address
        :param port: Port number
        :param pattern: Allowed values are: REQ, REP, PUB, SUB, while others might also work
        :param bind: If true, binds to address, else connects it
        :param subscribe_to: Subscription string for topic. If is list, subscribes to topics iteratively.
        """
        protocol = protocol.split(":")[
            0
        ]  # only first part is protocol and will be sufixed with ://

        if address.lower() == "localhost":
            address = "127.0.0.1"

        self.full_address = f"{protocol}://{address}:{port}"
        self.pattern = pattern.upper()
        self.bind_bool = bind
        self.subscribe_to = subscribe_to

        if auto_open:
            self.open()

    def open(self, force_open=False):
        logging.debug(
            f"{'Binding' if self.bind_bool else 'Connecting'} {self.pattern} socket on {self.full_address}."
        )

        if self.context is not None and not self.socket.closed:
            if not force_open:
                logging.debug(
                    "Already open. Not allowed to close and re-open. Use 'force_open=True' in call to open()"
                )
                return
            else:
                self.close()
                logging.debug(f"Trying to re-open connection on {self.full_address}")

        # OPENING
        self.context = zmq.Context()
        self.socket = self.context.socket(allowed_zmq_patterns.get(self.pattern))
        if self.bind_bool:
            self.socket.bind(self.full_address)
        else:
            self.socket.connect(self.full_address)

        if "SUB" in self.pattern:
            logging.debug(
                f"Subscribing to: '{self.subscribe_to}' on {self.full_address}"
            )
            if not isinstance(self.subscribe_to, list):
                self.socket.subscribe(b(self.subscribe_to))
            else:
                for topic in self.subscribe_to:
                    self.socket.subscribe(b(topic))

    def send_json(self, object=None):
        self.socket.send_json(obj=dict(object))

    def recv_json(self, *args, **kwargs):
        return self.socket.recv_json(*args, **kwargs)

    def recv_multipart(self):
        return self.socket.recv_multipart()

    def send_multipart(self, topic="", message=""):
        msg_parts = [b(part) for part in [topic, message]]
        return self.socket.send_multipart(msg_parts=msg_parts)

    def send_multipart_json(self, recipient="", message=None, flags=0):
        if not isinstance(message, dict):
            logging.warning(f"Message is type {type(message)}, but has to be dict.")
            return False

        self.socket.send(b(recipient), flags=flags | zmq.SNDMORE)
        return self.socket.send_json(obj=message, flags=flags)

    def send_array(self, array=None, metadata=None, flags=0, copy=True, track=False):
        """send a numpy array with metadata"""
        metadata_to_send = dict(
            dtype=str(array.dtype),
            shape=array.shape,
        )
        if isinstance(metadata, dict):
            metadata_to_send.update(metadata)

        self.socket.send_json(metadata_to_send, flags | zmq.SNDMORE)
        return self.socket.send(array, flags, copy=copy, track=track)

    def recv_array(self, flags=0, copy=True, track=False):
        """recv a numpy array"""
        received_metadata = self.socket.recv_json(flags=flags)
        data_segment = self.socket.recv(flags=flags, copy=copy, track=track)
        buf = memoryview(data_segment)
        received_array = np.frombuffer(buf, dtype=received_metadata["dtype"])
        return received_array.reshape(received_metadata["shape"])

    def recv_array_with_metadata(self, flags=0, copy=True, track=False):
        """recv a numpy array, plus additional metadata"""
        received_metadata = self.socket.recv_json(flags=flags)
        data_segment = self.socket.recv(flags=flags, copy=copy, track=track)
        buf = memoryview(data_segment)
        received_array = np.frombuffer(buf, dtype=received_metadata["dtype"])
        return received_metadata, received_array.reshape(received_metadata["shape"])

    def close(self):
        if self.socket is not None and not self.socket.closed:
            self.socket.close()
            self.socket = None
            logging.debug(f"Socket closed for {self.full_address}")

        if self.context is not None:
            self.context.term()
            self.context = None
            logging.debug(f"Context closed for {self.full_address}")

    def __del__(self):
        try:
            self.close()
        except zmq.ZMQBaseError:
            logging.warning(
                f"ZMQBaseError on closing of command_socket/context of {self.full_address}"
            )
        except BaseException:
            logging.warning(f"Unknown error on del of {self.full_address}")


class ListenerStream(Thread):
    """Bundle ZMQ sockets and streams with shared event loop in thread for non-blocking callback."""

    socket_dict = {}
    stream_dict = {}
    recv_callback_input = None
    recv_callback_dict = {}
    ioloop = None
    daemon = True

    def __init__(self, socket_dict: dict, recv_callback_dict: (dict, None)):
        """
        :param socket_dict: dict of ZMQ command_socket objects
        :param recv_callback_dict: dict of functions to call on event on the sockets
        or a single function handle that will be used for each command_socket like the dict would be.
        """
        super(ListenerStream, self).__init__()

        self.socket_dict = socket_dict
        self.recv_callback_input = recv_callback_dict

        if self.recv_callback_input is None:
            logging.warning(
                "No stream recv_callbacks defined! Settings all callbacks to None"
            )
            for socket_name, _ in socket_dict.items():
                self.recv_callback_dict[socket_name] = None

        if callable(self.recv_callback_input):
            logging.debug(
                f"Only one callback defined. Setting to same: {recv_callback_dict}"
            )
            for socket_name, _ in socket_dict.items():
                self.recv_callback_dict[socket_name] = self.recv_callback_input

        for socket_name, socket_handle in socket_dict.items():
            new_stream = ZMQStream(socket=socket_handle)
            new_stream.on_recv(callback=self.recv_callback_dict[socket_name])
            self.stream_dict[socket_name] = new_stream

        self.ioloop = ioloop.IOLoop.instance()

    def run(self):
        self.ioloop.start()

    def stop(self):
        for s, h in self.stream_dict.items():
            h.on_recv = None
            h.close(0)

        # self.ioloop.stop()
        # self.ioloop.clear_current()
        # self.ioloop = None
