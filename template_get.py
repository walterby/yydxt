#!/usr/bin/env python

from zbxapi import *

def main():
	demo = zabbixapi()
	template = demo.template_get()
	for temp in template:
		print(temp["templateid"],temp["name"])

if __name__ == "__main__":
	main()
