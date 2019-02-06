import argparse
import json
import logging
import sys

from blackduck.HubRestApi import HubInstance

parser = argparse.ArgumentParser("Sage, a program that looks at your Black Duck server and offers advice on how to get more value")
parser.add_argument("hub_url")
parser.add_argument("api_token")
parser.add_argument("--max_versions", default=20, help="Set max_versions to catch any projects having more than max_versions")
parser.add_argument("--max_scans", default=10, help="Set max_scans to catch any project-versions with more than max_scans")

args = parser.parse_args()

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stdout, level=logging.DEBUG)

hub = HubInstance(args.hub_url, api_token = args.api_token, insecure=True, write_config_flag=False)

projects = hub.get_projects(limit=99999)

# data = dict()
potential_issues = []

for project in projects['items']:
	project_name = project['name']

	versions = hub.get_project_versions(project, limit=9999)
	if len(versions['items']) > args.max_versions:
		issue = "Project {} has {} versions which is greater than max_versions {}".format(
			project_name, len(versions['items']), args.max_versions)
		advice = "Review scanning best practices. Development/intermediate branches should only have one version - the latest. Only released/published/in-production versions should be retained."
		potential_issues.append({
			'project_name': project_name, 
			'issue': issue, 
			'advice': advice})
		logging.debug("Added project {} to the suspect list since it has {} versions which is greater than max_versions {}".format(
			project_name, len(versions['items']), args.max_versions))
	for version in versions['items']:
		version_name = version['versionName']
		scans = hub.get_version_codelocations(version)

		if len(scans['items']) > args.max_scans:
			issue = "Version {} from project {} has {} scans which is greater than max_scans {}".format(
						version_name, project_name, len(scans['items']), args.max_scans)
			advice = "Review scanning best practices and particularly the setting of scan (aka code location) names. Make sure the scan (aka code location) name does NOT include a build or commit ID"
			potential_issues.append({
				'project_name': project_name,
				'version_name': version_name, 
				'issue': issue, 
				'advice': advice})
			logging.debug("Adding version {} from project {} to the suspect version list since it has {} scans which is greater than max_scans {}".format(
						version_name, project_name, len(scans['items']), args.max_scans))

sage_output_file = "/var/log/sage_says.json"

with open(sage_output_file, "wt") as out_f:
	json.dump({
		"description": "Sage says, no matter where you go, there you are",
		"potential_issues": potential_issues
		}, 
		out_f)

logging.info("Found {} potential issues which have been written (in JSON format) to {}".format(
	len(potential_issues), sage_output_file))

