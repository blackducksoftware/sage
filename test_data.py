
import json
import logging
import random
import sys
import uuid

from blackduck.HubRestApi import HubInstance

# Create test data for use by sage to detect certain anti-patterns

class FailedToCreateProject(Exception):
	pass

class FailedToCreateVersion(Exception):
	pass

def create_project_versions(hub_instance, project_name, versions=[], project_parameters={}):
	response = hub_instance.create_project(project_name, parameters=project_parameters)

	if response.status_code == 201:
		project = hub_instance.get_project_by_name(project_name)
		for version in range(20):
			response = hub_instance.create_project_version(project, version)
			if response.status_code == 201:
				logging.debug("Created version {}".format(version))
			else:
				raise FailedToCreateVersion("Failed to create version {}, status code: {}".format(version, response.status_code))
		return project
	else:
		raise FailedToCreateProject("Hmm, failed to create the test project {}, status code: {}".format(
			project_name, response.status_code))

def project_with_too_many_versions(hub_instance):
	project_name = "too-many-versions-{}".format(uuid.uuid4())
	project_description = "A project that has too many versions"
	project_parameters = {
		'description': project_description
	}
	versions = [v for v in range(20)]

	return create_project_versions(
		hub_instance, 
		project_name, 
		versions, 
		project_parameters=project_parameters)

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stdout, level=logging.DEBUG)

hub = HubInstance()

bad_project = project_with_too_many_versions(hub)
# print(json.dumps(bad_project))

