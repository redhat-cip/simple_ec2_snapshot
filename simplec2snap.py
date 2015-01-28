#!/usr/bin/env python2
# encoding: utf-8
#
# Authors:
#   Pierre Mavro <pierre.mavro@enovance.com>
#
# Contributors:
#   Hugo Rosnet <hugo.rosnet@enovance.com>
#
# Dependencies:
# - python boto
#
#  On Debian: aptitude install python-boto
#  With pip: pip install boto

import argparse
import sys
import boto.ec2
import ConfigParser
import os
import time
import datetime
import logging
from collections import OrderedDict

__version__ = 'v0.4'

LVL = {'INFO': logging.INFO,
       'DEBUG': logging.DEBUG,
       'ERROR': logging.ERROR,
       'CRITICAL': logging.CRITICAL}


def setup_log(name=__name__, level='INFO', log=None,
              console=True, form='%(asctime)s [%(levelname)s] %(message)s'):
    """
    Setup logger object for displaying information into console/file

    :param name: Name of the logger object to create
    :type name: str

    :param level: Level INFO/DEBUG/ERROR etc
    :type level: str

    :param log: File to which log information
    :type log: str

    :param console: If log information sent to console as well
    :type console: Boolean

    :param form: The format in which the log will be displayed
    :type form: str

    :returns: The object logger
    :rtype: logger object
    """
    level = level.upper()
    if level not in LVL:
        logging.warning("Option of log level %s incorrect, using INFO." % level)
        level = 'INFO'
    level = LVL[level]
    formatter = logging.Formatter(form)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if log is not None:
        filehdl = logging.FileHandler(log)
        filehdl.setFormatter(formatter)
        logger.addHandler(filehdl)
    if console is True:
        consolehdl = logging.StreamHandler()
        consolehdl.setFormatter(formatter)
        logger.addHandler(consolehdl)
    return logger


class Instance:
    """
    Contruct instances and set/get attached disks
    """

    def __init__(self, iid, name, state, root_dev):
        """
        Set instance id
        :param iid: Instance ID
        :type iid: str

        :param name: Name of the instance
        :type type: str

        :param state: State of instance
        :type state: str

        :param root_dev: Name of the root device
        :type root_dev: str
        """
        self.instance_id = iid
        self.name = name
        self.initial_state = state
        self.root_dev = root_dev
        self.disks = {}

    def add_disk(self, vol, device):
        """
        Add a disk to an instance

        :param vol: set the volume id
        :type vol: str

        :param device: set the device path
        :type device: str
        """
        self.disks[vol] = device

    def get_disks(self):
        """
        Get the list of disks with mount points

        :returns: Dictionary of volumes with mount points
        :rtype return: dict of str
        """
        return(self.disks)


