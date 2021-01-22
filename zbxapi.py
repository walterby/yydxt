# zabbix api

# -*- coding: utf-8 -*-

import urllib2
import json
import xlrd
import sys
import time

# zabbix user name & password
USER = ""
PASSWORD = ""

class zabbixapi:
    def __init__(self):
        self.url = "http://xx/zabbix/api_jsonrpc.php"
        self.header = {"Content-Type": "application/json"}
        self.authID = self.user_login()
    
    def user_login(self):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": USER,
                "password": PASSWORD
            },
            "id": 1
        })
        request = urllib2.Request(self.url, data)
        for key in self.header:
            request.add_header(key, self.header[key])
        result = urllib2.urlopen(request)
        response = json.loads(result.read())
        result.close()
        authID = response['result']
        return authID

    def data_get(self, data, hostip=""):
        request = urllib2.Request(self.url, data)
        for key in self.header:
            request.add_header(key, self.header[key])
        result = urllib2.urlopen(request)
        response = json.loads(result.read())
        result.close()
        return response

    def group_get(self):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": "extend"
            },
            "auth": self.authID,
            "id": 1
        })
        results = self.data_get(data)['result']
        return results

    def template_get(self):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "template.get",
            "params": {
                "output": "extend"
            },
            "auth": self.authID,
            "id": 1
        })
        results = self.data_get(data)['result']
        return results

# host
# host["host"]: Technical name of the host
# host["name"]: visible name of the host
# host["ip"]: IP
# host["groupid"]: groupid
# host["templateid"]:
# host["inventory"]["tag"]:
# host["status"]:
    def host_create(self, host):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "host.create",
            "params": {
                "host": host["host"],
                "name": host["name"],
                "interfaces": [
                    {
                        "type": 1,          # 1-agent; 2-SNMP; 3-IPMI; 4-JMX
                        "main": 1,
                        "port": 10050,
                        "ip": host["ip"],
                        "dns": "",
                        "useip": 1,         # 0-using DNS name; 1-using IP address; 
                    }
                ],
                "groups": [
                    {
                        "groupid": host["groupid"]
                    }
                ],
                "templates": [
                    {
                        "templateid": host["templateid"]
                    }
                ],
                "inventory_mode": 1,            # -1-disable; 0-manaual; 1-automatic
                "inventory": {
                    "tag": host["inventory"]["tag"]
                },
                "status": host["status"]		# 0-monitored host; 1-unmonitored host
            },
            "auth": self.authID,
            "id": 1
        })
        results = self.data_get(data)
        return results
