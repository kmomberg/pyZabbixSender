# -*- coding: utf-8
# Copyright 2015 Kurt Momberg <kurtqm (at) yahoo(dot)com(dot)ar>
# > Based on work by Klimenko Artyem <aklim007(at)gmail(dot)com>
# >> Based on work by Rob Cherry <zsend(at)lxrb(dot)com>
# >>> Based on work by Enrico Tröger <enrico(dot)troeger(at)uvena(dot)de>
# License: GNU GPLv2

import socket
import struct
import time
import sys
import re

# If you're using an old version of python that don't have json available,
# you can use simplejson instead: https://simplejson.readthedocs.org/en/latest/
#import simplejson as json
import json


class pyZabbixSender:
    '''
    This class allows you to send data to a Zabbix server, using the same
    protocol used by the zabbix_server binary
    distributed by Zabbix.
    '''
    ZABBIX_SERVER = "127.0.0.1"
    ZABBIX_PORT   = 10051

    # Return codes when sending data:
    RC_OK            =   0  # Everything ok
    RC_ERR_FAIL_SEND =   1  # Error reported by zabbix when sending data
    RC_ERR_PARS_RESP =   2  # Error parsing server response
    RC_ERR_CONN      = 255  # Error talking to the server
    RC_ERR_INV_RESP  = 254  # Invalid response from server

    def __init__(self, server=ZABBIX_SERVER, port=ZABBIX_PORT, verbose=False):
        '''
        Constructor. You can specify hostname/IP and port of your zabbix server.
        Defaults are "127.0.0.1" and 10051.
        The "verbose" parameter is to print all sending failures to stderr.
        '''
        self.zserver = server
        self.zport   = port
        self.verbose = verbose
        self.timeout = 5         # Socket connection timeout.
        self.data = []           # This is to store data when calling the "add_data" method.


    def add_data(self, host, key, value, clock=None):
        '''
        Adds host, key, value and optionally clock to the internal list of
        data to be sent later.
        '''
        obj = self.__create_data_obj(host, key, value, clock)
        self.data.append(obj)


    def __create_data_obj(self, host, key, value, clock=None):
        '''
        Based on parameters, this creates a dictionary containing
        the same data.
        '''
        obj = {
            'host': host,
            'key': key,
            'value': value,
        }
        if clock:
            obj['clock'] = clock
        return obj


    def print_vals(self):
        '''
        Print stored data, that will be sent if "send" is called.
        '''
        for elem in self.data:
            print str(elem)
        print 'Count: %d' % len(self.data)


    def send(self, packet_clock=None, max_data_per_conn=None):
        '''
        Sends data stored using "add_data" method, to the zabbix server.
        Zabbix server uses the "clock" parameter in the packet to
        associate that timestamp to all data values not containing
        its own clock.
        If packet_clock is specified, zabbix server will associate it to
        all data values not containing its own clock.
        If packet_clock is NOT specified, zabbix server will use the time
        when it received the packet as packet clock.
        You can use "int(round(time.time()))" to generate a current
        timestamp "clock".
        The parameter "max_data_per_conn" allows the user to limit the
        number of data points sent in one single connection, as some times
        a too big number can produce problems over slow connections.
        Several "sends" will be automatically performed until all data is sent.

        Please note that internal data is not deleted after "send" is
        executed. You need to call "clear_data" after sending it, if you
        want to.

        Return:  a list of (return_code, msg_from_server) associated to each send.
        '''
        if not max_data_per_conn or max_data_per_conn > len(self.data):
            max_data_per_conn = len(self.data)

        responses = []
        i = 0
        while i*max_data_per_conn < len(self.data):

            sender_data = {
                "request": "sender data",
                "data": [],
            }
            if packet_clock:
                sender_data['clock'] = packet_clock

            sender_data['data'] = self.data[i*max_data_per_conn:(i+1)*max_data_per_conn]
            to_send = json.dumps(sender_data)

            response = self.__send(to_send)
            responses.append(response)
            i += 1

        return responses


    def send_single(self, host, key, value, clock=None):
        '''
        Instead of sending all stored data, you can use this method to
        send specific values, one by one.
        '''
        sender_data = {
            "request": "sender data",
            "data": [],
        }

        obj = self.__create_data_obj(host, key, value, clock)
        sender_data['data'].append(obj)
        to_send = json.dumps(sender_data)
        return self.__send(to_send)


    def __send(self, mydata):
        '''
        This is the method that actually sends the data to the zabbix server.
        '''
        socket.setdefaulttimeout(self.timeout)
        data_length = len(mydata)
        data_header = str(struct.pack('q', data_length))
        data_to_send = 'ZBXD\1' + str(data_header) + str(mydata)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.zserver, self.zport))
            sock.send(data_to_send)
        except Exception, err:
            err_message = u'Error talking to server: %s\n' %str(err)
            sys.stderr.write(err_message)
            return self.RC_ERR_CONN, err_message

        response_header = sock.recv(5)
        if not response_header == 'ZBXD\1':
            err_message = u'Invalid response from server. Malformed data?\n---\n%s\n---\n' % str(mydata)
            sys.stderr.write(err_message)
            return self.RC_ERR_INV_RESP, err_message

        response_data_header = sock.recv(8)
        response_data_header = response_data_header[:4]
        response_len = struct.unpack('i', response_data_header)[0]
        response_raw = sock.recv(response_len)
        sock.close()
        response = json.loads(response_raw)
        match = re.match('^.*failed.+?(\d+).*$', response['info'].lower() if 'info' in response else '')
        if match is None:
            err_message = u'Unable to parse server response - \n%s\n' % str(response)
            sys.stderr.write(err_message)
            return self.RC_ERR_PARS_RESP, response
        else:
            fails = int(match.group(1))
            if fails > 0:
                if self.verbose is True:
                    err_message = u'Failures reported by zabbix when sending:\n%s\n' % str(mydata)
                    sys.stderr.write(err_message)
                return self.RC_ERR_FAIL_SEND, response
        return self.RC_OK, response


    def iter_send(self):
        '''
        You can use this method to send all stored data, one by one, to
        determine which traps are not being handled correctly by the server.
        It returns an array of return codes and the data sent.
        '''
        retarray = []
        for i in self.data:
            if 'clock' in i:
                (retcode, retstring) = self.send_single(i['host'], i['key'], i['value'], i['clock'])
            else:
                (retcode, retstring) = self.send_single(i['host'], i['key'], i['value'])

            retarray.append((retcode, i))
        return retarray


    def clear_data(self):
        '''
        This method deletes all data added using the method "add_data",
        so you can start adding again from zero.
        '''
        self.data = []


