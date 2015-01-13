simple_ec2_snapshot
===================

Simple solution to backup ec2 instances using snapshots

With Simple EC2 Snapshot supports:

* Hot snapshots (by default) and Cold snapshots
* Multiple instances snapshot on the same command line
* The detection of doubles
* Filters by tags (accepting wildcards) or by instance IDs
* Credential file with profiles and cli credentials
* Limit the number of snapshots

## Filters

You can first decide to choose what to backup with Instance ID or Tags. You can set multiple tags and/or multiple instance ID at the same time.

For example, if I want to snapshot 2 instances in the same command line, it should looks like this:
```
> ./simplec2snap.py -i i-ad0fcc4b -i i-56489db2
```

To snapshot multiple instances by selecting multiple tags. Here is an example with 2 tagsi, so it should match both:
```
> ./simplec2snap.py -t Name 'instance*' -t env prod
```

If you want to add an instance in addition of the previous tags:
```
> ./simplec2snap.py -t Name 'instance*' -t env prod -i i-ad0fcc4b
```

## Dry Run mode

Use the dry run mode (enabled by default) to see what actions will be performed when selecting a tag Name or an instance:
```
> ./simplec2snap.py -t Name 'instance-name-*'
2015-01-13 12:07:17,015 [INFO] == Launching dry run mode ==
2015-01-13 12:07:17,016 [INFO] Connecting to AWS with your Access key: xxxxx
2015-01-13 12:07:17,016 [INFO] Getting instances information
2015-01-13 12:07:18,957 [INFO] Working on instance i-ad0fcc4b (instance-name-1)
2015-01-13 12:07:18,957 [INFO]   - i-ad0fcc4b : snapshoting /dev/sda ( vol-faefbae6 )
2015-01-13 12:07:18,957 [INFO]   - i-ad0fcc4b : snapshoting /dev/sdf ( vol-2e742a32 )
2015-01-13 12:07:18,957 [INFO] Working on instance i-56489db2 (instance-name-2)
2015-01-13 12:07:18,957 [INFO]   - i-56489db2 : snapshoting /dev/sda ( vol-76b1bb71 )
2015-01-13 12:07:18,957 [INFO]   - i-56489db2 : snapshoting /dev/sdb ( vol-75b1bb72 )
```

## Run mode

If you're ok with the previous dry run, then add '-u' for run mode:
```
> ./simplec2snap.py -t Name 'instance-name-*' -u
2015-01-13 12:07:10,733 [INFO] == Launching run mode ==
2015-01-13 14:57:25,470 [INFO] Connecting to AWS with your Access key: xxxxx
2015-01-13 14:57:25,471 [INFO] Getting instances information
2015-01-13 14:57:27,927 [INFO] Working on instance i-ad0fcc4b (instance-name-1)
2015-01-13 14:57:28,315 [INFO]   - i-ad0fcc4b : snapshoting /dev/sda ( vol-faefbae6 ) snap-d061f521
2015-01-13 14:57:28,851 [INFO]   - i-ad0fcc4b : snapshoting /dev/sdf ( vol-2e742a32 ) snap-d661f527
2015-01-13 14:57:28,851 [INFO] Working on instance i-56489db2 (instance-name-2)
2015-01-13 14:57:29,343 [INFO]   - i-56489db2 : snapshoting /dev/sda ( vol-76b1bb71 ) snap-c161f530
2015-01-13 14:57:29,822 [INFO]   - i-56489db2 : snapshoting /dev/sdb ( vol-75b1bb72 ) snap-c761f536
```

## Hot vs Cold snapshot

By default Hot mode is selected to perform snapshot without stopping instances. However, this may not be the best choice in some case, like for database purpose. To get a full consistent snapshot of your EC2 with attached EBS, you have to make a Cold snapshot which involves to shutdown, snapshot and start instance.

