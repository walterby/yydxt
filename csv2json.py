#!/usr/bin/env python3

import csv
import json
import sys

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

def main():
    csvfile = sys.argv[1]
    jsonfile = sys.argv[2]

    csv2json(csvfile, jsonfile)

if __name__ == "__main__":
    main()