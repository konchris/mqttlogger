#!/bin/python3
#
# Created by Rui Santos
# Complete project details: http://randomnerdtutorials.com
#

__author__ = "Christopher Espy"

# Built-In Libraries
import logging
from datetime import datetime

# Third-party libraries
import paho.mqtt.client as mqtt
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

# Local libraries
# from mqttlogger.data_model import SensorReading

# Create logging
logging.basicConfig(
    filename="mqttlogger.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"

)

LOG = logging.getLogger("mqttlogger")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqldb://mqttlogger:REDACTED_DB_PASS@192.168.1.14:3306/sensorreadings"
db = SQLAlchemy(app)


class SensorReading(db.Model):
    __tablename__ = "sensorreadings"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    currentdate = db.Column(db.Date)
    currenttime = db.Column(db.Time)
    device = db.Column(db.Text)
    reading = db.Column(db.Float)

    def __repr__(self):
        return f"Reading: {self.currentdate}:{self.currenttime} - {self.device} - {self.reading}"


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    LOG.debug("Connected with result code %s" % str(rc))
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
    client.subscribe("temperature/bedroom")
    client.subscribe("humidity/bedroom")


# The callback for when a PUBLISH message is received from the ESP8266.
def on_message(client, userdata, message):
    LOG.debug("Received message for topic:\n\t%s" % message.topic)
    if 1:

        if message.payload == b'true':
            message_payload = True
        elif message.payload == b'false':
            message_payload = False
        else:
            message_payload = message.payload

        new_reading = SensorReading(currentdate=datetime.now().strftime("%Y-%m-%d"),
                                    currenttime=datetime.now().strftime("%H:%M:%S"),
                                    device=message.topic,
                                    reading=float(message_payload))
        db.session.add(new_reading)
        LOG.debug(f"Adding new record to DB:\n\t{new_reading}")
        db.session.commit()


mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect("localhost", 1883, 60)
mqttc.loop_start()


@app.route("/")
def main():
    db.create_all()
    readings = SensorReading.query.order_by(SensorReading.id.desc()).limit(100)
    return render_template('main.html', readings=readings)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8181, debug=True)
