#!/usr/bin/env python

import argparse
from datetime import datetime
import json
import random
import requests
import socket
import sys
import time
import graphitesend
from influxdb import InfluxDBClient

#Function to send data to graphite
def send_data_graphite(schema, backend_addr, backend_port, beeping_return):
    g = graphitesend.init(graphite_server=backend_addr,
                          graphite_port=backend_port,
                          lowercase_metric_names=True,
                          system_name='', prefix='')
    for i in beeping_return:
        if type(beeping_return[i]) == int: g.send(schema+"."+i, beeping_return[i])

#Function to send data to influxdb
def send_data_influxdb(backend_addr, backend_port, beeping_return, backend_user,
                       bakend_pwd, backend_db):
    client = InfluxDBClient(backend_addr, backend_port, backend_user,
                            backend_pwd, backend_db)
    current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    client.write_points([{
        "measurement": "http_status",
        "tags": {"host": payload["url"], "region": ""},
        "time": current_time,
        "fields": {"value": beeping_return["http_status_code"]}
    }])
    client.write_points([{
        "measurement": "http_request_time",
        "tags": {"host": payload["url"], "region": ""},
        "time": current_time,
        "fields": {"value": beeping_return["http_request_time"]}
    }])
    client.write_points([{
        "measurement": "dns_lookup",
        "tags": {"host": payload["url"], "region": ""},
        "time": current_time,
        "fields": {"value": beeping_return["dns_lookup"]}
    }])
    client.write_points([{
        "measurement": "tcp_connection",
        "tags": {"host": payload["url"], "region": ""},
        "time": current_time,
        "fields": {"value": beeping_return["tcp_connection"]}
    }])
    client.write_points([{
        "measurement": "server_processing",
        "tags": {"host": payload["url"], "region": ""},
        "time": current_time,
        "fields": {"value": beeping_return["server_processing"]}
    }])
    client.write_points([{
        "measurement": "content_transfer",
        "tags": {"host": payload["url"], "region": ""},
        "time": current_time,
        "fields": {"value": beeping_return["content_transfer"]}
    }])

    if beeping_return["ssl"] == True:
        client.write_points([{
            "measurement": "tls_handshake",
            "tags": {"host": payload["url"], "region": ""},
            "time": current_time,
            "fields": {"value": beeping_return["tls_handshake"]}
        }])
        client.write_points([{
            "measurement": "ssl_days_left",
            "tags": {"host": payload["url"], "region": ""},
            "time": current_time,
            "fields": {"value": beeping_return["ssl_days_left"]}
        }])

#Variables declarations
cmd = ""
payload = {}

#Parsing arguments
parser = argparse.ArgumentParser(description='A Beeping client.', add_help=True)
parser.add_argument('-u', help='url to check', action='store', required=True)
parser.add_argument('-upmb', help='url of your beeping instance', required=True)
parser.add_argument('-p', help='pattern to check on the url', default="")
parser.add_argument('-i', action='store_true',
                    help='insecure mod (boolean true or false) just include the'
                         'parameter to pass it to True',
                    default=False)
parser.add_argument('-t', type=int,
                    help='time to respond to declare that the request timedout',
                    default=20)
parser.add_argument('-b',
                    help='backend to send your data, default is graphite',
                    default="graphite")
parser.add_argument('-s',
                    help='schema to stored your data in graphite\n for example:'
                         'customer.app.env.servername',
                    default="test.test.prod.host.beeping")
parser.add_argument('-H',
                    help='host of your backend, default is loaclhost',
                    default="localhost")
parser.add_argument('-P', type=int,
                    help='port of your backend, default is graphite port',
                    default=2003)
parser.add_argument('-U', help='user of your backend')
parser.add_argument('-pwd', help='password of your backend')
parser.add_argument('-db', help='name of your backedn db')

#Feeding variables
args = parser.parse_args()
url_beeping = args.upmb
payload["url"] = args.u
if args.p != "":
    payload["pattern"] = args.p
if args.i != False:
    payload["insecure"] = args.i
if args.t != 20:
    payload["timeout"] = args.t
backend = args.b
schema = args.s
backend_addr = args.H
backend_port = args.P
backend_db = args.db
backend_user = args.U
backend_pwd = args.pwd

#Open socket
#print json.dumps(payload)
r = requests.post(url_beeping, data=json.dumps(payload))
beeping_return = r.json()
if "message" in beeping_return:
    print beeping_return["message"]
    sys.exit(0)

if backend == "graphite":
    send_data_graphite(schema, backend_addr, backend_port, beeping_return)

if backend == "influxdb":
    send_data_influxdb(backend_addr, backend_port, beeping_return, backend_user,
                       bakend_pwd, backend_db)
