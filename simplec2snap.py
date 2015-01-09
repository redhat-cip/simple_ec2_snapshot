#!/usr/bin/env python
# encoding: utf-8
# Made by Pierre Mavro / Deimosfr
# eNovance / RedHat

# Dependancies:
# - python boto
# On Debian: aptitude install python-boto

import argparse
import sys
import boto.ec2
import time


def custom_print(mtype, message=''):
    """@todo: Docstring for print_text.

    :mtype: set if message is 'ok', 'updated', '+', 'fail' or 'sub'
    :type mtype: str
    :message: the message to be shown to the user
    :type message: str
    """

    if mtype == '+':
        print(''.join(['[+] ', message]))
    elif mtype == 'sub':
        print(''.join(['  => ', message])),
    elif mtype == 'subsub':
        print(''.join(['    - ', message])),
    elif mtype == 'fail':
        print(''.join(['[FAIL] ', message]))


class Instance:
    """
    Contruct instances and set/get attached disks
    """

    def __init__(self, iid, rid, name):
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
        self.disks = {}

    def add_disk(self, vol, device):
        """
        Add a disk to an instance

        :vol: set the volume id
        :type vol: str
        :device: set the device path
        """
        self.disks[vol] = device

    def get_disks(self):
        """
        Get the list of disks with mount points

        :returns: Dictionary of volumes with mount points
        :type return: dict
        """
        return(self.disks)


class ManageSnapshot:
    """
    Manage AWS Snapshot
    """

    def __init__(self, region, key_id, access_key, instance_list, tags, action):
        self._region = region
        self._key_id = key_id
        self._access_key = access_key
        self._instance_list = instance_list
        self._tags = tags
        self._action = action
        self._instances = []
        self._conn = self._validate_aws_connection()
        self._filter_instances()
        self._set_instance_info()

    def _validate_aws_connection(self):
        """
        Validate if AWS connection is OK or not
        """
        c = False
        custom_print('+', 'Validating AWS connection')
        try:
            c = boto.ec2.connect_to_region(self._region,
                                           aws_access_key_id=self._key_id,
                                           aws_secret_access_key=self._access_key)
        except IndexError, e:
            print("Can't connect with the credentials: %s" % e)
            sys.exit(1)
        return(c)

    def _set_instance_info(self):
        """
        Set instances info from an ID
        This will construct an object containing disks attributes

        :instance_list: list of instance ID
        :type instance_list: list
        :returns: nothing
        """
        # Remove doubles
        self._instance_list = list(set(self._instance_list))
        # Create Instance object
        for iid in self._instance_list:
            # Get reservation id
            rid = self._conn.get_all_instances(instance_ids=iid)[0].id
            # Set instance name
            name = self._conn.get_all_instances(instance_ids=iid)[0].instances[0].tags['Name']
            # Create instance
            instance_id = Instance(iid, rid, name)
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
        custom_print('+', 'Getting instances information')
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

    def get_Instances(self):
        """
        Get all instances
        """
        if (len(self._instances) == 0):
            print('No instances found with those parameters !')
        else:
            for iid in self._instances:
                custom_print('sub', ''.join([iid.instance_id, ' (', iid.name, ')', "\n"]))
                disks = iid.get_disks()
                for vol, device in disks.iteritems():
                    custom_print('subsub', ''.join([vol, ' - ', device, "\n"]))

    def make_Snapshot(self, no_hot_backup):
        """
        Create snapshot on selected Instances ids
        """
        for iid in self._instances:
            custom_print('+', ''.join([iid.instance_id, ' (', iid.name, ')']))

            # Pausing VM
            if no_hot_backup is True:
                custom_print('sub', "Shutting down instance\n")
                self._conn.stop_instances(instance_ids=[iid.instance_id])
                while self._conn.get_all_instances(instance_ids=iid.instance_id)[0].instances[0].state != 'stopped':
                    custom_print('subsub', ''.join(['Please wait while stopping...', "\n"]))
                    time.sleep(5)
                custom_print('sub', "Now stopped !\n")

            # Creating Snapshot
            custom_print('sub', "Creating Snapshot\n")
            disks = iid.get_disks()
            for vol, device in disks.iteritems():
                snap_id = self._conn.create_snapshot(vol,
                                                     ''.join([iid.instance_id,
                                                              ' (',
                                                              iid.name,
                                                              ') - ',
                                                              device,
                                                              ' (',
                                                              vol,
                                                              ')']))
                custom_print('subsub', ' '.join(['Creating snapshot of',
                                                 device,
                                                 '(',
                                                 vol,
                                                 ') :',
                                                 str(snap_id.id),
                                                 "\n"])),

            # Starting VM
            if no_hot_backup is True:
                custom_print('sub', "Starting instance\n")
                self._conn.start_instances(instance_ids=[iid.instance_id])
                while self._conn.get_all_instances(instance_ids=iid.instance_id)[0].instances[0].state != 'running':
                    custom_print('subsub', ''.join(['Please wait while starting...', "\n"]))
                    time.sleep(5)
                custom_print('sub', "Instance started !\n")


def args():
    """
    Manage args
    """
    global region, key_id, access_key, instance, action, tag

    # Main informations
    parser = argparse.ArgumentParser(
        description='Simple EC2 Snapshot utility',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # Default args
    parser.add_argument('-r',
                        '--region',
                        action='store',
                        type=str,
                        required=True,
                        metavar='REGION',
                        help='Set AWS region (ex: eu-west-1)')
    parser.add_argument('-k',
                        '--key_id',
                        action='store',
                        type=str,
                        required=True,
                        metavar='KEY_ID',
                        help='Set AWS Key ID')
    parser.add_argument('-a',
                        '--access_key',
                        action='store',
                        type=str,
                        metavar='ACCESS_KEY',
                        required=True,
                        help='Set AWS Access Key')
    parser.add_argument('-i',
                        '--instance',
                        action='append',
                        default=[],
                        metavar='INSTANCE_ID',
                        help=' '.join(['Instance ID (ex: i-00000000 or all)']))
    parser.add_argument('-t',
                        '--tags',
                        action='append',
                        type=str,
                        default=[],
                        metavar='ARG',
                        nargs=2,
                        help='Select tags with their values (ex: tagname value)')
    parser.add_argument('-o',
                        '--action',
                        choices=['list', 'snapshot'],
                        required=True,
                        action='store',
                        help='Set action to make')
    parser.add_argument('-H',
                        '--no_hot_backup',
                        action='store_true',
                        default=False,
                        help=' '.join(['Make cold backup for a better',
                                       'consistency (Recommended)']))
    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version='v0.1 Licence GPLv2',
                        help='Print version number')

    # Print help if no args supplied
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    a = parser.parse_args()

    # Exit if no instance or tag has been set
    if a.instance is None and a.tags is None:
        custom_print('fail', ' '.join(['Please set at least an instance ID',
                                      'or a tag with its value']))
        sys.exit(1)
    else:
        # Create action
        action = a.action
        selected_intances = ManageSnapshot(a.region, a.key_id, a.access_key,
                                           a.instance, a.tags, a.action)
        # Launch chosen action
        if action == 'list':
            selected_intances.get_Instances()
        elif action == 'snapshot':
            selected_intances.make_Snapshot(a.no_hot_backup)
        sys.exit(0)

def main():
    """
    Main function
    """
    args()

if __name__ == "__main__":
    main()
