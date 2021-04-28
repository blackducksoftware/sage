#!/usr/bin/python

# filter_activity.py

import argparse
import arrow
import csv
import datetime
import logging
import os.path
from pprint import pprint
import re
import sys

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Filter input file")

    parser.add_argument('--output', dest='csv_file_output', default=None, help="Output CSV file (STDOUT if None)");

    group1 = parser.add_argument_group('required arguments')
    group1.add_argument('--input', dest='csv_file_input', required=True, help="Input CSV file");

    args = parser.parse_args()

    if args.csv_file_output:
        if os.path.exists(args.csv_file_output) and os.path.samefile(args.csv_file_input, args.csv_file_output):
            print("Error, input and output file cannot be the same")
            sys.exit(-1)

    reader = csv.DictReader(open(args.csv_file_input))

    if args.csv_file_output:
        f = open(args.csv_file_output, 'w', newline='', encoding='utf-8')
        w = csv.writer(f)
    else:
        w = csv.writer(sys.stdout)

    w.writerow(reader.fieldnames)

    for row in reader:
        # TODO: add your filtering and processing here
        # pprint(row)

        # Example: omit row if phase in ['RELEASED', 'ARCHIVED']
        # if row['phase'] in ['RELEASED', 'ARCHIVED']:
        #    continue

        # Example: omit row if createdAt is within 100 days
        # if arrow.now() - arrow.get(row['createdAt']) < datetime.timedelta(days=int(100)):
        #    continue

        # Example: omit row if createdAt is after 2019-03
        # if arrow.get(row['createdAt']) > arrow.get("2019-03"):
        #    continue

        # Example: omit row if latestSummary or latestScanEvent is after 2019-11-01
        # cutoff = arrow.get("2019-11-01")
        # if row['latestSummary'] and arrow.get(row['latestSummary']) > cutoff:
        #    continue
        # if row['latestScanEvent'] and arrow.get(row['latestScanEvent']) > cutoff:
        #    continue

        # Example: omit row if latestNotableActivity is not empty
        # if row['latestNotableActivity']:
        #    continue

        w.writerow(row.values())
