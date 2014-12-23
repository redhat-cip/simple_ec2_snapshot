#!/usr/bin/env python
# encoding: utf-8
# Made by Pierre Mavro / Deimosfr

# Dependancies:
# - python colorama
# - python boto
# On Debian: aptitude install python-colorama python-boto

import argparse
import sys
import boto.ec2
# import time
from colorama import init, Fore


def print_color(mtype, message=''):
    """@todo: Docstring for print_text.

    :mtype: set if message is 'ok', 'updated', '+', 'fail' or 'sub'
    :type mtype: str
    :message: the message to be shown to the user
    :type message: str

    """

    init(autoreset=True)
    if (mtype == 'ok'):
        print(Fore.GREEN + 'OK')
    elif (mtype == '+'):
        print('[+] ' + message + '...'),
    elif (mtype == 'fail'):
        print(Fore.RED + "\n[!]" + message)
    elif (mtype == 'sub'):
        print('  -> ' + message + '...'),
    elif (mtype == 'subsub'):
        print("\n    -> " + message + '...'),
    elif (mtype == 'up'):
        print(Fore.CYAN + 'UPDATED')


class ManageSnapshot:
    """
    Manage AWS Snapshot
    """

    # Constructor
    def __init__(self, region, key_id, access_key, instance, tag, action):
        self._region = region
        self._key_id = key_id
        self._access_key = access_key
        self._instance = ','.split(instance)
        self._tag = tag
        self._action = action
        self._conn = self._validate_aws_connection()
        self._items = []
        # If no instances specified select all
        if (self._instance[0] == 'all'):
            # If no tags are specified, print everything
            if (self._tag[0] != None):
                self._get_filtred_instances()
            else:
                # Set tags filters
                self._get_filtred_instances()

    def _validate_aws_connection(self):
        """
        Validate if AWS connection is OK or not
        """
        c = False
        try:
            c = boto.ec2.connect_to_region(self._region,
                                           aws_access_key_id=self._key_id,
                                           aws_secret_access_key=self._access_key)
        except IndexError, e:
            print("Can't connect with the credentials: %s" % e)
            sys.exit(1)
        return(c)

    def _get_filtred_instances(self):
        """
        Print filtred instances
        :returns: @todo
        """

    def get_listInstances(self):
        """
        Get all instances
        """


        stats = self._conn.get_all_volume_status()
        for stat in stats:
            print(stat)
            print "id %s status %s %s" % (stat.id, stat.volume_status, stat.zone)


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
                        action='store',
                        type=str,
                        default='all',
                        metavar='INSTANCE_NAME',
                        help='Instance ID (ex: i-00000000')
    parser.add_argument('-t',
                        '--tag',
                        action='store',
                        type=str,
                        default=[None, None],
                        metavar='TAG',
                        nargs=2,
                        help='Select a tag with its value (ex: tagname value)')
    parser.add_argument('-o',
                        '--action',
                        choices=['list', 'snapshot', 'restore'],
                        required=True,
                        action='store',
                        help='List available instances')
    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version='v0.1 Licence GPLv2',
                        help='Print version number')

    a = parser.parse_args()

    # Print help if no args supplied
    if (len(sys.argv) == 1):
        parser.print_help()
        sys.exit(1)

    action = a.action
    snapshot = ManageSnapshot(a.region, a.key_id, a.access_key, a.instance,
                              a.tag, a.action)
    if (action == 'list'):
        snapshot.print_filtred_instances()


def main():
    """
    Main function
    """
    args()

if __name__ == "__main__":
    main()
