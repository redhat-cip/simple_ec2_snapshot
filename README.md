simple_ec2_snapshot
===================

Simple solution to backup ec2 instances using snapshots

With Simple EC2 Snapshot supports:

* Hot snapshots (by default) and Cold snapshots
* Multiple instances snapshot in one line
* Detection of doubles
* Filters by tags (allowing wildcards) or by instance IDs
* Credentials file multiple with profiles
* Limit the number of snapshots
* Restrict snapshots to data disks only
* Snapshot retention

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

## Dry Run mode

Use the dry run mode (enabled by default) to see what actions will be performed when selecting a tag Name or an instance:
```
> ./simplec2snap.py -t Name "instance-name*"
2015-01-26 17:05:25,954 [INFO] == Launching dry run mode ==
2015-01-26 17:05:25,954 [INFO] Connecting to AWS
2015-01-26 17:05:25,955 [INFO] Getting instances information
2015-01-26 17:05:28,341 [INFO] Working on instance i-e16cc205 (instance-name2)
2015-01-26 17:05:28,341 [INFO] Snapshoting vol-fa415bfd(/dev/sdb) - dry-run
2015-01-26 17:05:28,341 [INFO] Snapshoting vol-22465c25(/dev/sda) - dry-run
2015-01-26 17:05:28,341 [INFO] Working on instance i-6f6ec08b (instance-name1)
2015-01-26 17:05:28,341 [INFO] Snapshoting vol-9d465c9a(/dev/sda) - dry-run
2015-01-26 17:05:28,341 [INFO] Snapshoting vol-9c465c9b(/dev/sdb) - dry-run
```

## Run mode

If you're ok with the previous dry run, then add '-u' for run mode:
```
> ./simplec2snap.py -t Name "instance-name*" -u
2015-01-26 17:06:19,163 [INFO] == Launching run mode ==
2015-01-26 17:06:19,163 [INFO] Connecting to AWS
2015-01-26 17:06:19,163 [INFO] Getting instances information
2015-01-26 17:06:21,083 [INFO] Working on instance i-e16cc205 (instance-name2)
2015-01-26 17:06:21,352 [INFO] Snapshoting vol-fa415bfd(/dev/sdb) - snap-35adb8c4
2015-01-26 17:06:21,587 [INFO] Snapshoting vol-22465c25(/dev/sda) - snap-36adb8c7
2015-01-26 17:06:21,587 [INFO] Working on instance i-6f6ec08b (instance-name1)
2015-01-26 17:06:21,832 [INFO] Snapshoting vol-9d465c9a(/dev/sda) - snap-3cadb8cd
2015-01-26 17:06:22,087 [INFO] Snapshoting vol-9c465c9b(/dev/sdb) - snap-21adb8d0
```

## Hot vs Cold snapshot

By default Hot mode is selected to perform snapshot without stopping instances. However, this may not be the best choice in some case, like for database purpose. To get a full consistent snapshot of your EC2 with attached EBS, you have to make a Cold snapshot which involves to shutdown, snapshot and start instance.

To do so, you have to add '-H' option:
```
> ./simplec2snap.py -t Name "instance-name*" -u -H
2015-01-26 17:07:10,281 [INFO] == Launching run mode ==
2015-01-26 17:07:10,281 [INFO] Connecting to AWS
2015-01-26 17:07:10,282 [INFO] Getting instances information
2015-01-26 17:07:12,490 [INFO] Working on instance i-e16cc205 (instance-name2)
2015-01-26 17:07:12,490 [INFO] Instance is going to be shutdown
2015-01-26 17:07:48,871 [INFO] Instance i-e16cc205 now stopped !
2015-01-26 17:07:49,134 [INFO] Snapshoting vol-fa415bfd(/dev/sdb) - snap-a8afba59
2015-01-26 17:07:49,379 [INFO] Snapshoting vol-22465c25(/dev/sda) - snap-adafba5c
2015-01-26 17:07:49,379 [INFO] Instance is going to be started
2015-01-26 17:08:20,565 [INFO] Instance i-e16cc205 now running !
2015-01-26 17:08:20,565 [INFO] Working on instance i-6f6ec08b (instance-name1)
2015-01-26 17:08:20,565 [INFO] Instance is going to be shutdown
2015-01-26 17:08:51,617 [INFO] Instance i-6f6ec08b now stopped !
2015-01-26 17:08:51,853 [INFO] Snapshoting vol-9d465c9a(/dev/sda) - snap-b1aebb40
2015-01-26 17:08:52,098 [INFO] Snapshoting vol-9c465c9b(/dev/sdb) - snap-b2aebb43
2015-01-26 17:08:52,098 [INFO] Instance is going to be started
2015-01-26 17:09:09,467 [INFO] Instance i-6f6ec08b now running !
```

## Limit snapshots for auto-scaling group

In auto-scaling groups, you normally have x time the same running intance. Snapshoting a huge number of time the same instance may not be very interesting. That's why you can limit the number of snapshot by using '-l' command followed by the number of desired snapshot. If I only want one:
```
> ./simplec2snap.py -t Name "instance-name*" -l 1 
2015-01-26 17:11:27,561 [INFO] == Launching dry run mode ==
2015-01-26 17:11:27,561 [INFO] Connecting to AWS
2015-01-26 17:11:27,562 [INFO] Getting instances information
2015-01-26 17:11:29,659 [INFO] Working on instance i-e16cc205 (instance-name2)
2015-01-26 17:11:29,659 [INFO] Snapshoting vol-fa415bfd(/dev/sdb) - dry-run
2015-01-26 17:11:29,659 [INFO] Snapshoting vol-22465c25(/dev/sda) - dry-run
2015-01-26 17:11:29,659 [INFO] Working on instance i-6f6ec08b (instance-name1)
2015-01-26 17:11:29,660 [INFO] The requested limit of snapshots has been reached: 1
```

