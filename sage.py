import argparse
from datetime import timedelta
from dateutil import parser as dt_parser
from difflib import SequenceMatcher
import json
import logging
import sys
import time

from blackduck.HubRestApi import HubInstance

# TODO: Incorporate points/scoring to the various analysis results so we can start to provide an overall score
# TODO: Make it possible to change the port where the REST API is listening

class BlackDuckSage(object):
	def __init__(self, hub_instance, **kwargs):
		assert isinstance(hub_instance, HubInstance)
		self.hub = hub_instance
		self.file = kwargs.get("file", "/var/log/sage_says.json")
		self.max_versions_per_project = kwargs.get('max_versions_per_project', 20)
		self.max_scans_per_version = kwargs.get('max_scans_per_version', 10)
		self.max_age_for_unmapped_scans = kwargs.get('max_age_unmapped_scans', 365) # days
		self.min_time_between_versions = kwargs.get("min_time_between_versions", 1) # hour
		self.min_ratio_of_released_versions = kwargs.get("min_ratio_of_released_versions", 0.1) # min ratio of RELEASED versions to the total
		self.max_recommended_projects = int(kwargs.get("max_recommended_projects", 1000))
		self.max_time_to_retrieve_projects = int(kwargs.get("max_time_to_retrieve_projects", 60))
		self.other_issues = []
		self.suspect_projects = []
		self.suspect_versions = []
		self.unmapped_scans = []


	def analyze_version(self, project_name, version):
		version_name = version['versionName']
		logging.debug("Analyzing version {} for project {}".format(version_name, project_name))
		scans = self.hub.get_version_codelocations(version)
		num_scans = len(scans['items'])

		if num_scans == 0:
			message = "Project {}, version {} has 0 scans. Should it be removed?".format(
				project_name, version_name)
			self.suspect_versions.append(message)
		elif num_scans > self.max_scans_per_version:
			message = """Project {}, version {} has {} scans which is greater than 
				the maximum recommended versions of {}. Review the scans to make sure there are not
				redundant scans all mapped to this project version. Look for scans with similar names
				or sizes. If redundant scans are found, use --detect.code.location.name with hub-detect 
				to override scan names and delete redundant scans.""".format(
				project_name, version_name, num_scans, self.max_versions_per_project)
			message = " ".join(message.split()) # remove extraneous whitespace
			signature_scan_info = [
				{
					"scan_name": s['name'],
					"scan_size": s['scanSize'],
					"created_at": s['createdAt'],
					"updated_at": s['updatedAt'],
				} for s in scans['items'] if s['name'].endswith('scan')
			]
			bom_scan_info = [
				{
					"scan_name": s['name'],
					"created_at": s['createdAt'],
					"updated_at": s['updatedAt'],
				} for s in scans['items'] if s['name'].endswith('bom')
			]
			self.suspect_versions.append({
					"message": message,
					"signature_scan_info": signature_scan_info,
					"bom_scan_info": bom_scan_info
				})


	def analyze_project(self, project):
		# Given a project REST API object, analyze its versions and their scans and return
		# any issues found along with advice on how to resolve those issues
		project_name = project['name']
		logging.debug("Analyzing project {}".format(project_name))

		versions = self.hub.get_project_versions(project, limit=9999)
		num_versions = len(versions['items'])

		if num_versions == 0:
			message = "Project {} has 0 versions. Should it be removed?".format(project_name)
			self.suspect_projects.append(message)
		elif num_versions > self.max_versions_per_project:
			message = "Project {} has {} versions which is greater than the recommend maximum of {}".format(
				project_name, num_versions, self.max_versions_per_project)

		for version in versions['items']:
			self.analyze_version(project_name, version)

	def analyze(self):
		start = time.time()
		projects = self.hub.get_projects(limit=99999)
		num_projects = len(projects['items'])
		elapsed = time.time() - start

		logging.debug(
			"Took {} seconds to retrieve the {} projects found on this instance of Black Duck".format(
				elapsed, len(projects['items']))
			)

		if elapsed > self.max_time_to_retrieve_projects:
			message = """It took {} seconds to retrieve all the project info which is greater 
				than the recommended max of {} seconds""".format(elapsed, self.max_time_to_retrieve_projects)
			message = " ".message.split() # remove newline and extra spaces
			self.other_issues.append(message)

		for project in projects['items']:
			self.analyze_project(project)

		analysis_results = {
			"other_issues": self.other_issues,
			"unmapped_scans": self.unmapped_scans,
			"suspect_projects": self.suspect_projects,
			"suspect_versions": self.suspect_versions
		}
		with open(self.file, 'w') as f:
			logging.debug("Writing results to {}".format(self.file))
			f.write(json.dumps(analysis_results))

		logging.info("Wrote results to {}".format(self.file))

	def unmapped_scans(self):
		unmapped_scans = self.hub.get_codelocations(limit=999999, unmapped=True)
		return unmapped_scans

if __name__ == "__main__":
	from pprint import pprint

	parser = argparse.ArgumentParser("Sage, a program that looks at your Black Duck server and offers advice on how to get more value")
	parser.add_argument("hub_url")
	parser.add_argument("api_token")

	parser.add_argument('-f', "--file", default="/var/log/sage_says.json", help="Change the name sage writes results into (default: sage_says.json")

	default_max_versions_per_project=20
	parser.add_argument(
		"-vp", 
		"--max_versions_per_project", 
		default=default_max_versions_per_project, 
		help="Set max_versions_per_project to catch any projects having more than max_versions_per_project (default: {})".format(
			default_max_versions_per_project))

	default_max_scans_per_version=10
	parser.add_argument(
		"-sv", 
		"--max_scans_per_version", 
		default=default_max_scans_per_version, 
		help="Set max_scans to catch any project-versions with more than max_scans (default: {})".format(
			default_max_scans_per_version))

	args = parser.parse_args()

	logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stdout, level=logging.DEBUG)
	logging.getLogger("requests").setLevel(logging.WARNING)
	logging.getLogger("urllib3").setLevel(logging.WARNING)
	hub = HubInstance(args.hub_url, api_token = args.api_token, insecure=True, write_config_flag=False)

	# TODO: Build and pass in the kwargs

	sage = BlackDuckSage(hub)
	sage.analyze()











