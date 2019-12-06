import argparse
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import signal
import sys
import time

from blackduck.HubRestApi import HubInstance

# TODO: Incorporate points/scoring to the various analysis results so we can start to provide an overall score
# TODO: Make it possible to change the port where the REST API is listening

class BlackDuckSage(object):
    VERSION="2.0"
    COMMON_ATTRIBUTES = [
        'name', 
        'versionName', 
        'createdAt', 
        'createdBy', 
        'distribution', 
        'mappedProjectVersion',
        'num_scans',
        'num_versions',
        'phase', 
        'scans',
        'scanSize', 
        'settingUpdatedAt',
        'versions',
        'updatedAt', 
        'updatedBy']

    def __init__(self, hub_instance, **kwargs):
        assert isinstance(hub_instance, HubInstance)
        self.hub = hub_instance
        self.file = kwargs.get("file", "/var/log/sage_says.json")
        self._check_file_permissions()
        self.max_versions_per_project = kwargs.get('max_versions_per_project', 20)
        self.max_scans_per_version = kwargs.get('max_scans_per_version', 10)
        self.max_age_for_unmapped_scans = kwargs.get('max_age_unmapped_scans', 365) # days
        self.min_time_between_versions = kwargs.get("min_time_between_versions", 1) # hour
        self.min_ratio_of_released_versions = kwargs.get("min_ratio_of_released_versions", 0.1) # min ratio of RELEASED versions to the total
        self.max_recommended_projects = int(kwargs.get("max_recommended_projects", 1000))
        self.max_time_to_retrieve_projects = int(kwargs.get("max_time_to_retrieve_projects", 60))
        self.analyze_jobs_flag = kwargs.get("analyze_jobs", True)
        
        # signal.signal(signal.SIGINT, lambda signal, frame: self._signal_handler())
        # signal.signal(signal.SIGTERM, lambda signal, frame: self._signal_handler())

    def _check_file_permissions(self):
        f = Path(self.file)
        if f.exists():
            if not os.access(self.file, os.W_OK):
                raise PermissionError("Need write access to file {} in order to save the analysis results".format(self.file))
        else:
            f = open(self.file, "w") # will fail if we don't have write permissions

    # def _signal_handler(self):
    #     logging.debug("Handling interrupt and writing results to {}".format(self.file))
    #     self._write_results()
    #     raise OSError("Interruped")

    def _remove_white_space(self, message):
        return " ".join(message.split())

    def _copy_common_attributes(self, obj, **kwargs):
        common_attribute_key_values = dict()
        for attr in BlackDuckSage.COMMON_ATTRIBUTES:
            if attr in obj:
                common_attribute_key_values[attr] = obj[attr]
        common_attribute_key_values.update({
                "url": obj['_meta']['href']
            })
        for k,v in kwargs.items():
            common_attribute_key_values[k] = v
        return common_attribute_key_values


    def _write_results(self):
        with open(self.file, 'w') as f:
            logging.debug("Writing results to {}".format(self.file))
            f.write(json.dumps(self.data))

        logging.info("Wrote results to {}".format(self.file))

    def _is_sig_scan(self, scan_obj):
        return scan_obj['name'].endswith("scan")

    def _is_bom_scan(self, scan_obj):
        return scan_obj['name'].endswith("bom")
        
    def _get_data(self):
        logging.debug('Retrieving projects')
        projects = self.hub.get_projects(limit=99999).get('items', [])
        total_versions = 0
        for project in projects:
            project_name = project['name']
            logging.debug("Retrieving versions for project {}".format(project_name))
            versions = self.hub.get_project_versions(project, limit=10000).get('items', [])
            for version in versions:
                version_name = version['versionName']
                logging.debug("Retrieving scans for version {}".format(version_name))
                scans = self.hub.get_version_codelocations(version, limit=1000)
                if scans:
                    scans = scans.get('items', [])
                    scans = [self._copy_common_attributes(s, version_name=version_name, project_name=project_name) for s in scans]
                else:
                    scans = []
                version['scans'] = scans
                version['num_scans'] = len(scans)
            versions = [self._copy_common_attributes(v, project_name=project_name) for v in versions]
            project['versions'] = versions
            project['num_versions'] = len(versions)
            total_versions += len(versions)
        projects = [self._copy_common_attributes(p) for p in projects]
        self.data['projects'] = projects

        logging.debug("Retrieving policies")
        self.data['policies'] = self.hub.get_policies(parameters={'limit':1000})

        logging.debug("Retrieving scans")
        self.data['scans'] = self.hub.get_codelocations(limit=99999).get('items', [])
        self.data['total_projects'] = len(projects)
        self.data['total_versions'] = total_versions
        self.data['total_scans'] = len(self.data['scans'])

    def analyze(self):
        self.data = {}
        self.data["time_of_analysis"] = datetime.now().isoformat()
        self._get_data()

        logging.debug("Analyzing data")
        self.data['projects_with_too_many_versions'] = list(filter(
            lambda p: p['num_versions'] > self.max_versions_per_project, self.data['projects']))
        versions_with_too_many_scans = []
        for p in self.data['projects']:
            versions_with_too_many_scans.extend(
                list(filter(lambda v: v['num_scans'] > self.max_scans_per_version, 
                    p['versions'])))
        self.data['versions_with_too_many_scans'] = versions_with_too_many_scans

        versions_with_no_scans = []
        for p in self.data['projects']:
            versions_with_no_scans.extend(
                list(filter(lambda v: v['num_scans'] == 0, 
                    p['versions'])))
        self.data['unmapped_scans'] = list(filter(
            lambda s: s.get('mappedProjectVersion') == None, self.data['scans']))
        self.data['total_unmapped_scans'] = len(self.data['unmapped_scans'])
        self.data['total_scans'] = len(self.data['scans'])
        self.data['total_scan_size'] = sum([s.get('scanSize', 0) for s in self.data['scans']])
        self.data['number_sig_scans'] = len(list(filter(lambda s: self._is_sig_scan(s), self.data['scans'])))
        self.data['number_bom_scans'] = len(list(filter(lambda s: self._is_bom_scan(s), self.data['scans'])))

        self.data["hub_url"] = self.hub.get_urlbase()
        self.data["hub_version"] = self.hub.version_info

        self._write_results()