To do so, you have to add '-H' option:
```
> ./simplec2snap.py -t Name 'instance-name-*' -u -H
2015-01-13 14:57:33,925 [INFO] == Launching run mode ==
2015-01-13 14:57:33,925 [INFO] Connecting to AWS with your Access key: xxxxx
2015-01-13 14:57:33,926 [INFO] Getting instances information
2015-01-13 14:57:36,483 [INFO] Working on instance i-ad0fcc4b (instance-name-1)
2015-01-13 14:57:36,483 [INFO] Instance is going to be shutdown
2015-01-13 14:58:22,754 [INFO] Instance i-ad0fcc4b now stopped !
2015-01-13 14:58:23,163 [INFO]   - i-ad0fcc4b : snapshoting /dev/sda ( vol-faefbae6 ) snap-4b61f5ba
2015-01-13 14:58:23,582 [INFO]   - i-ad0fcc4b : snapshoting /dev/sdf ( vol-2e742a32 ) snap-4c61f5bd
2015-01-13 14:58:23,582 [INFO] Instance is going to be started
2015-01-13 14:58:54,924 [INFO] Instance i-ad0fcc4b now running !
2015-01-13 14:58:54,924 [INFO] Working on instance i-56489db2 (instance-name-2)
2015-01-13 14:58:54,924 [INFO] Instance is going to be shutdown
2015-01-13 14:59:31,104 [INFO] Instance i-56489db2 now stopped !
2015-01-13 14:59:31,523 [INFO]   - i-56489db2 : snapshoting /dev/sda ( vol-76b1bb71 ) snap-ae62f65f
2015-01-13 14:59:32,007 [INFO]   - i-56489db2 : snapshoting /dev/sdb ( vol-75b1bb72 ) snap-9362f662
2015-01-13 14:59:32,007 [INFO] Instance is going to be started
2015-01-13 14:59:53,023 [INFO] Instance i-56489db2 now running !
```

## Limit snapshots for auto-scaling group

In auto-scaling groups, you normally have x time the same running intance. Snapshoting a huge number of time the same instance may not be very interesting. That's why you can limit the number of snapshot by using '-l' command followed by the number of desired snapshot. If I only want one:
```
> ./simplec2snap.py -t Name 'instance-name-*' -l 1
2015-01-13 15:26:38,532 [INFO] == Launching dry run mode ==
2015-01-13 15:26:38,532 [INFO] Connecting to AWS with your Access key: xxxxx
2015-01-13 15:26:38,533 [INFO] Getting instances information
2015-01-13 15:26:40,565 [INFO] Working on instance i-ad0fcc4b (instance-name-1)
2015-01-13 15:26:40,565 [INFO]   - i-ad0fcc4b : snapshoting /dev/sda ( vol-faefbae6 )
2015-01-13 15:26:40,565 [INFO]   - i-ad0fcc4b : snapshoting /dev/sdf ( vol-2e742a32 )
2015-01-13 15:26:40,565 [INFO] The requested limit of snapshots has been reached: 1
```

## Credentials file

You can use a credentials file with several profiles. It should looks like this:
```ini
[default]
aws_region = <region>
aws_access_key_id = <key_id>
aws_secret_access_key = <access_key>

#[profile profile1]
#aws_region = <region>
#aws_access_key_id = <key_id>
#aws_secret_access_key = <access_key>
```
The default one should be located in '~/.aws_cred'. You can override this with '-c' argument and '-p' to specify the profile fulfill into brackets.

## Help

Here is the help with the complete list of options:
```
> ./simplec2snap.py
usage: simplec2snap.py [-h] [-r REGION] [-k KEY_ID] [-a ACCESS_KEY]
                       [-c CREDENTIALS] [-p CRED_PROFILE] [-i INSTANCE_ID]
                       [-t ARG ARG] [-u] [-l LIMIT] [-H] [-m COLDSNAP_TIMEOUT]
                       [-f FILE] [-s] [-v LEVEL] [-V]

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
                        Select tags with values (ex: tagname value) (default:
                        [])
  -u, --dry_run         Define if it should make snapshot or just dry run
                        (default: True)
  -l LIMIT, --limit LIMIT
                        Limit the number of snapshot (can be usefull with
                        auto-scaling groups) (default: -1)
  -H, --no_hot_snap     Make cold snapshot for a better consistency
                        (Recommended) (default: False)
  -m COLDSNAP_TIMEOUT, --timeout COLDSNAP_TIMEOUT
                        Instance timeout (in seconds) for stop and start
                        during a cold snapshot (default: 600)
  -f FILE, --file_output FILE
                        Set an output file (default: None)
  -s, --stdout          Log output to console (stdout) (default: True)
  -v LEVEL, --verbosity LEVEL
                        Verbosity level: DEBUG/INFO/ERROR/CRITICAL (default:
                        INFO)
  -V, --version         Print version number
```
