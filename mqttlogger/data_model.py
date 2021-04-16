#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module/Script docstring

"""

__author__ = 'Christopher Espy'

# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
#
# app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqldb://mqttlogger:REDACTED_DB_PASS@192.168.1.14:3306/sensorreadings"
# # app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////Users/chris/Programming/MQTTLogger/data/sensorreadings.db"
# db = SQLAlchemy(app)


class SensorReading(db.Model):
    __tablename__ = "sensorreadings"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    currentdate = db.Column(db.Date)
    currenttime = db.Column(db.Time)
    device = db.Column(db.Text)
    reading = db.Column(db.Float)

    def __repr__(self):
        return f"Reading: {self.currentdate}:{self.currenttime} - {self.device} - {self.reading}"
