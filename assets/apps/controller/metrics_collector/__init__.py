import sqlite3
from flask import Flask, request, g, jsonify

from scaling_controller.consts import DB_PATH, INSERT_VALUE

app = Flask(__name__)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route("/")
def hello():
    return "Metrics Collector"


@app.route("/put/<string:instance>/<string:metric>", methods=['PUT'])
def put_metric(instance, metric):
    data = request.json
    c = get_db().cursor()
    c.execute(
        INSERT_VALUE,
        (instance, data['timestamp'], metric, data['value'])
    )
    get_db().commit()
    c.close()
    return jsonify({'status': 'ok'})
