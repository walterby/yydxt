#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# todo
#  function
#  query host by hostid
#  query group by grouid
#  query template by templateid
# 权限说明：
# superadmin 导入
# admin 导出

import requests
import sys
import logging
import json
from pyzabbix import ZabbixAPI, ZabbixAPIException
import logging
import xlwt
import csv

from urllib3.exceptions import InsecureRequestWarning
requests.urllib3.disable_warnings(InsecureRequestWarning)


# StreamHandler
stream_handler = logging.StreamHandler(sys.stdout)
#stream_handler.setLevel(level=logging.DEBUG)
py_logger = logging.getLogger("pyzabbix")
py_logger.addHandler(stream_handler)
py_logger.setLevel(logging.INFO) # INFO, DEBUG, WARNING

# FileHandler
file_handler = logging.FileHandler('zbxtool.log')
#file_handler.setLevel(level=logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger("inventory.py")
logger.addHandler(file_handler)
logger.setLevel(level=logging.INFO) # INFO, DEBUG, WARNING



NOT_FOUND       = 2
NOT_MONITORED   = 1
MONITORED       = 0


# users = zapi.user.get(output='extend', getAccess=1, selectMedias='extend')

# get all groups from the user
def group_get_all(zapi):
    group = zapi.hostgroup.get(
        output='extend',
        selectHosts='extend',
        #selectInterfaces='extend',  # '["interfaceid"],
        real_hosts=1,
        monitored_hosts=True
    )

    return group


def group_status_get(zapi, group):
    group = zapi.hostgroup.get(
        output='extend',
        filter={'name': group}
    )

    return group


# get group ID
# return: groupid
def group_id_get(zapi, group):
    try:
        group = zapi.hostgroup.get(
            filter={"name": group},
            output=["groupid"]
        )
    except ZabbixAPIException as e:
        print(e)
        sys.exit()

    return group[0]["groupid"]


def group_create(zapi, group):
    group = zapi.hostgroup.create(
        name=group
    )

    return group

# 根据hostname名获取host信息
# todo hostname可以修改成列表
def host_info_get(zapi, hostname):
    host = zapi.host.get(
        filter={"host": hostname},
        output='extend',            #['name'],
        selectInterfaces='extend',  #'["interfaceid"],
        selectInventory='extend',    #['alias','contact'],
        selectTags='extend'
        #monitored_hosts=True
    )
    return host[0]

# update inventory tag
def host_tag_update(zapi, hostID, InventoryTag):
    host = zapi.host.update(
        hostid=hostID,
        inventory_mode=0,
        inventory={"tag": InventoryTag}
    )
    return host


# 检查host监控状态
# 如果返回值大于等于1，表示有效监控。
# host = 主机名
def host_status_get(zapi, host):
    try:
        host = zapi.host.get(
            filter={"host": host},
            output=['status'],
        )
    except ZabbixAPIException as e:
        print(e)
        sys.exit()

    # host没在监控系统中找到
    # -1：监控没加
    if not host:
        return NOT_FOUND
    # host已监控
    # 1：监控已添加 && 监控关闭
    # 0：监控已添加 && 监控开启
    else:
        return int(host[0]['status'])

def host_id_get(zapi, host):
    try:
        host = zapi.host.get(
            filter={"host": host},
            output=["hostid"],
        )
    except ZabbixAPIException as e:
        print(e)
        logger.info(e)
        sys.exit()

    return host

# TODO
#  增加监控
#  hostName          监控名称
#  hostGroupName     组ID
#  ip                IP地址
#  templateId        模版ID
#
def host_create_test(zapi, hostName, GroupName, ip, templateId):
    host = zapi.host.create(
        host=hostName,
        interfaces=[{"type":1,
                    "main":1,
                    "useip":1,
                    "ip": ip,
                    "dns":"",
                    "port":10050
                    }],
        groups=[{"groupid": 39}],
        # tags=[{"tag": "hostTag"},{"value": "hostTagValue"}],    # hostTag, hostTagValue TODO
        templates=[{"templateid": templateId}],
        inventory_mode=0,
        # inventory={"macaddress_a": "macAddress"},               # macAddress TODO
    )
    return host


