#!/usr/bin/env python

from zbxapi import *

def main():
	demo = zabbixapi()
	groups = demo.group_get()
	for group in groups:
		print group

if __name__ == "__main__":
	main()