# ####################################
# --- Examples of usage ---
#####################################
#
# Initiating a pyZabbixSender object -
# z = pyZabbixSender() # Defaults to using ZABBIX_SERVER,ZABBIX_PORT
# z = pyZabbixSender(verbose=True) # Prints all sending failures to stderr
# z = pyZabbixSender(server="172.0.0.100",verbose=True)
# z = pyZabbixSender(server="zabbix-server",port=10051)
# z = pyZabbixSender("zabbix-server", 10051)

# --- Adding data to send later ---
# Host, Key, Value are all necessary
# z.add_data("test_host","test_trap","12")
#
# Optionally you can provide a specific timestamp for the sample
# z.add_data("test_host","test_trap","13",1365787627)
#
# If you provide no timestamp, you still can assign one when sending, or let
# zabbix server to put the timestamp when the message is received.

# --- Printing values ---
# Not that useful, but if you would like to see your data in tuple form:
# z.print_vals()

# --- Sending data ---
#
# Just sending a single data point (you don't need to call add_value for this
# to work):
# z.send_single("test_host","test_trap","12")
#
# Sending everything at once, with no concern about
# individual item failure -
#
# result = z.send()
# for r in result:
#     print "Result: %s -> %s" % (str(r[0]), r[1])
#
# If you're ok with the result, you can delete the data inside the sender, to
# allow a new round of data feed/send.
# z.clear_data()
#
# If you want to specify a timestamp to all values without one, you can specify
# the packet_clock parameter:
# z.send(packet_clock=1365787627)
#
# When you're sending data over a slow connection, you may find useful the
# possibility to send data in packets with no more than max_data_per_conn
# data points on it.
# All the data will be sent, but in smaller packets.
# For example, if you want to send 4000 data points in packets containing no
# more than 200 of them:
#
# results = z.send(max_data_per_conn=200)
# for partial_result in results:
#     print partial_result
#
# Sending every item individually so that we can capture
# success or failure
#
# results = z.iter_send()
# for (code,data) in results:
#   if code == 1:
#      print "Failed to send: %s" % str(data)
#
#
#####################################
# Mini example of a working program #
#####################################
#
# import sys
# sys.path.append("/path/to/pyZabbixSender.py")
# from pyZabbixSender import pyZabbixSender
#
# z = pyZabbixSender() # Defaults to using ZABBIX_SERVER,ZABBIX_PORT
# z.add_data("test_host","test_trap_1","12")
# z.add_data("test_host","test_trap_2","13",1366033479)
# z.print_vals()
#
# results = z.iter_send()
# for (code,data) in results:
#   if code == 1:
#      print "Failed to send: %s" % str(data)
# z.clear_data
#####################################