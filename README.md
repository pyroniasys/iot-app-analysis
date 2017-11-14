# IoT App Analysis

### Callgraph Analysis

How to run the callgraph data collection on the Sample Apps:
* Transfer all data collection files to the Raspberry Pi: `./setup-pi callgraph_analysis`
* SSH into the Raspberry Pi
* `cd callgraph_analysis`
* Run the data collection: `./run-collection <email>`. This will send you an email notification when the script is done.
* Logout of the Raspberry Pi
* On your local machine, run `./retrieve-pi-data callgraph_analysis` to transfer all collected data back.