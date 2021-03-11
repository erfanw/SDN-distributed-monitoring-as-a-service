#!/usr/bin/env python3

import json
import requests
from flask import Flask, jsonify, request
from flask_influxdb import InfluxDB
from influxdb.exceptions import InfluxDBClientError

app = Flask(__name__)

# Configure InfluxDB host, port, database, etc.
app.config.from_pyfile('example.cfg')
app.config.update(SESSION_COOKIE_NAME='dbsession')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
influx_db = InfluxDB(app=app)


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/<dbname>', methods=['POST'])
def write(dbname):
    """Writes points to a database.

    Parses the request body as JSON that contains points and writes them 
    into the database specified. The request body should a list of points
    which contain "fields", "tags", and "measurement". For example:
    [
        {
            "fields": {"value_1": 0.5, "value_2": 1, "value_3": 1.8858},
            "tags": {"tag_1": "tag_string1", "tag_2": "tag_string2"},
            "measurement": "testseries"
        }
    ]

    Args:
        dbname (str): A string of the name of the database selected. 

    Returns:
        A list of points that are written into the database as JSON
        format.
    """
    try:
        influx_db.database.switch(database=dbname)
        points = request.get_json(force=True)
        influx_db.write_points(points)
        return jsonify(points)
    except InfluxDBClientError as e:
        print(e)
        return str(e), 404, {"Content-Type":"text/html"}


@app.route('/<dbname>/<measurement>', methods=['GET'])
def selectAll(dbname, measurement):
    """Selects all points in a measurement.

    Args:
        dbname (str): A string of the name of the database selected.
        measurement (str): A string of the name of the measurement. 

    Returns:
        A list of all points in a measurement as JSON format.
    """
    try:
        influx_db.database.switch(database=dbname)
        table = influx_db.query("SELECT * FROM {0}".format(measurement))
        points = []
        for p in table.get_points():
            points.append(p)
        return jsonify(points)
    except InfluxDBClientError as e:
        print(e)
        return str(e), 404, {"Content-Type":"text/html"}


@app.route('/<dbname>/<measurement>/last', methods=['GET'])
def selectLast(dbname, measurement):
    """Selects the last point in a measurement.

    Args:
        dbname (str): A string of the name of the database selected.
        measurement (str): A string of the name of the measurement. 

    Returns:
        A dictionary of the last point in a measurement as JSON format.
    """
    try:
        influx_db.database.switch(database=dbname)
        table_last = influx_db.query(
            "SELECT * FROM {0} ORDER BY time DESC LIMIT 1"
            .format(measurement))
        point_last = next(table_last.get_points())
        return jsonify(point_last)
    except InfluxDBClientError as e:
        print(e)
        return str(e), 404, {"Content-Type":"text/html"}


@app.route('/<dbname>/<measurement>/last_second', methods=['GET'])
def selectLastSecond(dbname, measurement):
    """Selects all points in the last second.

    Args:
        dbname (str): A string of the name of the database selected.
        measurement (str): A string of the name of the measurement. 

    Returns:
        A list of all points in the last second as JSON format.
    """
    try:
        last = selectLast(dbname, measurement)
        info = json.loads(last.get_data())
        time = info["time"]

        influx_db.database.switch(database=dbname)
        table = influx_db.query(
            "SELECT * FROM {0} WHERE time >= '{1}' - 1s"
            .format(measurement, time))
        points = []
        for p in table.get_points():
            points.append(p)
        return jsonify(points)
    except InfluxDBClientError as e:
        print(e)
        return str(e), 404, {"Content-Type":"text/html"}
    

@app.route('/<dbname>/<measurement>', methods=['DELETE'])
def delete(dbname, measurement):
    """Deletes a measurement from a database.

    Args:
        dbname (str): A string of the name of the database selected.
        measurement (str): A string of the name of the measurement to
            be deleted.

    Returns:
        A list of names of the measurements left in the database as JSON
        format.
    """
    try:
        influx_db.database.switch(database=dbname)
        influx_db.measurement.drop(measurement=measurement)
        measurements_all = influx_db.measurement.all()
        measurements_list = []
        for m in measurements_all:
            measurements_list.append(m[u'name'])
        return jsonify(measurements_list)
    except InfluxDBClientError as e:
        print(e)
        return str(e), 404, {"Content-Type":"text/html"}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
