# This is only for testing influxDB

from influxdb import InfluxDBClient

client = InfluxDBClient(database="mydb")

table = client.query("SELECT * FROM testseries ORDER BY time DESC LIMIT 1")

points=[]

# for measurement, tags in table.keys():
#     for p in table.get_points(measurement=measurement, tags=tags):
#         points.append(p)

for p in table.get_points():
    points.append(p)

print(table.keys())
print(points)