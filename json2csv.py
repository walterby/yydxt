#!/usr/bin/env python3

import csv
import json
import sys

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

def main():
    jsonfile = sys.argv[1]
    csvfile = sys.argv[2]

    json2csv(jsonfile, csvfile)

if __name__ == "__main__":
    main()