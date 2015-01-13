#!/usr/bin/env python
# encoding: utf-8
# Made by Pierre Mavro / Deimosfr
# eNovance / RedHat

# Dependancies:
# - python boto
# On Debian: aptitude install python-boto
# With pip: pip install boto

import argparse
import sys
import boto.ec2
import ConfigParser
import os
import time
import logging

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

    def __init__(self, iid, rid, name, state, root_dev):
        """
        Set instance id
        :param iid: Instance ID
        :type iid: str
        :param rid: Reservation ID
        :type rid: str
        :param name: Name of the instance
        :type type: str
        """
        self.instance_id = iid
        self.reservation = rid
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
        :rtype return: dict
        """
        return(self.disks)


class ManageSnapshot:
    """
    Manage AWS Snapshot
    """

    def __init__(self, region, key_id, access_key, instance_list, tags,
                 dry_run, timeout, no_hot_snap, limit, no_root_device,
                 logger=__name__):
        self._region = region
        self._key_id = key_id
        self._access_key = access_key
        self._instance_list = instance_list
        self._tags = tags
        self._dry_run = dry_run
        self._timeout = timeout
        self._no_hot_snap = no_hot_snap
        self._limit = limit
        self._no_root_device = no_root_device
        self._instances = []
        self.logger = logging.getLogger(logger)
        self._conn = self._validate_aws_connection()
        self._filter_instances()
        self._set_instance_info()

    def _validate_aws_connection(self):
        """
        Validate if AWS connection is OK or not
        """
        # Print running mode
        mode = 'run'
        if self._dry_run is True:
            mode = ' '.join(['dry', mode])
        self.logger.info(' '.join(['== Launching', mode, 'mode ==']))

        c = False
        self.logger.info(' '.join(['Connecting to AWS with your Access key:',
                                   self._access_key]))
        try:
            c = boto.ec2.connect_to_region(self._region,
                                           aws_access_key_id=self._key_id,
                                           aws_secret_access_key=self._access_key)
        except IndexError, e:
            self.logger.critical("Can't connect with the credentials: %s" % e)
            sys.exit(1)
        return(c)

    def _set_instance_info(self):
        """
        Set instances info from an ID
        This will construct an object containing disks attributes

        :param instance_list: list of instance ID
        :type instance_list: list
        """
        # Remove doubles
        self._instance_list = list(set(self._instance_list))
        # Create Instance object
        for iid in self._instance_list:
            # Get reservation id
            rid = self._conn.get_all_instances(instance_ids=iid)[0].id
            # Get instance name
            name = self._conn.get_all_instances(instance_ids=iid)[0].instances[0].tags['Name']
            # Get instance status
            state = self._conn.get_all_instances(instance_ids=iid)[0].instances[0].state
            # Get root device
            root_dev = self._conn.get_all_instances(instance_ids=iid)[0].instances[0].root_device_name
            # Create instance
            instance_id = Instance(iid, rid, name, state, root_dev)
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
                self._instance_list.append(instance.id)

    def change_instance_state(self, message, iid, expected_state, no_hot_snap):
        """
        Start or stop instance
        Will wait until the expected state or until timeout will be reached

        :param message: the message to inform what will happen
        :type message: str

        :param instance_id: instance ID
        :type instance_id: object

        :param expected_state: instance expected state state
        :type expected_state: str

        :param no_hot_swap: request cold or host snapshot
        :type no_hot_swap: bool

        :returns: int
        """
        retry = 5
        if no_hot_snap is True:
            if self._dry_run is False:
                if expected_state == 'stopped':
                    self.logger.info('Instance is going to be shutdown')
                    self._conn.stop_instances(instance_ids=[iid.instance_id])
                elif expected_state == 'running':
                    self.logger.info('Instance is going to be started')
                    self._conn.start_instances(instance_ids=[iid.instance_id])

                counter = 0
                while self._conn.get_all_instances(instance_ids=iid.instance_id)[0].instances[0].state != expected_state:
                    self.logger.debug(''.join(['Waiting for ', expected_state,
                                               ' state...', str(counter),
                                               '/', str(self._timeout)]))
                    counter += retry
                    if counter <= self._timeout:
                        time.sleep(retry)
                    else:
                        self.logger.error('Timeout exceded')
                        return 1
                self.logger.info(''.join(['Instance ', iid.instance_id, ' now ',
                                          expected_state, ' !']))
                return 0
            else:
                self.logger.info(' '.join(['Instance will be', expected_state]))
        return 0

    def make_snapshot(self):
        """
        Create snapshot on selected Instances ids
        """

        if (len(self._instances) == 0):
            print('No instances found with those parameters !')
        else:
            counter = 0
            for iid in self._instances:
                self.logger.info(''.join(['Working on instance ',
                                          iid.instance_id,
                                          ' (', iid.name, ')']))

                # Pausing VM and skip if failed
                if iid.initial_state == 'running':
                    if self.change_instance_state('Shutting down instance',
                                                  iid,
                                                  'stopped',
                                                  self._no_hot_snap) != 0:
                        continue

                # Creating Snapshot
                disks = iid.get_disks()
                for vol, device in disks.iteritems():
                    # Removing root device if required
                    if self._no_root_device is True:
                        if device == iid.root_dev:
                            self.logger.info('Not snapshoting root device')
                            continue
                    # Make snapshot
                    cur_snap = ' '.join(['  -', iid.instance_id,
                                         ': snapshoting', device,
                                         '(', vol, ')'])
                    if self._dry_run is False:
                        snap_id = self._conn.create_snapshot(vol,
                                                             ''.join([iid.instance_id,
                                                                      ' (',
                                                                      iid.name,
                                                                      ') - ',
                                                                      device,
                                                                      ' (', vol,
                                                                      ')']))
                        self.logger.info(' '.join([cur_snap,
                                                  str(snap_id.id)]))
                    else:
                        self.logger.info(cur_snap)

                # Starting VM if was running
                if iid.initial_state == 'running':
                    self.change_instance_state('Starting instance', iid,
                                               'running', self._no_hot_snap)

                # Limit the number of backups if requested
                if self._limit != -1:
                    counter += 1
                    if counter >= self._limit:
                        self.logger.info(' '.join(['The requested limit of',
                                                   'snapshots has been',
                                                   'reached:',
                                                   str(self._limit)]))
                        break


def main():
    """
    Main - manage args
    """
    global region, key_id, access_key, instance, action, tag

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
                        default=''.join([os.path.expanduser("~"),
                                         '/.aws_cred']),
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
    parser.add_argument('-H', '--no_hot_snap',
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

    parser.add_argument('-f', '--file_output', metavar='FILE',
                        default=None, action='store', type=str,
                        help='Set an output file')
    parser.add_argument('-s', '--stdout', action='store_true', default=True,
                        help='Log output to console (stdout)')
    parser.add_argument('-v', '--verbosity', metavar='LEVEL', default='INFO',
                        type=str, action='store',
                        help='Verbosity level: DEBUG/INFO/ERROR/CRITICAL')

    parser.add_argument('-V', '--version',
                        action='version', version='v0.1 Licence GPLv2',
                        help='Print version number')

    # Print help if no args supplied
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    a = parser.parse_args()

    # Setup loger
    setup_log(console=a.stdout, log=a.file_output, level=a.verbosity)

    # Read credential file and override by command args
    if os.path.isfile(a.credentials):
        if os.access(a.credentials,  os.R_OK):
            config = ConfigParser.ConfigParser()
            config.read([str(a.credentials)])
            if a.region is None:
                a.region = config.get(a.profile, 'aws_region')
            if a.access_key is None:
                a.access_key = config.get(a.profile, 'aws_secret_access_key')
            if a.key_id is None:
                a.key_id = config.get(a.profile, 'aws_access_key_id')
        else:
            print('fail', "Can't have permission to read credentials file")
            sys.exit(1)

    # Exit if no instance or tag has been set
    if a.instance is None and a.tags is None:
        print(' '.join(['[FAIL] Please set at least an instance ID',
                        'or a tag with its value']))
        sys.exit(1)
    else:
        # Create action
        selected_intances = ManageSnapshot(a.region, a.key_id, a.access_key,
                                           a.instance, a.tags, a.dry_run,
                                           a.timeout, a.no_hot_snap, a.limit,
                                           a.no_root_device)
        # Launch snapshot
        selected_intances.make_snapshot()

        sys.exit(0)

if __name__ == "__main__":
    main()
