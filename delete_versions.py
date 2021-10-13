#!/usr/bin/python

# delete_versions.py

import argparse
from blackduck import Client
from blackduck.Client import HubSession
from blackduck.Authentication import BearerAuth, CookieAuth
import csv
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] {%(module)s:%(lineno)d} %(levelname)s - %(message)s"
)


def check_for_columns(column_names, fieldnames):
    for column in column_names:
        if column not in fieldnames:
            print("Error, input CSV file does not have required column", column)
            sys.exit(-1)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Delete project versions from Hub")

    # must specify authentication details (i.e. token file or username/password) on command line
    parser.add_argument('--base-url', dest='base_url', default=None,
                        help="Hub server BASE_URL e.g. https://example.com")
    parser.add_argument('--token-file', dest='token_file', default=None, help="File containing access token")
    parser.add_argument('--username', dest='username', default=None, help="Hub server USERNAME")
    parser.add_argument('--password', dest='password', default=None, help="Hub server PASSWORD")

    parser.add_argument('--one', dest='one', action='store_true', default=None, help="Exit after processing one row")

    group1 = parser.add_argument_group('required arguments')
    group1.add_argument('--input', dest='csv_file_input', required=True, help="Input CSV file")
    group1.add_argument('--mode', dest='mode', required=True, help="One of list, delete")

    args = parser.parse_args()

    verify = False  # TLS certificate verification
    session = HubSession(args.base_url, timeout=15.0, retries=3, verify=verify)

    # De-tangle the possibilities of specifying credentials
    if args.token_file:
        tf = open(args.token_file, 'r')
        access_token = tf.readline().strip()
        auth = BearerAuth(session, access_token)
    elif args.username and args.password:
        auth = CookieAuth(session, args.username, args.password)
    else:
        raise SystemError("Authentication credentials not specified")

    bd = Client(base_url=args.base_url, session=session, auth=auth, verify=verify)

    if args.mode not in ['list', 'delete']:
        print("Error: must specify --mode to be one of: list or delete")
        sys.exit(-1)

    input_file = open(args.csv_file_input, 'r')
    reader = csv.DictReader(input_file)

    logging.info("csv fieldnames:")
    logging.info(reader.fieldnames)

    check_for_columns([
        'projectId',
        'project',
        'versionId',
        'version',
        'phase',
        'createdAt',
        'sumScanSize',
        'sumScanSizeReadable',
        'latestSummary',
        'bom',
        'events',
        'latestScanEvent',
        'rescanned',
        'latestNotableActivity',
        'notableActivityEvents'], reader.fieldnames)

    if args.mode == 'list':
        print("Listing all rows in CSV to be processed for deletion")
    elif args.mode == 'delete':
        print("Deleting ALL rows in CSV")
        print("WARNING: deletion cannot be undone!")
        confirm = input("Do you want to proceed (type 'yes' to DELETE)? ")
        if confirm != "yes":
            print("Exiting")
            sys.exit(0)
    else:
        print("Error: unknown mode: " + args.mode)
        sys.exit(-1)

    num_deleted = 0
    row_num = 0  # csv module will skip header row automatically
    for row in reader:
        row_num += 1
        print("Row {} ".format(row_num), end='')
        pv_url = args.base_url + "/api/projects/" + row['projectId'] + "/versions/" + row['versionId']
        if args.mode == 'delete':
            print("- deleting project:{}  version:{}".format(row['project'], row['version']))
            response = bd.session.delete(pv_url)
            if response.status_code == 204:
                # success
                num_deleted += 1
            elif response.status_code == 404:
                print("  Error: response status code returned: 404 Not Found")
                print("  Does the project version still exist?")
                print("  " + pv_url)
            else:
                print("  Error: response status code returned: " + str(response.status_code))
                print("  An unexpected error occurred. Check the project version?")
                print("  " + pv_url)
        else:
            print("[DRY-RUN] project:{}  version:{}".format(row['project'], row['version']))
        if args.one:
            print("Exiting after processing one row")
            break

    if args.mode == 'delete' and num_deleted > 0:
        print("Deleted", num_deleted, "project versions.")
        print("Note storage usage is not updated until unmapped scans are removed.")
