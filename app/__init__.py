"""Subscription Tracker - minimal Flask API backed by SQLite."""
#creating Flash App, setting up DB path
import os

from flask import Flask

from app import db
from app.routes import bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get("DATABASE_PATH", "/data/subscriptions.db"),
    )
    if test_config:
        app.config.update(test_config)

    #prod would use RDS or DyanomoDB
    db.init_app(app)
    app.register_blueprint(bp)
    return app
