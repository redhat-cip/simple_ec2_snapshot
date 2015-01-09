simple_ec2_snapshot
===================

Simple solution to backup ec2 instances using snapshots

With Simple EC2 Snapshot you can:

* Filter by tags which instance(s) you want to snapshot (accepting wildcards)
* Support filtering with multiple tags
* Support multiple instances snapshot at the same time
* Make hot snapshot (by default) or cold snapshot (recommended for some softwares like databases)
* Can use credential file with profiles or cli credentials

Here is an example. First we're using list action, to check which instances we're going to snapshot:
```
> ./simplec2snap.py -o list -t Name 'instance-name-*'
[+] Validating AWS connection
[+] Getting instances information
  => i-ad0fcc4b (instance-name-1)
    - vol-faefbae6 - /dev/sda
    - vol-2e742a32 - /dev/sdf
  => i-56489db2 (instance-name-2)
    - vol-76b1bb71 - /dev/sda
    - vol-75b1bb72 - /dev/sdb
```

Then we launch hot snapshot by choosing snapshot action:
```
> ./simplec2snap.py -o snapshot -t Name 'instance-name-*'
[+] Validating AWS connection
[+] Getting instances information
[+] i-ad0fcc4b (instance-name-1)
  => Creating Snapshot
    - Creating snapshot of /dev/sda ( vol-faefbae6 ) : snap-3e309ecf
    - Creating snapshot of /dev/sdf ( vol-2e742a32 ) : snap-15309ee4
[+] i-56489db2 (instance-name-2)
  => Creating Snapshot
    - Creating snapshot of /dev/sda ( vol-76b1bb71 ) : snap-0d309efc
    - Creating snapshot of /dev/sdb ( vol-75b1bb72 ) : snap-c9319f38
```

If we want to create cold snapshot on a specified instance ID:
```
./simplec2snap.py -o snapshot -i i-ad0fcc4b -H
[+] Validating AWS connection
[+] Getting instances information
[+] i-ad0fcc4b (instance-name-1)
  => Shutting down instance
    - Please wait while stopping...
    ...
    - Please wait while stopping...
  => Now stopped !
  => Creating Snapshot
    - Creating snapshot of /dev/sda ( vol-faefbae6 ) : snap-a106a850
    - Creating snapshot of /dev/sdf ( vol-2e742a32 ) : snap-a206a853
  => Starting instance
    - Please wait while starting...
    ...
    - Please wait while starting...
  => Instance started !
```

Here is the help with the complete list of options:
```
/simplec2snap.py
usage: simplec2snap.py [-h] [-r REGION] [-k KEY_ID] [-a ACCESS_KEY]
                       [-c CREDENTIALS] [-p CRED_PROFILE] [-i INSTANCE_ID]
                       [-t ARG ARG] -o {list,snapshot} [-H] [-v]

Simple EC2 Snapshot utility

optional arguments:
  -h, --help            show this help message and exit
  -r REGION, --region REGION
                        Set AWS region (ex: eu-west-1) (default: None)
  -k KEY_ID, --key_id KEY_ID
                        Set AWS Key ID (default: None)
  -a ACCESS_KEY, --access_key ACCESS_KEY
                        Set AWS Access Key (default: None)
  -c CREDENTIALS, --credentials CREDENTIALS
                        Credentials file path (default:
                        /home/pmavro/.aws_cred)
  -p CRED_PROFILE, --profile CRED_PROFILE
                        Credentials profile file defined in credentials file
                        (default: default)
  -i INSTANCE_ID, --instance INSTANCE_ID
                        Instance ID (ex: i-00000000 or all) (default: [])
  -t ARG ARG, --tags ARG ARG
                        Select tags with their values (ex: tagname value)
                        (default: [])
  -o {list,snapshot}, --action {list,snapshot}
                        Set action to make (default: None)
  -H, --no_hot_backup   Make cold backup for a better consistency
                        (Recommended) (default: False)
  -v, --version         Print version number
```