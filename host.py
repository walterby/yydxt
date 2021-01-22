#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from zbxapi import *
import json
import xlrd

def excel_info():
	data = xlrd.open_workbook("zabbix.xlsx")
	data.sheet_names()
	table = data.sheets()[0]
	nrows = table.nrows - 1
	print(table.nrows)
	hosts = []
	for i in range(nrows):
		host = {}
		location = table.cell(i+1,2).value
		ip = table.cell(i+1,3).value
		site_name = table.cell(i+1,4).value
		visiable_name = location.strip() + "-" + site_name.strip() + "-" + ip.strip()
		#print visiable_name
		host["name"] = visiable_name
		host["host"] = ip
		hosts.append(host)

	return json.dumps(hosts)

def main():
	hosts = json.loads(excel_info())
	for host in hosts:
		#print host["name"]
		host["ip"] = host["host"]
		host["groupid"] = 52
		host["templateid"] = 10995
		host["inventory"] = {}
		host["inventory"]["tag"] = ""
		host["status"] = 0
		print(json.dumps(host))

		demo = zabbixapi()
		result = demo.host_create(host)
		print(result)
if __name__ == "__main__":
	main()
