# IoT App Analysis

### Callgraph Analysis

How to run the callgraph data collection (incl. AppArmor logs):
* `cd callgraph-analysis`
* Load a basic AppArmor profile for python3 in complain mode (i.e. no enforcement): `sudo apparmor_parser -C usr.local.bin.python3`
* Check that the profile was loaded successfully: `sudo apparmor_status`. Look for the following message in the output:
```
1 profiles are in complain mode:
/usr/local/bin/python3
```
* Collect the python callgraphs and AppArmor logs for a specific IoT app category *cat*: `python3 collect-callgraphs.py <cat>`. *cat* can be `audio`, `visual`, `env`, or `multi`.
* Check `logs/<cat>_log` to make sure the data collection ran to completion.
* Unload the AppArmor profile: `sudo apparmor_parser -R usr.local.bin.python3`
