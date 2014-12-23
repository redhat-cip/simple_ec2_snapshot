#!/usr/bin/env python
# encoding: utf-8
# Made by Pierre Mavro / Deimosfr

# Dependancies:
# - python colorama
# On Debian: aptitude install python-colorama

import argparse
import sys
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
        self.region = region
        self.key_id = key_id
        self.access_key = access_key
        self.instance = instance
        self.tag = tag
        self.action = action

    def get_listInstances(self):
        print self.action


def args():
    """
    Manage args
    """

    global region, key_id, access_key, instance, action, tag

    # Main informations
    parser = argparse.ArgumentParser(
        description='Amazon Snapshot utility',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # Default args
    parser.add_argument('-r',
                        '--region',
                        action='store',
                        type=str,
                        # required=True,
                        metavar='REGION',
                        help='Set AWS region (ex: eu-west-1)')
    parser.add_argument('-k',
                        '--key_id',
                        action='store',
                        type=str,
                        # required=True,
                        metavar='KEY_ID',
                        help='Set AWS Key ID')
    parser.add_argument('-a',
                        '--access_key',
                        action='store',
                        type=str,
                        metavar='ACCESS_KEY',
                        # required=True,
                        help='Set AWS Access Key')
    parser.add_argument('-i',
                        '--instance',
                        action='store',
                        type=str,
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

    if (a.region):
        region = a.region
    if (a.key_id):
        key_id = a.key_id
    if (a.access_key):
        access_key = a.access_key
    if (a.instance):
        instance = a.instance
    if (a.tag):
        tag = a.tag
    if (a.action):
        action = a.action
        snapshot = ManageSnapshot(region, key_id, access_key, instance, tag,
                                  action)
        if (action == 'list'):
            snapshot.get_listInstances()
    else:
        print 'You need to choose an action'
        sys.exit(1)


def main():
    """
    Main function
    """
    args()

if __name__ == "__main__":
    main()
