#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module/Script docstring

"""

__author__ = 'Christopher Espy'

import logging

from sqlalchemy import Column, Integer, Date, Time, Text, Float, create_engine
from sqlalchemy.orm import declarative_base

from constants import ROOT_DIR
from mqttlogger.db_connection import create_connection_string

module_logger = logging.getLogger("mqttlogger.data_model")

Base = declarative_base()


class SensorReading(Base):
    __tablename__ = "sensorreadings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    currentdate = Column(Date)
    currenttime = Column(Time)
    device = Column(Text)
    reading = Column(Float)

    def __repr__(self):
        return f"<Reading: {self.currentdate}T{self.currenttime} - {self.device} - {self.reading}>"


def create():
    """

    Returns
    -------

    """

    db_conn_str = create_connection_string(ROOT_DIR / "config.json")

    engine = create_engine(db_conn_str)
    module_logger.debug(f"Successfully created engine: {engine.url}")
    Base.metadata.create_all(engine)
    module_logger.debug("Created all tables.")


if __name__ == "__main__":
    create()
