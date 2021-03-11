# DM APIs README

This is a README documentation for `dm_api.py`. It contains serveral RESTful APIs for InfluxDB including writing data, deleting measurements, selecting all points in a measurement, etc.

## Set-up

Use the package manager `pip3` to install Flask, InfluxDB-Python, and Flask_InfluxDB.

```bash

pip3 install -r requirements.txt

```

Run `dm_api.py` to start Flask server. The default port for Flask is 5000.

```bash
chmod +x dm_api.py
./dm_api.py
```

## Usage

Before calling the APIs, make sure to configure Flask and InfluxDB in `example.cfg`. By default debug mode is set `True` for Flask.

### `write(dbname)`

Write points to a database. It parses the request body as JSON that contains points and writes them into the database specified. The request body should be a list of points which contain "fields", "tags", and "measurement". For example:

```json
[
    {
        "fields": {"value_1": 1.1, "value_2": 2, "value_3": 1.34},
        "tags": {"tag_1": "tag_string1", "tag_2": "tag_string2"},
        "measurement": "testseries"
    },
    {
        "fields": {"value_1": 1.5, "value_2": 6, "value_3": 1.78},
        "tags": {"tag_1": "tag_string1", "tag_2": "tag_string2"},
        "measurement": "testseries"
    }
]
```

To use this API, send a `POST` request to `http://localhost:5000/<dbname>` with the request body of a list of points.

Parameters:
- `dbname` (str): The name of the database selected. 

Returns:
- A list of points that are written into the database as JSON format. If an error occurs, return that error in string with status code 404 instead. 

### `selectAll(dbname, measurement)`

Select all points in a measurement in the format of JSON string. To use this API, send a `GET` request to `http://localhost:5000/<dbname>/<measurement>`.

Parameters:
- `dbname` (str): The name of the database selected. 
- `measurement` (str): The name of the measurement selected.

Returns:
- A list of all points in a measurement as JSON format. If an error occurs, return that error in string with status code 404 instead. Successful request example:

    ```json
    [
        {
            "time":"2020-09-19T20:38:15.360308Z",
            "tag_1":"tag_string1",
            "tag_2":"tag_string2",
            "value_1":0.5,
            "value_2":1,
            "value_3":1.8858
        },
        {
            "time":"2020-09-19T20:38:37.620786Z",
            "tag_1":"tag_string1",
            "tag_2":"tag_string2",
            "value_1":1.2,
            "value_2":2,
            "value_3":0.1238
        }
    ]
    ```

### `selectLast(dbname, measurement)`

Select the last point in a measurement in the format of JSON string. To use this API, send a `GET` request to `http://localhost:5000/<dbname>/<measurement>/last`.

Parameters:
- `dbname` (str): The name of the database selected. 
- `measurement` (str): The name of the measurement selected.

Returns:
- A dict of the last point in a measurement as JSON format. If an error occurs, return that error in string with status code 404 instead. Successful request example:

    ```json
    {
        "time":"2020-09-19T20:38:37.620786Z",
        "tag_1":"tag_string1",
        "tag_2":"tag_string2",
        "value_1":1.2,
        "value_2":2,
        "value_3":0.1238
    }
    ```

### `selectLastSecond(dbname, measurement)`

Select all points in the last second of a measurement in the format of JSON string. To use this API, send a `GET` request to `http://localhost:5000/<dbname>/<measurement>/last_second`.

Parameters:
- `dbname` (str): The name of the database selected. 
- `measurement` (str): The name of the measurement selected.

Returns:
- A list of all points in the last second of a measurement as JSON format. If an error occurs, return that error in string with status code 404 instead. Successful request example:

    ```json
    [
        {
            "time":"2020-09-19T20:38:15.360308Z",
            "tag_1":"tag_string1",
            "tag_2":"tag_string2",
            "value_1":0.5,
            "value_2":1,
            "value_3":1.8858
        },
        {
            "time":"2020-09-19T20:38:15.620786Z",
            "tag_1":"tag_string1",
            "tag_2":"tag_string2",
            "value_1":1.2,
            "value_2":2,
            "value_3":0.1238
        }
    ]
    ```
    
### `delete(dbname, measurement)`

Delete a measurement from a database. To use this API, send a `DELETE` request to `http://localhost:5000/<dbname>/<measurement>`.

Parameters: 
- `dbname` (str): The name of the database selected. 
- `measurement` (str): The name of the measurement to be deleted.

Returns:
- A list of names of the measurements left in the database as JSON format. If an error occurs, return that error in string with status code 404 instead. Successful request example:

    ```json
    [
        "test0",
        "test1",
        "testseries"
    ]
    ```