class ManageSnapshot:
    """
    Manage AWS Snapshot
    """

    def __init__(self, region, key_id, access_key, instance_list, tags,
                 dry_run, timeout, cold_snap, limit, no_root_device,
                 max_age, no_snap, keep_last_snapshots, logger=__name__):
        """
        :param region: EC2 region
        :type region: str

        :param key_id: EC2 key identifier
        :type key_id: str

        :param access_key: EC2 access key
        :type access_key: str

        :param instance_list: filter on this list of instances
        :type instance_list: list

        :param tags: filter on this tags
        :type tags: dict

        :param dry_run: run without applying, just for test
        :type dry_run: bool

        :param timeout: maximum time to wait when instances are switching state
        :type timeout: int

        :param cold_snap: choose if you want to stop
                            or not instance before snapshoting
        :type cold_snap: bool

        :param limit: limit the number of snapshots
        :type limit: int

        :param no_root_device: do not snapshot root devices
        :type no_root_device: bool

        :param max_age: maximum age of snapshot to keep
        :type max_age: list

        :param no_snap: specify if snapshot needs to be done or not
        :type no_snap: bool

        :param keep_last_snapshots: keep at least x snapshots
        :type keep_last_snapshots: int

        :param logger: logger name
        :type logger: str

        """
        self._region = region
        self._key_id = key_id
        self._access_key = access_key
        self._instance_list = instance_list
        self._tags = tags
        self._dry_run = dry_run
        self._timeout = timeout
        self._cold_snap = cold_snap
        self._limit = limit
        self._no_root_device = no_root_device
        self._max_age = max_age
        self._max_age_sec = 0
        self._no_snap = no_snap
        self._keep_last_snapshots = keep_last_snapshots
        self.logger = logging.getLogger(logger)

        self._instances = []
        self._conn = self._validate_aws_connection()
        self._filter_instances()
        self._set_instance_info()

    def _validate_aws_connection(self):
        """
        Validate if AWS connection is OK or not

        :returns: connection access
        :rtype return: object
        """
        # Print running mode
        mode = 'run'
        if self._dry_run is True:
            mode = ' '.join(['dry', mode])
        self.logger.info("== Launching %s mode ==" % mode)

        c = False
        self.logger.info('Connecting to AWS')
        self.logger.debug("Using Access key: %s" % self._access_key)
        try:
            c = boto.ec2.connect_to_region(self._region,
                                           aws_access_key_id=self._key_id,
                                           aws_secret_access_key=self._access_key)
        except IndexError, e:
            self.logger.critical("Can't connect with the credentials: %s" % e)
            sys.exit(1)
        return c

    def _set_instance_info(self):
        """
        Set instances info from an ID
        This will construct an object containing disks attributes
        """
        # Remove doubles
        self._instance_list = list(set(self._instance_list))
        # Create Instance object
        for iid in self._instance_list:
            # Get instance elements
            instance = self._conn.get_all_instances(instance_ids=iid)[0].instances[0]
            name = instance.tags['Name']
            state = instance.state
            root_dev = instance.root_device_name
            instance_id = Instance(iid, name, state, root_dev)
            self._instances.append(instance_id)
            # Set disks
            filter = {'attachment.instance-id': iid}
            vol = self._conn.get_all_volumes(filters=filter)
            for device in vol:
                filter = {'block-device-mapping.volume-id': device.id}
                volumesinstance = self._conn.get_all_instances(filters=filter)
                ids = [z for k in volumesinstance for z in k.instances]
                for s in ids:
                    instance_id.add_disk(device.id, device.attach_data.device)
        # Stop if no instances matched
        if (len(self._instances) == 0):
            self.logger.error('No instances found with those parameters !')
            return

    def _filter_instances(self):
        """
        Filter instances by tag
        """
        self.logger.info('Getting instances information')
        if len(self._tags) > 0:

            # Create a dictionary with tags to create filters
            filter_tags = {}
            for tag in self._tags:
                key = ''.join(['tag:', tag[0]])
                value = tag[1]
                filter_tags[key] = value

            reservations = self._conn.get_all_instances(filters=filter_tags)
            instances = [i for r in reservations for i in r.instances]
            for instance in instances:
                # Do not keep terminated instances
                if self._conn.get_all_instances(instance_ids=instance.id)[0].instances[0].state == 'terminated':
                    return
                else:
                    self._instance_list.append(instance.id)

    def _check_inst_state(self, iid, expected_state):
        """
        Will wait until the expected state or until timeout will be reached

        :param iid: EC2 instance ID
        :type iid: object

        :param expected_state: instance expected state state
        :type expected_state: str

        :returns: Boolean
        """
        retry = 5
        counter = 0
        while self._conn.get_all_instances(instance_ids=iid.instance_id)[0].instances[0].state != expected_state:
            self.logger.debug("Waiting for %s state... %s / %s" %
                              (expected_state, counter, self._timeout))
            counter += retry
            if counter <= self._timeout:
                time.sleep(retry)
            else:
                self.logger.error('Timeout exceded')
                return False
        self.logger.info("Instance %s now %s !" %
                         (iid.instance_id, expected_state))
        return True

    def _create_inst_snap(self, iid):
        """
        Create instance snapshot

        :param iid: EC2 instance ID
        :type iid: str
        """
        # Name cold and hot snapshots
        if self._cold_snap is False:
            stype = 'Hot'
        else:
            stype = 'Cold'

        disks = iid.get_disks()
        for vol, device in disks.iteritems():
            # Removing root device if required
            if self._no_root_device is True and device == iid.root_dev:
                self.logger.debug('Not snapshoting root device %s(%s)' %
                                  (vol, device))
                continue
            # Make snapshot
            snap_name = ''.join([iid.instance_id,
                                 ' (', iid.name, ') - ', stype, ' ', device,
                                 ' (', vol, ')'])
            if self._dry_run is False:
                snap_id = self._conn.create_snapshot(vol, snap_name)
                snap_id.add_tags({'type': stype,
                                  'volume': vol,
                                  'device': device,
                                  'instance name': iid.name})
                self.logger.info("%s snapshot made for %s(%s) - %s" %
                                 (stype, vol, device, snap_id.id))
            else:
                self.logger.info("%s snapshot made for %s(%s)" %
                                 (stype, vol, device))

    def calulate_max_snap_age(self):
        """
        Calculate Snapshot age
        """
        self.logger.debug('Calculating max age')

        # Check params
        self._max_age[0] = int(self._max_age[0])
        try:
            self._max_age[0] == 0
        except ValueError:
            self.logger.error('Max age value cannot be 0')
            sys.exit(1)
        if self._max_age[0] == 0:
            self.logger.error('Max age value cannot be 0')
            sys.exit(1)

        # Calculate the maximum allowed snapshot age
        if self._max_age[1] == 's':
            self._max_age_sec = self._max_age[0]
        elif self._max_age[1] == 'm':
            self._max_age_sec = self._max_age[0] * 60
        elif self._max_age[1] == 'h':
            self._max_age_sec = self._max_age[0] * 60 * 60
        elif self._max_age[1] == 'd':
            self._max_age_sec = self._max_age[0] * 60 * 60 * 24
        elif self._max_age[1] == 'w':
            self._max_age_sec = self._max_age[0] * 60 * 60 * 24 * 7
        elif self._max_age[1] == 'M':
            self._max_age_sec = self._max_age[0] * 60 * 60 * 24 * 30
        elif self._max_age[1] == 'y':
            self._max_age_sec = self._max_age[0] * 60 * 60 * 24 * 30 * 365
        else:
            self.logger.error("Can't find the correct value (here %s),\
                              please choose between s/m/h/d/w/M/y" %
                              self._max_age[1])
            sys.exit(1)

    def mk_rm_snapshot(self):
        """
        Create and remove snapshot on selected Instances ids
        """
        counter = 0
        for iid in self._instances:
            self.logger.info("Working on instance %s (%s)" %
                             (iid.instance_id, iid.name))

            # Limit the number of backups if requested
            self.logger.debug("Limit: %s" % self._limit)
            if self._limit != -1 and counter >= self._limit:
                self.logger.info("The requested limit of snapshots has been reached: %s" % self._limit)
                break
            counter += 1

            if self._no_snap is False:
                # Pausing VM and skip if failed
                self.logger.debug("Initial_state: %s, No hot snap: %s, Dry run: %s" %
                                  (iid.initial_state, self._cold_snap, self._dry_run))
                if iid.initial_state == 'running':
                    if self._cold_snap is True:
                        self.logger.info('Instance is going to be shutdown')
                    if self._cold_snap is True and self._dry_run is False:
                        self._conn.stop_instances(instance_ids=[iid.instance_id])
                        if self._check_inst_state(iid, 'stopped') is False:
                            continue

                # Creating Snapshots
                self._create_inst_snap(iid)

                # Starting VM if was running
                if iid.initial_state == 'running':
                    if self._cold_snap is True:
                        self.logger.info('Instance is going to be started')
                    if self._cold_snap is True and self._dry_run is False:
                        self._conn.start_instances(instance_ids=[iid.instance_id])
                        self._check_inst_state(iid, 'running')

            # Delete old Snapshots
            if len(self._max_age) > 0 or self._keep_last_snapshots > 0:
                self._remove_old_snap(iid)

    def _remove_old_snap(self, iid):
        """
        Remove old snapshots

        :param iid: EC2 instance ID
        :type iid: object
        """
        disks = iid.get_disks()
        for vol, device in disks.iteritems():
            snapshots = self._conn.get_all_snapshots(filters={'volume-id': vol})
            snapshots_tstamp = {}

            for snapshot in snapshots:
                snap_date = snapshot.start_time
                timestamp = datetime.datetime.strptime(snap_date,
                                                       '%Y-%m-%dT%H:%M:%S.000Z')
                self.logger.debug("Volume %s(%s) has snapshot %s on %s" %
                                  (vol, device, snapshot.id, timestamp))
                delta_seconds = int((datetime.datetime.utcnow() - timestamp).total_seconds())

                # When max_age arg is set
                if len(self._max_age) > 0:
                    if delta_seconds > self._max_age_sec:
                        self.logger.info("Deleting snapshot %s (%s|%s)" %
                                         (snapshot.id, vol, device))
                        if self._dry_run is False:
                            snapshot.delete()
                    else:
                        self.logger.debug("Do not delete snapshot %s" %
                                          snapshot.id)

                # When keep_last_snapshots arg is set store them in a dict
                elif self._keep_last_snapshots > 0:
                    snapshots_tstamp[snapshot.id] = delta_seconds

            # Kepp at least the desired number of snapshots
            if self._keep_last_snapshots > 0:
                counter = 1
                # Sort snapshots by timestamp
                snapshots_tstamp = OrderedDict(sorted(snapshots_tstamp.items(), key=lambda v: v[1]))
                for snapshotid, delta_tstamp in snapshots_tstamp.iteritems():
                    if counter > self._keep_last_snapshots:
                        self.logger.info("Deleting snapshot %s (%s|%s)" %
                                         (snapshotid, vol, device))
                        if self._dry_run is False:
                            snapshot = self._conn.get_all_snapshots(snapshot_ids=snapshotid)
                            snapshot[0].delete()
                    else:
                        self.logger.debug("Do not delete snapshot %s (%s|%s)" %
                                          (snapshotid, vol, device))
                    counter += 1


