#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module/Script docstring

"""

__author__ = 'Christopher Espy'

import argparse
import logging
import paho.mqtt.client as mqtt
from flask import Flask, render_template
import sqlite3


app = Flask(__name__)


def parse_agruments(args):
    """The argument parser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', help='set logging trace level to debug', action='store_true')
    return parser.parse_args(args)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("test_home_readings")
    client.subscribe("cellar_fan_power_status")
    client.subscribe("temp_cellar_front")
    client.subscribe("hum_cellar_front")
    client.subscribe("temp_cellar_back")
    client.subscribe("hum_cellar_back")
    client.subscribe("temp_patio")
    client.subscribe("hum_patio")
    client.subscribe("temp_patio")
    client.subscribe("hum_patio")
    client.subscribe("temperature_office")
    client.subscribe("humidity_office")


# The callback for when a PUBLISH message is received from the ESP8266.
def on_message(client, userdata, message):
    if 1:
        # print("Sensor Reading Update")
        # print("\t", message.topic)
        # print(message.payload.json())
        # print(dhtreadings_json['temperature'])
        # print(dhtreadings_json['humidity'])

        # dhtreadings_json = json.loads(message.payload)

        # connects to SQLite database. File is named "sensordata.db" without the quotes
        # WARNING: your database file should be in the same directory of the app.py file or have the correct path
        conn=sqlite3.connect('sensorreadings.db')
        c=conn.cursor()

        c.execute("""INSERT INTO sensorreadings (currentdate,
            currenttime, device, reading) VALUES(date('now'),
            time('now'), (?), (?))""", (message.topic,
            float(message.payload)) )

        conn.commit()
        conn.close()


mqttc=mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect("localhost",1883,60)
mqttc.loop_start()


@app.route("/")
def main(argv=None):
    """The main function"""
    arguments = parse_agruments(argv)

    if arguments.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # connects to SQLite database. File is named "sensordata.db" without the quotes
    # WARNING: your database file should be in the same directory of the app.py file or have the correct path
    conn = sqlite3.connect('sensorreadings.db')
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute("SELECT * FROM sensorreadings ORDER BY id DESC LIMIT 20")
    readings = c.fetchall()
    # print(readings)
    return render_template('main.html', readings=readings)


if __name__ == '__main__':
    import sys

    app.run(host='0.0.0.0', port=8181, debug=True)

    sys.exit(main(sys.argv[1:]))
