#!/usr/bin/python

# sage_version_activity_to_csv.py

import argparse
from blackduck import Client
import csv
from datetime import datetime
from dateutil.parser import isoparse
import json
import logging
import os
from pprint import pprint
import re
import sys

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] {%(module)s:%(lineno)d} %(levelname)s - %(message)s"
)


def check_for_activity(events):
    """Look through all events for activity and return the following dict:
       {
           events: total number of events processed
           latestScanTimestamp: timestamp
           rescanned: count
           latestNotableTimestamp: timestamp
           notableCounts: dictionary of events not corresponding to routine scans and vulnerability activity
       }
    """
    latestScanTimestamp = None
    latestNotableTimestamp = None
    eventCounts = {}
    notableCounts = {}

    # Mundane events from automated activity:
    #   COMPONENT; Component Added/Deleted; triggered by blackduck_system
    #   COMPONENT; Policy Violation Detected/Cleared
    #   VULNERABILITY; Vulnerability Found; triggered by blackduck_system
    #   SCAN; Scan Mapped; by anyone
    #   SCAN; Matches Found; triggered by blackduck_system
    #
    # Other events indicate activity including:
    #   COMPONENT events with action = 'Adjustment Added', 'Adjustment Deleted', 'Comment Added', etc.
    #   etc.
    #
    scanEvents = 0
    rescanned = 0

    for event in events:
        eventType = event['objectData']['type']
        compositeKey = eventType + ":" + event['action']

        if compositeKey in eventCounts:
            eventCounts[compositeKey] += 1
        else:
            eventCounts[compositeKey] = 1

        if eventType == 'SCAN':
            scanEvents += 1
            if not latestScanTimestamp:
                latestScanTimestamp = event['timestamp']
            if isoparse(event['timestamp']) > isoparse(latestScanTimestamp):
                latestScanTimestamp = event['timestamp']

        # high frequency scanning is best checked from codelocations instead of project versions

        if eventType == 'SCAN' and event['action'] == 'Rescanned':
            rescanned += 1
            continue

        # not counted as manual activity, likely from automation
        if eventType == 'SCAN' and event['action'] == 'Scan Mapped':  # triggered by both automation and manual
            continue
        if eventType == 'SCAN' and event['action'] == 'Matches Found' and event['triggerData']['name'] == 'blackduck_system':
            continue
        if eventType == 'VULNERABILITY' and event['action'] == 'Vulnerability Found':  # triggered by both automation and manual
            continue
        if eventType == 'COMPONENT' and event['action'] == 'Component Added' and event['triggerData']['name'] == 'blackduck_system':
            continue
        if eventType == 'COMPONENT' and event['action'] == 'Component Deleted' and event['triggerData']['name'] == 'blackduck_system':
            continue
        if eventType == 'COMPONENT' and event['action'] == 'Policy Violation Detected':
            continue
        if eventType == 'COMPONENT' and event['action'] == 'Policy Violation Cleared':
            continue
        if eventType == 'POLICY' and event['action'] == 'Policy Rule Evaluated':
            continue
        if eventType == 'KB_COMPONENT' and event['action'] == 'KB Component Deprecated':
            continue
        if eventType == 'KB_COMPONENT_VERSION' and event['action'] == 'KB Component Version Deprecated':
            continue

        if not latestNotableTimestamp:
            latestNotableTimestamp = event['timestamp']
        if isoparse(event['timestamp']) > isoparse(latestNotableTimestamp):
            latestNotableTimestamp = event['timestamp']

        if compositeKey in notableCounts:
            notableCounts[compositeKey] += 1
        else:
            notableCounts[compositeKey] = 1

    resultDict = {'events': len(events),
                  'latestScanTimestamp': latestScanTimestamp,
                  'rescanned': rescanned,
                  'latestNotableTimestamp': latestNotableTimestamp,
                  'notableCounts': notableCounts}

    return resultDict


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.2f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.2f %s%s" % (num, 'Yi', suffix)


