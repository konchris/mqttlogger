#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module/Script docstring

"""

__author__ = 'Christopher Espy'

from sqlalchemy import Column, Integer, Date, Time, Text, Float

from mqttlogger.base import Base


class SensorReading(Base):
    __tablename__ = "sensorreadings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    currentdate = Column(Date)
    currenttime = Column(Time)
    device = Column(Text)
    reading = Column(Float)

    def __repr__(self):
        return f"<Reading: {self.currentdate}T{self.currenttime} - {self.device} - {self.reading}>"