# hostName: visName
# host["group"]:    group name
# host["name"]:     visible name of the host
#
def host_create(zapi, hosts):
    logger.info("function host_create")
    for host in hosts:
        group = group_status_get(zapi, host["group"])
        print("group:{0}".format(group))
        print("host:{0}".format(host))

        # if group is not exist, create new group.
        if not group:
            groupId = group_create(zapi, host["group"])
            logger.info('Group add: {0}'.format(groupId))

        groupId = group_status_get(zapi, host["group"])[0]["groupid"]
        # print("groupid:{0}".format(groupid))

        name = hostname_check(host["name"])
        # create new host
        try:
            host_new = zapi.host.create(
                host=host["host"],
                interfaces=[{
                    "type": host["type"],
                    "useip": 1,
                    "ip": host["ip"],
                    "dns": "",
                    "port": host["port"],
                    "main": 1
                }],
                groups=[{"groupid": groupId}],
                name=name,
                inventory_mode=1,
                inventory={
                    "serialno_a": host["serialno_a"],
                    "serialno_b": host["serialno_b"],
                    "location": host["location"],
                    "os": host["os"]
                },
                tags=[{"tag": host["tag"],"value": host["tagvalue"]}]
            )
            logger.info('Host add: {0}'.format(host_new))
        except ZabbixAPIException as e:
            print(e)
            #sys.exit()

    return True

# Json第一行不缺少request里的key
def host_update(zapi, hosts):
    logger.info("function host_update")
    create_num = 0
    update_num = 0
    for host in hosts:
        group = group_status_get(zapi, host["group"])
        if not group:
            groupId = group_create(zapi, host["group"])
            logger.info('Group add: {0}'.format(groupId))
        # 组里
        groupId_new = group_status_get(zapi, host["group"])[0]["groupid"]
        if host["name"]:
            name = hostname_check(host["name"])
        else:
            name = ""
        hostStatus = host_status_get(zapi, host["host"])

        if hostStatus is NOT_FOUND:
            # HOSTCREATE
            try:
                host_new = zapi.host.create(
                    host=host["host"],
                    interfaces=[{
                        "type": host["type"],
                        "useip": 1,
                        "ip": host["ip"],
                        "dns": "",
                        "port": host["port"],
                        "main": 1
                    }],
                    groups=[{"groupid": groupId_new}],
                    name=name,
                    inventory={
                        "serialno_a": host["serialno_a"],
                        "serialno_b": host["serialno_b"],
                        "location": host["location"],
                        "os": host["os"]
                    },
                    tags=[{"tag": host["tag"],"value": host["tagvalue"]}]
                )
                logger.info("Host add: {0},{1},{2}".format(host_new, name, host["ip"]))
            except ZabbixAPIException as e:
                print(e)
                logger.info(e)
            create_num += 1
        else:
            #HOSTUPDATE
            # add hostid
            hostid = host_id_get(zapi, host["host"])[0]["hostid"]
            print(hostid)
            groupId_old_tmp = zapi.host.get(
                filter={"hostid": hostid},
                selectGroups="extend",
                output=["host"]
            )
            print("##{0}".format(groupId_new))
            groupId_old = []
            group_tmp = []

            for group in groupId_old_tmp[0]["groups"]:
                print("{0}\n".format(group))
                group_old = {"groupid": group["groupid"]}
                groupId_old.append(group["groupid"])
                group_tmp.append(group_old)

            if groupId_new not in groupId_old:
                group_new = {"groupid": groupId_new}
                group_tmp.append(group_new)

            print(group_tmp)
            try:
                host_update = zapi.host.update(
                    host=host["host"],
                    hostid=hostid,
                    # 添加的话会导致有模板的主机不能更新
                    #interfaces=[{
                    #    "type": host["type"],
                    #    "useip": 1,
                    #    "ip": host["ip"],
                    #    "dns": "",
                    #    "port": host["port"],
                    #    "main": 1
                    #}],
                    groups=group_tmp,
                    name=name,
                    inventory={
                        "serialno_a": host["serialno_a"],
                        "serialno_b": host["serialno_b"],
                        "location": host["location"],
                        "os": host["os"]
                    },
                    tags=[{"tag": host["tag"], "value": host["tagvalue"]}]
                )
                logger.info("Host update: {0},{1},{2},".format(host_update, name, host["ip"]))
            except ZabbixAPIException as e:
                print(e)
                logger.info(e)
            update_num += 1
    logger.info("create_num: {0}\tupdate_num: {1}\ttotal: {2}".format(create_num, update_num, create_num+update_num))
    return True

def host_delete(zapi, host):
    host = zapi.host.delete([hostid])


