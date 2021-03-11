import os
import json
import requests

import pandas as pd
import numpy as np
import plotly
import plotly.graph_objs as go

from flask import Flask, render_template, url_for, jsonify, request
from flask_influxdb import InfluxDB
from influxdb.exceptions import InfluxDBClientError

import boxplot as bp


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
influx_db = InfluxDB(app=app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/statistics')
def statistics():
    return render_template('statistics.html')


# @app.route('/topology')
# def topology():
#     return render_template('topology.html')


@app.route('/clear-db')
def clear_db():
    try:
        influx_db.database.switch(database='mydb')
        influx_db.measurement.drop(measurement='links_bw')
        return "clear success", 200, {"Content-Type":"text/html"}
    except InfluxDBClientError as e:
        print(e)
        return str(e), 404, {"Content-Type":"text/html"}


@app.route('/create-box/<freq>')
def create_plot(freq):
    freq = int(freq)
    data_dict = bp.get_data(freq)

    data = []
    for time in data_dict:
        data.append(go.Box(
            name=time,
            y=data_dict[time],
            boxmean=True,
            marker=dict(
                    color='rgb(219, 64, 82)',
                    outliercolor='rgba(219, 64, 82, 0.6)',
                    line=dict(
                        outliercolor='rgba(219, 64, 82, 0.6)',
                        outlierwidth=2)),
            line_color='rgb(8,81,156)',
            fillcolor= 'rgba(159, 208, 237, 0.5)'
            )
        )

    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

@app.route('/clear-mininet')
def clear_mininet():
    sudopw = '128000'
    cmd = 'mn -c && rm nfm/cpm_dynamic.py'
    os.system('echo %s|sudo -S %s' % (sudopw, cmd))
    return 'Clear!'

@app.route('/start-controller')
def start_controller():
    os.system('make controller')
    return 'Start!'

@app.route('/start-mininet')
def start_mininet():
    sudopw = '128000'
    cmd = 'make test_st'
    os.system('echo %s|sudo -S %s' % (sudopw, cmd))
    return 'Start!'

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

@app.route('/<dbname>/<measurement>/last/<src>/<dst>', methods=['GET'])
def selectLastLink(dbname, measurement, src, dst):
    """Selects the last record of a specific link.

    Args:
        dbname (str): A string of the name of the database selected.
        measurement (str): A string of the name of the measurement. 
        src (int): The DPID of the source of the link.
        dst (int): The DPID of the destination of the link.

    Returns:
        A dictionary of the last record of the specific link as JSON format. 
        For example:
        ```json
        {
            "dst_port": "00000002",
            "dst_dpid": "0000000000000002",
            "last": 0.0,
            "src_port": "00000004",
            "src_dpid": "0000000000000004",
            "time": "2020-11-22T16:53:25.195772Z"
        }
        ```
    """
    try:
        influx_db.database.switch(database=dbname)
        query = influx_db.query(
            "SELECT LAST(bw), src_dpid, src_port, dst_dpid, dst_port FROM {0} WHERE src_dpid = '{1}' AND dst_dpid = '{2}'"
            .format(measurement, src, dst)
        )
        point = next(query.get_points())
        return jsonify(point)
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
    app.run(debug=True, host='0.0.0.0', port=5000)