def main():
    """
    Main - manage args
    """
    # Main informations
    parser = argparse.ArgumentParser(
        description='Simple EC2 Snapshot utility',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Command args
    parser.add_argument('-r', '--region', action='store',
                        type=str, default=None, metavar='REGION',
                        help='Set AWS region (ex: eu-west-1)')
    parser.add_argument('-k', '--key_id', action='store',
                        type=str, default=None, metavar='KEY_ID',
                        help='Set AWS Key ID')
    parser.add_argument('-a', '--access_key', action='store',
                        type=str, default=None, metavar='ACCESS_KEY',
                        help='Set AWS Access Key')

    parser.add_argument('-c', '--credentials', action='store', type=str,
                        default=''.join([os.path.expanduser("~"), '/.aws_cred']),
                        metavar='CREDENTIALS',
                        help='Credentials file path')
    parser.add_argument('-p', '--profile', action='store',
                        type=str, default='default', metavar='CRED_PROFILE',
                        help='Credentials profile file defined in \
                              credentials file')

    parser.add_argument('-i', '--instance', action='append',
                        default=[], metavar='INSTANCE_ID',
                        help=' '.join(['Instance ID (ex: i-00000000 or all)']))
    parser.add_argument('-t', '--tags', action='append', type=str,
                        default=[], metavar='ARG', nargs=2,
                        help='Select tags with values (ex: tagname value)')

    parser.add_argument('-u', '--dry_run', action='store_false', default=True,
                        help='Define if it should make snapshot or just \
                        dry run')
    parser.add_argument('-l', '--limit',
                        action='store', default=-1, type=int,
                        help=' '.join(['Limit the number of snapshot (can be',
                                       'usefull with auto-scaling groups)']))
    parser.add_argument('-H', '--cold_snap',
                        action='store_true', default=False,
                        help='Make cold snapshot for a better consistency \
                        (Recommended)')
    parser.add_argument('-m', '--timeout', action='store',
                        type=int, default=600, metavar='COLDSNAP_TIMEOUT',
                        help='Instance timeout (in seconds) for stop and start \
                              during a cold snapshot')
    parser.add_argument('-o', '--no_root_device',
                        action='store_true', default=False,
                        help='Do not snapshot root device')

    parser.add_argument('-g', '--max_age',
                        type=str, default=[],
                        metavar='ARG', nargs=2,
                        help='Maximum snapshot age to keep \
                        (<int> <s/m/h/d/w/M/y>) (ex: 1 h for one hour)')
    parser.add_argument('-d', '--keep_last_snapshots',
                        action='store', default=0, type=int,
                        help='Keep the x last snapshots')
    parser.add_argument('-n', '--no_snap',
                        action='store_true', default=False,
                        help='Do not make snapshot \
                        (useful when combien to -g option)')

    parser.add_argument('-f', '--file_output', metavar='FILE',
                        default=None, action='store', type=str,
                        help='Set an output file')
    parser.add_argument('-s', '--stdout', action='store_true', default=True,
                        help='Log output to console (stdout)')
    parser.add_argument('-v', '--verbosity', metavar='LEVEL', default='INFO',
                        type=str, action='store',
                        help='Verbosity level: DEBUG/INFO/ERROR/CRITICAL')

    parser.add_argument('-V', '--version',
                        action='version',
                        version=' '.join([__version__, 'Licence GPLv2+']),
                        help='Print version number')

    # Print help if no args supplied
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    arg = parser.parse_args()

    # Setup loger
    setup_log(console=arg.stdout, log=arg.file_output, level=arg.verbosity)

    # Read credential file and override by command args
    if os.path.isfile(arg.credentials):
        if os.access(arg.credentials,  os.R_OK):
            config = ConfigParser.ConfigParser()
            config.read([str(arg.credentials)])
            if arg.region is None:
                arg.region = config.get(arg.profile, 'aws_region')
            if arg.access_key is None:
                arg.access_key = config.get(arg.profile, 'aws_secret_access_key')
            if arg.key_id is None:
                arg.key_id = config.get(arg.profile, 'aws_access_key_id')
        else:
            print("Don't have permission to read credentials file")
            sys.exit(1)

    # Exit if no instance or tag has been set
    if arg.instance is None and arg.tags is None:
        print('Please set at least instance ID or tag with value')
        sys.exit(1)
    else:
        # Create action
        selected_instances = ManageSnapshot(arg.region, arg.key_id,
                                            arg.access_key, arg.instance,
                                            arg.tags, arg.dry_run, arg.timeout,
                                            arg.cold_snap, arg.limit,
                                            arg.no_root_device, arg.max_age,
                                            arg.no_snap,
                                            arg.keep_last_snapshots)
        # Calculate max snapshot age
        if len(arg.max_age) > 0:
            selected_instances.calulate_max_snap_age()
        # Launch snapshot
        selected_instances.mk_rm_snapshot()

        sys.exit(0)

if __name__ == "__main__":
    main()