def process_project_version(project, version):
    m = re.match(r".*/projects/(.*)/versions/(.*)", version['url'])
    projectId = m.group(1)
    versionId = m.group(2)

    print("  {};  bom:".format(version['versionName']), end='', flush=True)
    if args.skip_bom:
        num_components = "skipped"
    else:
        url = f"/api/projects/{projectId}/versions/{versionId}/components"
        num_components = bd.get_json(url, params={'offset': 0, 'limit': 1})['totalCount']
    sys.stdout.write(str(num_components))
    sys.stdout.flush()

    # projectOwner
    project_owner = ""
    if 'projectOwner' in project:
        url = project['projectOwner']
        owner_dict = bd.get_json(url)
        project_owner = owner_dict['userName']

    # Look at project version codelocations as it is possible
    # to have mapped scan results but no history within the events
    sum_scanSize = 0
    sum_summaries = 0
    latest_summary_timestamp = None

    codelocations = version['scans']
    for codelocation in codelocations:
        m = re.match(r".*/codelocations/(.*)", codelocation['url'])
        codelocationId = m.group(1)

        sum_scanSize += codelocation['scanSize']

        summaries = codelocationsDict[codelocationId]['scan_summaries']
        sum_summaries += len(summaries)

        for summary in summaries:
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
            if isoparse(ts) > isoparse(latest_summary_timestamp):
                latest_summary_timestamp = ts

    # Look at event history for activity
    sys.stdout.write(";  events:")
    sys.stdout.flush()

    # There is a very nasty bug in the REST-API for this endpoint where if I return all the
    # results using a small page size it returns the correct number but overall incorrect results
    # with occasional duplicate keys.  However, if I use a page size large enough to get everything in
    # one go it fetches the results correctly.
    #
    # Passing a sort by timestamp ASC via params makes a multiple page fetch behave correctly.
    url = f"/api/journal/projects/{projectId}/versions/{versionId}"
    params = {'sort': "timestamp ASC"}
    events = list(bd.get_items(url, page_size=1000, params=params))

    sys.stdout.write(str(len(events)))

    activity = check_for_activity(events)

    sys.stdout.write("\n")

    return [
            projectId,
            versionId,
            project['name'],
            version['versionName'],
            project_owner,
            version['distribution'],
            version['phase'],
            version['createdAt'],
            version['createdBy'],
            len(codelocations),
            sum_scanSize,
            sizeof_fmt(sum_scanSize),
            sum_summaries,
            latest_summary_timestamp,
            num_components,
            activity['events'],
            activity['latestScanTimestamp'],
            activity['rescanned'],
            activity['latestNotableTimestamp'],
            activity['notableCounts'] if len(activity['notableCounts']) > 0 else None
    ]


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process Sage project versions and check Hub for notable activity")

    parser.add_argument("--no-verify", dest='verify', action='store_false', help="disable TLS certificate verification")
    parser.add_argument('--timeout', dest='timeout', default=15.0, help="Connection timeout in seconds")
    parser.add_argument('--retries', dest='retries', default=3, help="Maximum number of retries for a single request")
    parser.add_argument('--skip-bom', dest='skip_bom', action='store_true', default=None, help="Skip BOM lookup")

    group1 = parser.add_argument_group('required arguments')
    group1.add_argument('--input', dest='json_file_input', required=True, help="File containing Sage output e.g. sage_says.json")
    group1.add_argument('--output', dest='csv_file_output', required=True, help="Output CSV file")
    group1.add_argument("--token-file", dest='token_file', required=True, help="containing access token")

    args = parser.parse_args()

    if os.path.exists(args.csv_file_output) and os.path.samefile(args.json_file_input, args.csv_file_output):
        print("Error, input and output file cannot be the same")
        sys.exit(-1)

    with open(args.json_file_input, 'r') as jf:
        logging.info("Loading data from %s...", args.json_file_input)
        sageJson = json.load(jf)
        logging.info("Loaded data for %i codelocations across %i projects", len(sageJson['scans']), len(sageJson['projects']))

    with open(args.token_file, 'r') as tf:
        access_token = tf.readline().strip()

    bd = Client(
        base_url=sageJson['hub_url'],
        token=access_token,
        verify=args.verify,
        timeout=args.timeout,
        retries=args.retries,
    )

    projectDict = {}   # key:projectId: json
    pvDict = {}        # key:projectId: json array

    for project in sageJson['projects']:
        m = re.match(r".*/projects/(.*)", project['url'])
        projectId = m.group(1)
        projectDict[projectId] = project
        pvDict[projectId] = project['versions']

    codelocationsDict = {}  # key:codelocationId: json
    for codelocation in sageJson['scans']:
        m = re.match(r".*/codelocations/(.*)", codelocation['url'])
        codelocationId = m.group(1)
        codelocationsDict[codelocationId] = codelocation

    # Process project versions
    start_time = datetime.now()
    logging.info("Loading project versions complete, now processing each and every project version")

    f = open(args.csv_file_output, 'w', newline='', encoding='utf-8')
    w = csv.writer(f)

    columns = [
            'projectId',
            'versionId',
            'project',
            'version',
            'projectOwner',
            'distribution',
            'phase',
            'createdAt',
            'createdBy',
            'codelocations',
            'sumScanSize',
            'sumScanSizeReadable',
            'sumSummaries',
            'latestSummary',
            'bom',
            'events',
            'latestScanEvent',
            'rescanned',
            'latestNotableActivity',
            'notableActivityEvents']
    w.writerow(columns)

    projectCount = 0
    pvCount = 0
    for projectId in projectDict:
        projectCount += 1
        project = projectDict[projectId]
        print("Project ({}/{}) {}:".format(projectCount, len(projectDict), project['name']))

        versions = pvDict[projectId]
        for version in versions:
            row = process_project_version(project, version)
            w.writerow(row)
            f.flush()  # allow tail -f csv file
            pvCount += 1

    logging.info("Processing %i project versions complete, output written to: %s", pvCount, args.csv_file_output)
    logging.info("Elapsed time: %s", datetime.now() - start_time)

    sys.exit(0)
