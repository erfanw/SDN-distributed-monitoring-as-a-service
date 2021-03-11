# ik2200-csd

This repository contains all the modules for the SDN project, including CPM, NFM, Topology, DM and the Web module.

## Usage

For a full test, please run the database module at first, then controller. Run the topology/test at last.

There is also an advanced option to launch the test from a well-designed website. Please chech the "DM and Website" section.

### Topology

To run the topology and enter the Mininet CLI, use the following commands:

```bash
make topo
```

This will run the “testbed" topology containing six clients and six servers.

We also added an "auto_test" feature. To enable that, use this command instead:

```bash
make test
```

This will not launch the Mininet CLI, but will launch the auto test scripts and keep it running.

To launch the designated tests for the Stanford topology, please use this command:

```bash
make test_st
```


### NFM & CPM 

To run the NFM with the Shortest Path (SP) routing controller, use the following commands:

```bash
make controller_sp
```

This will run the NFM and the SP routing controller. 

To use the advanced controller with the "Least-cost Path" routing algorithm, use the following commands:

```bash
make controller
```


### DM and Web

To run the DM, use the following commands:

```bash
make database
```

This will start InfluxDB server and Flask server for RESTful API calls. The default port for InfluxDB is 8086 and that for Flask is 5000. 

If you want to start the tests from the website, please open a browser after launching the DM and enter `0.0.0.0:5000`

### Data Processing

Please refer to the README in the data_processing folder.


### Clean the enviroment

To clean the mininet and ryu configurations, please use the following commands:

```bash
make clean
```