def hostname_check(name):
    if name.find(".") > 0:
        # delete ip on visible name
        tmp = name.split("-")[:-1]
        str = "-".join(tmp)
    else:
        str = name

    str = str.replace('Qingdao','QD')
    str = str.replace('Ningbo','NB')
    str = str.replace('ZhengZhou','ZZ')
    str = str.replace('XiaMenCDC','CDC-XM')
    str = str.replace('HangZhouCDC','CDC-HZ')
    str = str.replace('FoShan','FS')
    str = str.replace('cctv', 'CCTV')
    str = str.replace('door', 'DOOR')
    str = str.replace('Maxhub', 'MAXHUB')

    print(str)
    return str

def get_httpid(zapi, http):
    http = zapi.httptest.get(
        output=["httptestid","name"],
        hostids=[http],
    )
    return http

def get_http_status(zapi, httpid):
    http = zapi.httptest.get(
        output="extend",
        httptestids=httpid,
        selectSteps="extend",
        monitored=1
    )
    return http

def get_item(zapi, host, item):
    item = zapi.item.get(
        #output="extend",
        output=["name","key_","lastvalue"],
        hostids=[host],
        search={"key_": item},
        webitems=1,
        sortfield="name"
    )
    return item

def get_trigger(zapi, host):
    trigger = zapi.trigger.get(
        hostids=[host],
        output="extend"
    )
    return trigger

# def host_create(zapi, groupName, hostIP, hostName, templateName):
#     hostGroupID = group_get(zapi, groupName)
#     templateID = templateID_get(zapi, templateName)
#     host = zapi.host.create(
#         host=hostIP,
#         name=hostName,
#         groups=[{"groupid": hostGroupID}],
#     )


# 根据模版名称获取模版ID
def template_id_get(zapi, templateName):
    try:
        template = zapi.template.get(
            filter={"host": [templateName]},
            output="extend",
        )
    except ZabbixAPIException as e:
        print(e)
        sys.exit()

    if template:
        return template[0]["templateid"]
    else:
        print("Not found {0}'s templateid".format(templateName))
        return 0




# Todo
#  主机组信息导出
#  保存到csv
#  返回Json
# def group_info_export():


# save csv file named csvfile
def json2csv(jsonfile, csvfile):
    inputFile = open(jsonfile)
    outputFile = open(csvfile, 'w+')
    data = json.load(inputFile) #load json content
    inputFile.close() #close the input file
    output = csv.writer(outputFile) #create a csv.write
    # header row
    output.writerow(data[0].keys())
    for row in data:
        output.writerow(row.values())

    return True



#  save Json file name jsonfile
#  return Json
def csv2json(csvfile, jsonfile):
    # read csv to dict
    arr = []

    with open(csvfile) as csvFile:
        csvReader = csv.DictReader(csvFile)
        # print(csvReader)
        for csvRow in csvReader:
            arr.append(csvRow)
    # write the data to a json file
    with open(jsonfile, "w") as jsonFile:
        jsonFile.write(json.dumps(arr, indent=4))

    return json.dumps(arr, indent=4)


# Todo
#  主机组信息导入
#  通过Json添加到监控
def group_info_import(zapi, jsfile):
    f = open(jsfile)
    data = json.load(f)
    f.close()

    # hosts = host_create(zapi, data)
    hosts = host_update(zapi, data)


# be careful!!
def inventory_delete_for_test(zapi):
    groups = group_get_all(zapi)
    for group in groups:
        print(group['groupid'])
        for host in group['hosts']:
            print(host['hostid'])
            host = zapi.host.delete(
                host['hostid']
            )
        group_delete = zapi.hostgroup.delete(
            group['groupid']
        )

    return True

# Todo
# json sort

"""
if hosts:
    host_id = hosts[0]["hostid"]
    #print("Found host id {0}".format(host_id))
    #print(json.dumps(hosts[0],sort_keys=True, indent=4, separators=(',', ':')))
    logger.info('Found host id {0}'.format(host_id))
    #logger.info('{0}'.format(json.dumps(hosts[0],sort_keys=True, indent=4, separators=(',', ':'))))

    try:
        items = zapi.item.get(
            output='extend',
            hostids=host_id,
            search={"key_":"logstash"}
        )
    except ZabbixAPIException as e:
        print(e)
        sys.exit()
    print("host item {0}".format(item))

else:
    print("No hosts found")
"""


