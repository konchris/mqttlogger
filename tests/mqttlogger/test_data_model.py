import datetime
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mqttlogger.data_model import Base, SensorReading

# --- SQLite in-memory (always runs) -------------------------------------------


@pytest.fixture(scope="module")
def sqlite_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_tablename():
    assert SensorReading.__tablename__ == "sensorreadings"


def test_repr_contains_device_and_reading():
    r = SensorReading(
        currentdate=datetime.date(2026, 5, 10),
        currenttime=datetime.time(12, 0, 0),
        device="environment/indoor/kitchen/temperature",
        reading=21.5,
    )
    text = repr(r)
    assert "kitchen/temperature" in text
    assert "21.5" in text


def test_commit_and_query(sqlite_session):
    r = SensorReading(
        currentdate=datetime.date(2026, 5, 10),
        currenttime=datetime.time(8, 30, 0),
        device="environment/indoor/bedroom/humidity",
        reading=55.0,
    )
    sqlite_session.add(r)
    sqlite_session.commit()
    result = (
        sqlite_session.query(SensorReading)
        .filter_by(device="environment/indoor/bedroom/humidity")
        .first()
    )
    assert result is not None
    assert result.reading == 55.0


def test_id_is_autoincrement(sqlite_session):
    r1 = SensorReading(
        currentdate=datetime.date(2026, 5, 10),
        currenttime=datetime.time(9, 0, 0),
        device="environment/outdoor/patio/temperature",
        reading=18.0,
    )
    r2 = SensorReading(
        currentdate=datetime.date(2026, 5, 10),
        currenttime=datetime.time(9, 5, 0),
        device="environment/outdoor/patio/temperature",
        reading=18.2,
    )
    sqlite_session.add_all([r1, r2])
    sqlite_session.commit()
    assert r1.id is not None
    assert r2.id is not None
    assert r1.id != r2.id


# --- MariaDB integration (runs in CI only) ------------------------------------


@pytest.fixture(scope="module")
def mariadb_session():
    host = os.environ.get("TEST_DB_HOST")
    if not host:
        pytest.skip("Requires MariaDB (set TEST_DB_HOST)")
    port = os.environ.get("TEST_DB_PORT", "3306")
    user = os.environ.get("TEST_DB_USER", "root")
    password = os.environ.get("TEST_DB_PASS", "")
    db = os.environ.get("TEST_DB_NAME", "mqttlogger_test")
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def test_mariadb_roundtrip(mariadb_session):
    r = SensorReading(
        currentdate=datetime.date(2026, 5, 10),
        currenttime=datetime.time(10, 0, 0),
        device="environment/indoor/attic/humidity",
        reading=72.3,
    )
    mariadb_session.add(r)
    mariadb_session.commit()
    result = (
        mariadb_session.query(SensorReading)
        .filter_by(device="environment/indoor/attic/humidity")
        .first()
    )
    assert result is not None
    assert result.reading == pytest.approx(72.3, rel=1e-3)
