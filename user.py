#!/usr/bin/env python3

import requests
import sys
import logging
from pyzabbix import ZabbixAPI
#from requests.packages.urllib3.exceptions import InsecureRequestWarning

from urllib3.exceptions import InsecureRequestWarning
requests.urllib3.disable_warnings(InsecureRequestWarning)
#import socket

"""
stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)
log = logging.getLogger('pyzabbix')
log.addHandler(stream)
log.setLevel(logging.DEBUG)
"""


ZABBIX_SERVER = ''

zapi = ZabbixAPI(ZABBIX_SERVER)
zapi.session.verify = False


# Login to the Zabbix API
zapi.login('', '')

#
users = zapi.user.get(output='extend', getAccess=1,selectMedias='extend')


# unack_trigger_ids = [t['triggerid'] for t in unack_triggers]
for t in users:
    #print(t)
    print("{0}: {1}\t{2}\t{3}".format(t['alias'],
                                 t['attempt_ip'],
                                 t['attempt_clock'],
                               t['medias']))
    #t['unacknowledged'] = True if t['triggerid'] in unack_trigger_ids \
    #    else False

# Print a list containing only "tripped" triggers
"""
for t in triggers:
    if int(t['value']) == 1:
        # print(t)
        print("{0} - {1} {2} {3}".format(t['hosts'][0]['host'],
                                     t['description'],
                                     '(Unack)' if t['unacknowledged'] else '',
                                     t['priority'])
           )
"""