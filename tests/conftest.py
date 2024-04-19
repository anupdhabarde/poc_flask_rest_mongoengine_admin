import mongomock
import pytest
from mongoengine import connect, disconnect

from poc import create_app


@pytest.fixture(scope="session", autouse=True)
def app():
    flask_app = create_app({"TESTING": True})

    return flask_app


@pytest.fixture(autouse=True)
def mongo():
    connect("mongoenginetest", host="mongodb://localhost", mongo_client_class=mongomock.MongoClient)
    yield
    disconnect()