## Remove root device from snapshots

Still for auto-scaling groups, your root device may not be required to snapshot. Generally because it may be builded from a configuration manager and you just don't care of it. So the goal is to remove it from the snapshot list, you can so use '-o' option:

```
> ./simplec2snap.py -t Name "instance-name*" -o  
2015-01-26 17:11:50,757 [INFO] == Launching dry run mode ==
2015-01-26 17:11:50,757 [INFO] Connecting to AWS
2015-01-26 17:11:50,758 [INFO] Getting instances information
2015-01-26 17:11:52,708 [INFO] Working on instance i-e16cc205 (instance-name2)
2015-01-26 17:11:52,708 [INFO] Snapshoting vol-fa415bfd(/dev/sdb) - dry-run
2015-01-26 17:11:52,708 [INFO] Working on instance i-6f6ec08b (instance-name1)
2015-01-26 17:11:52,708 [INFO] Snapshoting vol-9c465c9b(/dev/sdb) - dry-run
```

## Snapshot retention

You can define the retention of your backups. You need to specify 2 args:

* Number: sepcify a number for day, week... which is defined in the second arg
* Time element: specify s(second), m(min), h(hour), d(day), w(week), M(month), y(year)

So for example, if you want to keep snapshots for 3 weeks and delete the old ones, you have to set: 3 w.

Here is a basic example where I want to delete snapshots older than 10 days:
```
> ./simplec2snap.py -t Name "instance-name*" -n -g 10 d
2015-01-26 17:21:33,616 [INFO] == Launching dry run mode ==
2015-01-26 17:21:33,616 [INFO] Connecting to AWS
2015-01-26 17:21:33,617 [INFO] Getting instances information
2015-01-26 17:21:36,201 [INFO] Working on instance i-e16cc205 (instance-name2)
2015-01-26 17:21:36,334 [INFO] Deleting snapshot snap-a8afba59
2015-01-26 17:21:36,462 [INFO] Deleting snapshot snap-adafba5c
2015-01-26 17:21:36,462 [INFO] Working on instance i-6f6ec08b (instance-name1)
2015-01-26 17:21:36,566 [INFO] Deleting snapshot snap-b1aebb40
2015-01-26 17:21:36,683 [INFO] Deleting snapshot snap-b2aebb43
```

Here -n is used to not make snapshots, only delete olds. But you can ask on the same line to make snapshots AND remove old ones:
```
> ./simplec2snap.py -t Name "instance-name*" -g 10 m   
2015-01-26 17:22:43,263 [INFO] == Launching dry run mode ==
2015-01-26 17:22:43,263 [INFO] Connecting to AWS
2015-01-26 17:22:43,264 [INFO] Getting instances information
2015-01-26 17:22:46,217 [INFO] Working on instance i-e16cc205 (instance-name2)
2015-01-26 17:22:46,218 [INFO] Snapshoting vol-fa415bfd(/dev/sdb) - dry-run
2015-01-26 17:22:46,218 [INFO] Snapshoting vol-22465c25(/dev/sda) - dry-run
2015-01-26 17:22:47,328 [INFO] Deleting snapshot snap-a8afba59
2015-01-26 17:22:47,491 [INFO] Deleting snapshot snap-adafba5c
2015-01-26 17:22:47,491 [INFO] Working on instance i-6f6ec08b (instance-name1)
2015-01-26 17:22:47,491 [INFO] Snapshoting vol-9d465c9a(/dev/sda) - dry-run
2015-01-26 17:22:47,492 [INFO] Snapshoting vol-9c465c9b(/dev/sdb) - dry-run
2015-01-26 17:22:47,669 [INFO] Deleting snapshot snap-b1aebb40
2015-01-26 17:22:47,842 [INFO] Deleting snapshot snap-b2aebb43
```

## Help

Here is the help with the complete list of options:
```
> ./simplec2snap.py 
usage: simplec2snap.py [-h] [-r REGION] [-k KEY_ID] [-a ACCESS_KEY]
                       [-c CREDENTIALS] [-p CRED_PROFILE] [-i INSTANCE_ID]
                       [-t ARG ARG] [-u] [-l LIMIT] [-H] [-m COLDSNAP_TIMEOUT]
                       [-o] [-g ARG ARG] [-n] [-f FILE] [-s] [-v LEVEL] [-V]

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
                        /home/instance-name/.aws_cred)
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
  -o, --no_root_device  Do not snapshot root device (default: False)
  -g ARG ARG, --max_age ARG ARG
                        Maximum snapshot age to keep (<int> <s/m/h/d/w/M/y>)
                        (ex: 1 h for one hour) (default: [])
  -n, --no_snap         Do not make snapshot (useful when combien to -g
                        option) (default: False)
  -f FILE, --file_output FILE
                        Set an output file (default: None)
  -s, --stdout          Log output to console (stdout) (default: True)
  -v LEVEL, --verbosity LEVEL
                        Verbosity level: DEBUG/INFO/ERROR/CRITICAL (default:
                        INFO)
  -V, --version         Print version number
```
