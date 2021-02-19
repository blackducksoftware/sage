import argparse
from datetime import datetime, timedelta
from dateutil import parser as dt_parser
import json
import logging
import os
from pathlib import Path
import signal
import sys
import time

from blackduck.HubRestApi import HubInstance

# TODO: Find scans (code locations) whose scan frequency is higher than we recommend
# TODO: Find signature scans taking a long time to complete (e.g. > 30m ) and suggest they be optimized, e.g. by splitting things up
# TODO: Find signature scans that are particular large and should possibly be split up
# TODO: Find Released versions that don't have any reports
# TODO: Find projects that don't have an owner
# TODO: Analyze versions and their reports to see if customer is using them
# TODO: Analyze global reports to see if customer is using them


class BlackDuckSage(object):
    VERSION="2.1"
    COMMON_ATTRIBUTES = [
        'name', 
        'versionName', 
        'createdAt', 
        'createdBy', 
        'distribution', 
        'mappedProjectVersion',
        'num_bom_scans',
        'num_scans',
        'num_versions',
        'phase', 
        'scans',
        'scanSize', 
        'scan_summaries',
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
        self.data = {}

    def _check_file_permissions(self):
        f = Path(self.file)
        if f.exists():
            if not os.access(self.file, os.W_OK):
                raise PermissionError("Need write access to file {} in order to save the analysis results".format(self.file))
        else:
            f = open(self.file, "w") # will fail if we don't have write permissions

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

    def _is_signature_scan(self, scan_obj):
        return scan_obj['name'].lower().endswith("scan")

    def _is_bom_scan(self, scan_obj):
        return (scan_obj['name'].lower().endswith("bom") or scan_obj['name'].lower().endswith("black duck i/o export"))
        
    def _number_bom_scans(self, scans):
        return len(list(filter(lambda s: s['name'].lower().endswith('bom'), scans)))

    def _get_code_locations(self, limit=100):
        # loop to retreive all the code locations using offset, limit parms
        scans = []

        offset = 0
        while True:
            parameters = {'offset': offset, 'limit': limit}
            logging.debug(f"Retrieving {limit} scans from offset {offset}")
            more_scans = self.hub.get_codelocations(limit=limit, parameters=parameters).get('items', [])
            scans.extend(more_scans)
            if len(more_scans) < limit:
                break
            offset += limit
        logging.debug(f"Retrieved {len(scans)} scans")
        return scans

    def _get_data(self):
        '''Retrieve all the projects, versions, and scans and put them into self.data for
        subsequent analysis.
        '''
        logging.debug("Retrieving scans and scan summaries (aka scan history)")
        # self.data['scans'] = self.hub.get_codelocations(limit=99999).get('items', [])

        self.data['scans'] = self._get_code_locations(limit=1000)
        logging.debug(f"Retrieving scan summaries for {len(self.data['scans'])} scans")
        for scan in self.data['scans']:
            try:
                scan_summaries = self.hub.get_codelocation_scan_summaries(code_location_obj = scan).get('items', [])
            except:
                logging.warning(f"Unable to retrieve scan summaries for scan {scan['name']}")
                scan_summaries = []
            logging.debug(f"Retrieved {len(scan_summaries)} scan summary for scan {scan['name']}")
            scan['scan_summaries'] = scan_summaries

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
                scans = self.hub.get_version_codelocations(version, limit=1000).get('items', [])
                scans = [self._copy_common_attributes(s, version_name=version_name, project_name=project_name) for s in scans]
                version['scans'] = scans
                version['num_bom_scans'] = self._number_bom_scans(scans)
                version['num_scans'] = len(scans)
            versions = [self._copy_common_attributes(v, project_name=project_name) for v in versions]
            project['versions'] = versions
            project['num_versions'] = len(versions)
            total_versions += len(versions)
        projects = [self._copy_common_attributes(p) for p in projects]
        self.data['projects'] = projects

        logging.debug("Retrieving policies")
        self.data['policies'] = self.hub.get_policies(parameters={'limit':1000}).get('items', [])

        self.data['total_projects'] = len(projects)
        self.data['total_versions'] = total_versions
        self.data['total_scans'] = len(self.data['scans'])

    def _find_projects_with_too_many_versions(self):
        self.data['projects_with_too_many_versions'] = list(filter(
            lambda p: p['num_versions'] > self.max_versions_per_project, self.data['projects']))
        for project in self.data['projects_with_too_many_versions']:
            project['too_many_versions_message'] = """Project {} has {} versions which is greater than
                the threshold of {}. You should review these versions and remove extraneous ones,
                and their scans, to reclaim space and reduce clutter. Typically, there should be
                one version per development branch, and one version per release. When new vulnerabilities are published you want
                to be able to quickly identify which projects are affected and take action.
                Keeping a large number of un-released versions in the system will make that difficult.
                And accruing a large number of versions per project can lead to serious performance degradation.
                Look at https://github.com/blackducksoftware/hub-rest-api-python/tree/master/examples for python examples
                for finding/deleting/removing versions and their scans.""".format(project['name'], 
                    project['num_versions'], self.max_versions_per_project)
            project['too_many_versions_message'] = self._remove_white_space(project['too_many_versions_message'])

    def _find_projects_without_an_owner(self):
        self.data['projects_without_an_owner'] = list(filter(
            lambda p: 'projectOwner' not in p, self.data['projects']))
        for project in self.data['projects_without_an_owner']:
            project['no_owner_message'] = """Project {} has no owner assigned. 
                Assigning an owner is a good practice in case there are issues requiring their 
                attention such as issues with their use of Black Duck or the presence of a critical
                vulnerability or serious legal compliance issue.""".format(project['name'])
            project['no_owner_message'] = self._remove_white_space(project['no_owner_message'])

    def _find_versions_with_too_many_scans(self):
        versions_with_too_many_scans = []
        for p in self.data['projects']:
            versions_with_too_many_scans.extend(
                list(filter(lambda v: v['num_scans'] > self.max_scans_per_version, 
                    p['versions'])))
        self.data['versions_with_too_many_scans'] = versions_with_too_many_scans
        for v in self.data['versions_with_too_many_scans']:
            v['too_many_scans_message'] = """Project {}, version {} has {} scans which is greater than 
                    the maximum recommended scans of {}. Review the scans to make sure there are not
                    redundant scans all mapped to this project version. Look for scans with similar names
                    or sizes. If redundant scans are found, you should delete them and update the scanning
                    setup to use --detect.code.location.name with Synopsys detect to override scan names and 
                    delete redundant scans.""".format(
                    v['project_name'], v['versionName'], v['num_scans'], self.max_scans_per_version)
            if v['num_bom_scans'] > self.max_scans_per_version:
                v['message'] += """There are {} BOM scans in this version. 
                    You should consider using {} to aggregate them into one scan which 
                    will reduce the processing load on the server and usually reduce the 
                    time it takes to complete the scan.""".format(v['num_bom_scans'], "--detect.bom.aggregate.name")
            v['too_many_scans_message'] = self._remove_white_space(v['too_many_scans_message'])

    def _find_versions_with_zero_scans(self):
        versions_with_no_scans = []
        for p in self.data['projects']:
            versions_with_no_scans.extend(
                list(filter(lambda v: v['num_scans'] == 0, 
                    p['versions'])))
        self.data['versions_with_zero_scans'] = versions_with_no_scans
        for v in self.data['versions_with_zero_scans']:
            v['zero_scans_message'] = """Project {}, version {} has 0 scans. You should review this version and
            delete it if it is not being used. One exception is if someone created this project-version
            to populate with components manually, i.e. no scans are mapped to it, but the BOM inside this
            version is populated by manually adding components to it.""".format(
                    v['project_name'], v['versionName'])
            v['zero_scans_message'] = self._remove_white_space(v['zero_scans_message'])

    def _find_unmapped_scans(self):
        self.data['unmapped_scans'] = list(filter(
            lambda s: s.get('mappedProjectVersion') == None, self.data['scans']))
        self.data['total_unmapped_scans'] = len(self.data['unmapped_scans'])
        for ums in self.data['unmapped_scans']:
            ums['unmapped_scan_message'] = """This scan, {}, is not mapped to any project-version in the system. It should
                either be mapped to something or deleted to reclaim space and reduce clutter.""".format(ums['name'])
            ums['unmapped_scan_message'] = self._remove_white_space(ums['unmapped_scan_message'])

    def _find_high_frequency_scans(self):
        high_freq_scans = []
        for scan in self.data['scans']:
            if scan.get('scan_summaries') and len(scan['scan_summaries']) > 1:
                # found there can be scan summaries that don't have a createdAt so filter those out
                scans_with_createdAt = list(filter(lambda s: 'createdAt' in s, scan['scan_summaries']))
                scan_create_dts = sorted([dt_parser.parse(s['createdAt']) for s in scans_with_createdAt])
                total_span_less_than_24h = (scan_create_dts[-1] - scan_create_dts[0]) < timedelta(days=1)
                spans = [
                    scan_create_dts[i] - scan_create_dts[i-1] for i in range(1, len(scan_create_dts))
                ]
                any_span_less_than_24h = any([s < timedelta(days=1) for s in spans])
                if any_span_less_than_24h or total_span_less_than_24h:
                    scan['high_freq_scan_message'] = """This scan (aka code location) has two or more scans (out of {}) that
                        were run within 24 hours of each other which may indicate a scan that is being run too
                        often. Consider reducing the frequency to once per day.""".format(len(scan_create_dts))
                    scan['high_freq_scan_message'] = self._remove_white_space(scan['high_freq_scan_message'])
                    high_freq_scans.append(scan)
        self.data['high_frequency_scans'] = high_freq_scans

    # Calculate the total scan size for all scans in each vesion and all versions in a project.
    # Add 'scanSize' data to each project and version object with the results.
    def _calc_scan_sizes(self):
        for p in self.data['projects']:
            project_scan_size = 0
            for v in p['versions']:
                version_scan_size=0
                for scan in v['scans']:
                    version_scan_size += scan['scanSize']
                v['scanSize'] = version_scan_size
                project_scan_size += version_scan_size
            p['scanSize'] = project_scan_size

    def _analyze_jobs(self):
        url = self.hub.get_apibase() + "/job-statistics?limit=999" # using limit 999 to ensure we get all job types
        response = self.hub.execute_get(url)
        job_statistics = response.json().get('items', [])
        self.data['job_statistics'] = job_statistics

    def analyze(self):
        self.data["sage_version"] = BlackDuckSage.VERSION
        self.data["time_of_analysis"] = datetime.now().isoformat()
        self._get_data()

        logging.debug("Analyzing data")
        self._calc_scan_sizes()
        self._find_projects_with_too_many_versions()
        self._find_projects_without_an_owner()
        self._find_versions_with_too_many_scans()
        self._find_versions_with_zero_scans()
        self._find_unmapped_scans()
        self._find_high_frequency_scans()
        self.data['total_scans'] = len(self.data['scans'])
        self.data['total_scan_size'] = sum([s.get('scanSize', 0) for s in self.data['scans']])
        self.data['number_signature_scans'] = len(list(filter(
            lambda s: self._is_signature_scan(s), self.data['scans'])))
        self.data['number_bom_scans'] = len(list(filter(
            lambda s: self._is_bom_scan(s), self.data['scans'])))

        self.data["hub_url"] = self.hub.get_urlbase()
        self.data["hub_version"] = self.hub.version_info

        if self.analyze_jobs_flag:
            self._analyze_jobs()
        self._write_results()


if __name__ == "__main__":
    from pprint import pprint

    parser = argparse.ArgumentParser("Sage, a program that looks at your Black Duck server and offers advice on how to get more value")

    parser.add_argument('hub_url', help="Hub server URL e.g. https://example.com");
    parser.add_argument('api_token', nargs='?', default=None, help="API access token");

    parser.add_argument('--api_token_file', dest='token_file', default=None, help="File containing access token");
    parser.add_argument('--username', dest='username', default=None, help="Hub server USERNAME");
    parser.add_argument('--password', dest='password', default=None, help="Hub server PASSWORD");

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

    create_config = False
    if (create_config): logging.info("writing .restconfig.json upon successful authentication")

    accept_self_signed = True
    if (accept_self_signed): logging.info("accepting self-signed certificates in SSL connection")

    hub = None
    if (args.hub_url and args.username and args.password):
        hub = HubInstance(args.hub_url, args.username, args.password, write_config_flag=create_config, insecure=accept_self_signed)
    elif (args.hub_url and args.api_token):
        token = args.api_token
        hub = HubInstance(args.hub_url, api_token=token, write_config_flag=create_config, insecure=accept_self_signed)
    elif (args.hub_url and args.token_file):
        f = open(args.token_file)
        token = f.readline().strip()
        hub = HubInstance(args.hub_url, api_token=token, write_config_flag=create_config, insecure=accept_self_signed)
    else:
        if not os.path.exists(".restconfig.json"):
            print("Error: authentication details not specified")
            parser.print_help()
            sys.exit(-1)
        logging.info("reading authentication details from .restconfig.json")
        hub = HubInstance()

    sage = BlackDuckSage(
        hub, 
        mode=args.mode,
        file=args.file,
        max_versions_per_project=args.max_versions_per_project,
        max_scans_per_version=args.max_scans_per_version,
        analyze_jobs = args.jobs)
    sage.analyze()











