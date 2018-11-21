#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import time
import socket
import struct
import json
import message


class Client:
    MESSAGE_LENGTH_SIZE = 4
    BUFFER_SIZE = 1024

    DEFAULT_TCP_IP = '127.0.0.1'
    DEFAULT_TCP_PORT = 13000
    DEFAULT_TCP_FORWARD_PORT = 13001
    DEFAULT_NUM_CONNECTION_RETRIES = 12
    DEFAULT_CONNECTION_RETRY_TIMEOUT = 5

    def __init__(self, tcp_ip=DEFAULT_TCP_IP, tcp_port=DEFAULT_TCP_PORT):
        if tcp_ip is None:
            raise ValueError("tcp_ip cannot be None!")

        if tcp_port is None:
            raise ValueError("tcp_port cannot be None!")

        self.tcp_ip = tcp_ip
        self.tcp_port = tcp_port

    def connect(self, num_retries=DEFAULT_NUM_CONNECTION_RETRIES, timeout=DEFAULT_CONNECTION_RETRY_TIMEOUT):
        while num_retries > 0:
            try:
                logging.info("Connecting with ip: {0} and port: {1}".format(self.tcp_ip, self.tcp_port))
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.tcp_ip, self.tcp_port))
                break
            except Exception as e:
                logging.error(e)
                num_retries -= 1
                time.sleep(timeout)

        if num_retries <= 0:
            self.stop()
            raise Exception("Could not connect to server at {0}:{1}".format(self.tcp_ip, self.tcp_port))

    def stop(self):
        self.socket.shutdown(socket.SHUT_WR)
        self.socket.close()

    def read_message(self):
        """
        A blocking call that returns a full IMessage from the server.
        :return: Message
        """

        # Read content length...
        content_length_binary = self.socket.recv(self.MESSAGE_LENGTH_SIZE)

        while len(content_length_binary) < self.MESSAGE_LENGTH_SIZE:
            content_length_binary += self.socket.recv(self.MESSAGE_LENGTH_SIZE - len(content_length_binary))

        content_length = struct.unpack('>HH', content_length_binary)[1]

        # Read content in full...
        content_binary = self.socket.recv(self.BUFFER_SIZE)

        while len(content_binary) < content_length:
            content_binary += self.socket.recv(self.BUFFER_SIZE)

        msg = json.loads(content_binary)
        logging.info("Receive: {0}".format(msg))

        return msg

    def send_message(self, msg):
        """
        Serializes the message and sends to server.
        :param msg:
        :return: None
        """
        if msg is None:
            raise ValueError('message cannot be None!')

        if type(msg) is not message.Message:
            raise ValueError('message must be a type of Message')

        message_json = json.dumps(msg.__dict__)
        message_length = len(message_json)
        message_length_binary = struct.pack('>I', message_length)

        logging.info("Send: {0}".format(message_json))

        self.socket.send(message_length_binary)
        self.socket.send(message_json)