#  主机组信息导出
#  保存Json文件
#  返回Json
def inventory2Json(zapi, saveFile):
    groups = group_get_all(zapi)
    #logger.info('\033[96m ############################ host group information ############################\033[00m')
    inventories = []
    # loop groups
    num = 0
    for group in groups:
        logger.debug('hostgroup name: \033[96m {0}\033[00m'.format(group['name']))
        # loop hosts
        for host in group['hosts']:
            hostStatus = host_status_get(zapi, host['host'])

            if hostStatus is MONITORED:
                # update inventory tag
                # host_tag_update(zapi, host['hostid'], "")

                # get host
                hostInfo = host_info_get(zapi, host['host'])

                """
                logger.debug('host info: host:{0}\nname:{1}\ninterface:{2}\ninventory:{3}'
                             .format(hostInfo['host'],
                                     hostInfo['name'],
                                     json.dumps(hostInfo['interfaces'], sort_keys=True, indent=4, separators=(',', ':')),
                                     json.dumps(hostInfo['inventory'], sort_keys=True, indent=4, separators=(',', ':'))
                                     )
                             )
                js_t = json.dumps(hostInfo['interfaces'], sort_keys=True, indent=4, separators=(',', ':'))
                """

                inventory = {}
                inventory["groupid"] = group["groupid"]
                inventory["group"] = group["name"]
                inventory["hostid"] = hostInfo["hostid"]
                inventory["host"] = hostInfo["host"]        # monitor name
                inventory["name"] = hostInfo["name"]        # monitor visiable name

                # todo: interfaces info need to be dict
                inventory["ip"] = hostInfo["interfaces"][0]["ip"]
                inventory["type"] = hostInfo["interfaces"][0]["type"]  # 1-agent, 2-snmp, 3-ipmi, 4-jmx
                inventory["port"] = hostInfo["interfaces"][0]["port"]

                #if hostInfo["inventory"]:
                try:
                    inventory["os"] = hostInfo["inventory"]["os"]
                    inventory["location"] = hostInfo["inventory"]["location"]
                    inventory["serialno_a"] = hostInfo["inventory"]["serialno_a"]
                    inventory["serialno_b"] = hostInfo["inventory"]["serialno_b"]
                except:
                    inventory["os"] = ""
                    inventory["location"] = ""
                    inventory["serialno_a"] = ""
                    inventory["serialno_b"] = ""

                try:
                    inventory["tag"] = hostInfo["tags"][0]["tag"]
                except:
                    inventory["tag"] = ""
                try:
                    inventory["tagvalue"] = hostInfo["tags"][0]["value"]
                except:
                    inventory["tagvalue"] = ""


                inventories.append(inventory)
                num += 1
                logger.info("inventory export: {0}".format(inventory))

            else:
                logger.info('{0} has stop monitored. '.format(host['host']))
                continue;
    logger.info("total export num: {0}".format(num))
    f = open(saveFile, "w+")
    f.write(json.dumps(inventories, sort_keys=True, indent=4, separators=(',', ':')))
    f.close()

    inventories = sorted(inventories, key = lambda x:(x["group"],x["name"]), reverse=False)
    return json.dumps(inventories)


def main():
    #zapi = ZabbixAPI(ZABBIX_SERVER_CM)
    #zapi.session.verify = False

    # Login to the Zabbix API
    #zapi.login('test-nhp', 'test')

    #inventories = json.loads(inventory2Json(zapi, "nhp.json"))
    #print("{0}".format(json.dumps(inventories, sort_keys=True, indent=4, separators=(',', ':'))))


    test = ZabbixAPI("")
    test.session.verify = False
    test.login("test","test")
    #host = host_id_get(cm03, 'NCT-API')[0]["hostid"]
    #http = get_httpid(cm03, host)
    #http = get_http_status(cm03, 371)
    #item = get_item(cm03, host, "web.test.rspcode[SCR Workbench,health check]")
    #trigger = get_trigger(cm03, host)

    # 导出到Json
    #inventories = inventory2Json(test, "test.json")

    # for delete
    #cm03.login("test","test")

    # f = open("cm2_niohouse.json")
    # data = json.load(f)
    # f.close()

    # 主机组导入
    group_info_import(test, "nio_hardware.json")
    #res = inventory_delete_for_test(cm03)
    #group = host_create(cm03, data)


    #group_get_status(cm03, 'SHDC/SERVER-Window')
    #json2csv("test.json", "sh-mlx.csv")
    #res = csv2json("test1.csv", "testtest.js")
    #res = csv2json("test.csv", "test.json")


    #print(js)
    #templateid = template_id_get(zapi, "apitest1")
    #print(templateid)

    #groupid = group_id_get(cm03, "testforapi")
    #status = host_status_get(zapi, "a")
    #print(status)
    #logger.info('get inventory information')
    #inventory = get_host_inventory(zapi, 'logstash-zbx-test')
    #logger.debug('Inventory: {0}'.format(inventory))

if __name__ == "__main__":
    main()