if __name__ == "__main__":
    from pprint import pprint

    parser = argparse.ArgumentParser("Sage, a program that looks at your Black Duck server and offers advice on how to get more value")
    parser.add_argument("hub_url")
    parser.add_argument("api_token")

    parser.add_argument(
        '-f', 
        "--file", 
        default="/var/log/sage_says.json", 
        help="Change the name sage writes results into (default: sage_says.json")

    parser.add_argument(
        '-j',
        '--jobs',
        action='store_true',
        help="Include this flag if you want to try to collect and analyze jobs info")

    parser.add_argument(
        "-m", 
        "--mode", 
        choices=["new", "resume"],
        default="new",
        help="""Set to 'resume' to resume analysis or to 'new' to start new (default). 
Resuming requires a previously saved file is present to read the current state of analysis. 'New' will overwrite the analysis file.""")

    default_max_versions_per_project=20
    parser.add_argument(
        "-vp", 
        "--max_versions_per_project", 
        default=default_max_versions_per_project, 
        type=int,
        help="Set max_versions_per_project to catch any projects having more than max_versions_per_project (default: {})".format(
            default_max_versions_per_project))

    default_max_scans_per_version=10
    parser.add_argument(
        "-sv", 
        "--max_scans_per_version", 
        default=default_max_scans_per_version, 
        type=int,
        help="Set max_scans to catch any project-versions with more than max_scans (default: {})".format(
            default_max_scans_per_version))

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', stream=sys.stderr, level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    hub = HubInstance(args.hub_url, api_token = args.api_token, insecure=True, write_config_flag=False)

    sage = BlackDuckSage(
        hub, 
        mode=args.mode,
        file=args.file,
        max_versions_per_project=args.max_versions_per_project,
        max_scans_per_version=args.max_scans_per_version,
        analyze_jobs = args.jobs)
    sage.analyze()











