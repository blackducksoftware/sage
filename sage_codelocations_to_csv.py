#!/usr/bin/python

# sage_codelocations_to_csv.py

import argparse
import csv
import json
import logging
import os
from pprint import pprint
import re
import sys

loggingLevel = logging.INFO
logging.basicConfig(stream=sys.stdout, format='%(threadName)s: %(asctime)s: %(levelname)s: %(message)s', level=loggingLevel)


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.2f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.2f %s%s" % (num, 'Yi', suffix)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract codelocations to CSV")

    group1 = parser.add_argument_group('required arguments')
    group1.add_argument('--input', dest='json_file_input', required=True, help="File containing Sage output e.g. sage_says.json")
    group1.add_argument('--output', dest='csv_file_output', required=True, help="Output CSV file")

    args = parser.parse_args()

    if os.path.exists(args.csv_file_output) and os.path.samefile(args.json_file_input, args.csv_file_output):
        print("Error, input and output file cannot be the same")
        sys.exit(-1)

    with open(args.json_file_input, 'r') as jf:
        logging.info("Loading data from %s...", args.json_file_input)
        sageJson = json.load(jf)
        logging.info("Loaded data for %i codelocations across %i projects", len(sageJson['scans']), len(sageJson['projects']))

    hub_25835_affected_versions = ['2020.8', '2020.10']
    for h in hub_25835_affected_versions:
        if sageJson['hub_version']['version'].startswith(h):
            logging.warning("Scan summaries may be incorrect showing only 1 entry (ref. HUB-25835)")
            logging.warning("Affected Hub versions: %s", hub_25835_affected_versions)

    projectDict = {}
    versionDict = {}
    for project in sageJson['projects']:
        m = re.match(r".*/projects/(.*)", project['url'])
        projectId = m.group(1)
        projectDict[projectId] = project['name']
        for version in project['versions']:
            m = re.match(r".*/versions/(.*)", version['url'])
            versionId = m.group(1)
            versionDict[versionId] = version['versionName']

    f = open(args.csv_file_output, 'w', newline='', encoding='utf-8')
    w = csv.writer(f)

    # Future enhancement: add more detail about too frequent scanning

    columns = ['codelocationId',
               'scanSize',
               'scanSizeReadable',
               'createdAt',
               'updatedAt',
               'summaries',
               'frequent',
               'latestSummary',
               'latestCreatedBy',
               'latestCreatedAt',
               'latestUpdatedAt',
               'latestStatus',
               'latestScanType',
               'latestMatchCount',
               'latestHostName',
               'latestBaseDirectory',
               'projectId',
               'versionId',
               'project',
               'version',
               'codelocation']
    w.writerow(columns)

    i = 0
    for codelocation in sageJson['scans']:
        mappedProjectVersion = ""
        projectId = ""
        project = ""
        versionId = ""
        version = ""
        if 'mappedProjectVersion' in codelocation:
            mappedProjectVersion = codelocation['mappedProjectVersion']
            m = re.match(r".*/projects/(.*)/versions/(.*)", mappedProjectVersion)
            projectId = m.group(1)
            if projectId in projectDict:
                project = projectDict[projectId]
            else:
                logging.warning("index %i projectId %s not found in projectDict", i, projectId)
                project = "ERROR: NOT IN PROJECT DICT!"
            versionId = m.group(2)
            if versionId in versionDict:
                version = versionDict[versionId]
            else:
                logging.warning("index %i versionId %s not found in versionDict", i, versionId)
                version = "ERROR: NOT IN VERSION DICT!"
        num_summaries = len(codelocation['scan_summaries'])

        latest_summary_timestamp = ""
        latest_summary_createdAt = ""
        latest_summary_updatedAt = ""
        latest_summary_status = ""
        latest_summary_createdBy = ""
        latest_summary_matchCount = ""
        latest_summary_baseDirectory = ""
        latest_summary_hostName = ""
        latest_summary_scanType = ""
        for summary in codelocation['scan_summaries']:
            if 'createdAt' in summary:
                ts = summary['createdAt']
            elif 'updatedAt' in summary:
                ts = summary['updatedAt']
            else:
                logging.warning("no createdAt or updatedAt in summary")
                pprint(summary)
                continue
            if not latest_summary_timestamp:
                latest_summary_timestamp = ts
            if ts >= latest_summary_timestamp:
                latest_summary_timestamp = ts
                latest_summary_createdBy = summary['createdByUserName']
                latest_summary_createdAt = summary['createdAt'] if 'createdAt' in summary else ""
                latest_summary_updatedAt = summary['updatedAt']
                latest_summary_status = summary['status']
                latest_summary_scanType = summary['scanType']
                latest_summary_matchCount = summary['matchCount']
                latest_summary_hostName = summary['hostName']
                latest_summary_baseDirectory = summary['baseDirectory']

        m = re.match(r".*/codelocations/(.*)", codelocation['url'])
        codelocationId = m.group(1)

        row = [codelocationId,
               codelocation['scanSize'],
               sizeof_fmt(codelocation['scanSize']),
               codelocation['createdAt'],
               codelocation['updatedAt'],
               num_summaries,
               True if 'high_freq_scan_message' in codelocation else "",
               latest_summary_timestamp,
               latest_summary_createdBy,
               latest_summary_createdAt,
               latest_summary_updatedAt,
               latest_summary_status,
               latest_summary_scanType,
               latest_summary_matchCount,
               latest_summary_hostName,
               latest_summary_baseDirectory,
               projectId,
               versionId,
               project,
               version,
               codelocation['name']]
        w.writerow(row)
        i += 1

    logging.info("Output written to: %s", args.csv_file_output)
    sys.exit(0)
