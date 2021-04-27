import argparse
from blackduck import Client
from blackduck.Client import HubSession
from blackduck.Authentication import BearerAuth, CookieAuth
from datetime import datetime, timedelta
from dateutil import parser as dt_parser
import json
import logging
import os
from pathlib import Path
import sys

# TODO: Find scans (code locations) whose scan frequency is higher than we recommend
# TODO: Find signature scans taking a long time to complete (e.g. > 30m ) and suggest they be optimized, e.g. by splitting things up
# TODO: Find signature scans that are particular large and should possibly be split up
# TODO: Find projects that don't have any Released versions
# TODO: Find Released versions that don't have any reports
# TODO: Analyze versions and their reports to see if customer is using them
# TODO: Analyze global reports to see if customer is using them


class BlackDuckSage(object):
    VERSION = "2.3"
    COMMON_ATTRIBUTES = [
        'baseDirectory',
        'createdAt',
        'createdBy',
        'createdByUserName',
        'directoryCount',
        'distribution',
        'fileCount',
        'hostName',
        'mappedProjectVersion',
        'matchCount',
        'name',
        'num_bom_scans',
        'num_scans',
        'num_versions',
        'phase',
        'scans',
        'scanSize',
        'scanType',
        'scan_summaries',
        'serverVersion',
        'settingUpdatedAt',
        'status',
        'statusMessage',
        'updatedAt',
        'updatedBy',
        'versionName',
        'versions',
    ]

    def __init__(self, hub_instance, **kwargs):
        assert isinstance(hub_instance, Client)
        self.hub = hub_instance
        self.file = kwargs.get("file", "/var/log/sage_says.json")
        self._check_file_permissions()
        self.max_versions_per_project = kwargs.get('max_versions_per_project', 20)
        self.max_scans_per_version = kwargs.get('max_scans_per_version', 10)
        self.max_age_for_unmapped_scans = kwargs.get('max_age_unmapped_scans', 365)  # days
        self.min_time_between_versions = kwargs.get("min_time_between_versions", 1)  # hour
        self.min_ratio_of_released_versions = kwargs.get("min_ratio_of_released_versions", 0.1)  # min ratio of RELEASED versions to the total
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
            open(self.file, "w")  # will fail if we don't have write permissions

    @staticmethod
    def _remove_white_space(message):
        return " ".join(message.split())

    @staticmethod
    def _copy_common_attributes(obj, **kwargs):
        common_attribute_key_values = dict()
        for attr in BlackDuckSage.COMMON_ATTRIBUTES:
            if attr in obj:
                common_attribute_key_values[attr] = obj[attr]
        common_attribute_key_values.update({
                "url": obj['_meta']['href']
            })
        for k, v in kwargs.items():
            common_attribute_key_values[k] = v
        return common_attribute_key_values

    def _write_results(self):
        with open(self.file, 'w') as f:
            logging.info("Writing results to {}".format(self.file))
            f.write(json.dumps(self.data))

        logging.info("Wrote results to {}".format(self.file))

    @staticmethod
    def _is_signature_scan(scan_obj):
        return scan_obj['name'].lower().endswith("scan")

    @staticmethod
    def _is_bom_scan(scan_obj):
        return scan_obj['name'].lower().endswith("bom") or scan_obj['name'].lower().endswith("black duck i/o export")

    @staticmethod
    def _number_bom_scans(scans):
        return len(list(filter(lambda s: s['name'].lower().endswith('bom'), scans)))

    @staticmethod
    def get_hub_version_info():
        headers = {'accept': "application/vnd.blackducksoftware.status-4+json"}
        return hub.get_json("/api/current-version", headers=headers)

    def _get_data(self):
        start_time = datetime.now()

        '''Retrieve all the projects, versions, and scans and put them into self.data for
        subsequent analysis.
        '''
        logging.info("Fetching projects...")
        projects = list(hub.get_resource('projects', headers={'accept': "application/vnd.blackducksoftware.project-detail-4+json"}))
        logging.info("Fetched %i projects", len(projects))
        total_versions = 0
        project_count = 0
        for project in projects:
            project_count += 1
            project_name = project['name']
            print("Project ({}/{}): {};  versions:".format(project_count, len(projects), project_name), end='', flush=True)
            versions = list(hub.get_resource('versions', project, headers={'accept': "application/vnd.blackducksoftware.project-detail-5+json"}))
            print(len(versions))
            for version in versions:
                version_name = version['versionName']
                print("  {};  codelocations:".format(version_name), end='', flush=True)
                # Using key 'accept' on its own returns http response status code 406 on 2020.12, 2020.2
                # Using key 'content-type' on its own will actually use the internal proprietary content-type:
                #   application/vnd.blackducksoftware.internal-1+json.
                # So we need both.
                headers = {'accept': "application/json",
                           'content-type': "application/vnd.blackducksoftware.scan-4+json"}
                scans = list(hub.get_resource('codelocations', version, headers=headers))
                print(len(scans))
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

        logging.info("Fetching policies...")
        # note using key 'content-type' does not work with 2020.12
        self.data['policies'] = list(hub.get_resource('policyRules', headers={'accept': "application/vnd.blackducksoftware.policy-5+json"}))
        logging.info("Fetched %i policies", len(self.data['policies']))

        logging.info("Fetching codelocations...")
        scans = list(hub.get_resource('codeLocations', headers={'accept': "application/vnd.blackducksoftware.scan-4+json"}))
        logging.info("Fetched %i codelocations", len(scans))
        codelocation_count = 0
        for scan in scans:
            codelocation_count += 1
            print("Codelocation ({}/{}): {};  scan-summaries:".format(codelocation_count, len(scans), scan['name']), end='', flush=True)
            scan_summaries = list(hub.get_resource('scans', scan, headers={'accept': "application/vnd.blackducksoftware.scan-4+json"}))
            print(len(scan_summaries))
            scan_summaries = [self._copy_common_attributes(ss) for ss in scan_summaries]
            scan['scan_summaries'] = scan_summaries
        scans = [self._copy_common_attributes(s) for s in scans]
        self.data['scans'] = scans

        self.data['total_projects'] = len(projects)
        self.data['total_versions'] = total_versions
        self.data['total_scans'] = len(self.data['scans'])

        logging.info("Elapsed time to get data: %s", datetime.now() - start_time)

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
                for finding/deleting/removing versions and their scans.""".format(
                    project['name'], project['num_versions'], self.max_versions_per_project)
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
                list(filter(lambda v1: v1['num_scans'] > self.max_scans_per_version, p['versions'])))
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
                v['too_many_scans_message'] += """There are {} BOM scans in this version.
                    You should consider using {} to aggregate them into one scan which
                    will reduce the processing load on the server and usually reduce the
                    time it takes to complete the scan.""".format(v['num_bom_scans'], "--detect.bom.aggregate.name")
            v['too_many_scans_message'] = self._remove_white_space(v['too_many_scans_message'])

    def _find_versions_with_zero_scans(self):
        versions_with_no_scans = []
        for p in self.data['projects']:
            versions_with_no_scans.extend(
                list(filter(lambda v1: v1['num_scans'] == 0, p['versions'])))
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
            lambda s: s.get('mappedProjectVersion') is None, self.data['scans']))
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
                scans_with_created_at = list(filter(lambda s: 'createdAt' in s, scan['scan_summaries']))
                scan_create_dts = sorted([dt_parser.parse(s['createdAt']) for s in scans_with_created_at])
                if len(scan_create_dts) < 2:
                    continue
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

    # Calculate the total scan size for all scans in each version and all versions in a project.
    # Add 'scanSize' data to each project and version object with the results.
    def _calc_scan_sizes(self):
        for p in self.data['projects']:
            project_scan_size = 0
            for v in p['versions']:
                version_scan_size = 0
                for scan in v['scans']:
                    version_scan_size += scan['scanSize']
                v['scanSize'] = version_scan_size
                project_scan_size += version_scan_size
            p['scanSize'] = project_scan_size

    def _analyze_jobs(self):
        logging.info("Fetching job statistics...")
        # This endpoint is not in the REST API docs with 2021.2 but it still works
        url = "/api/job-statistics"
        job_statistics = list(hub.get_items(url, headers={'accept': "application/vnd.blackducksoftware.status-4+json"}))
        logging.info("Fetched %i job statistics", len(job_statistics))
        self.data['job_statistics'] = job_statistics

    def analyze(self):
        self.data["sage_version"] = BlackDuckSage.VERSION
        self.data["time_of_analysis"] = datetime.now().isoformat()
        self._get_data()

        logging.info("Analyzing data")
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

        self.data["hub_url"] = self.hub.base_url
        self.data["hub_version"] = self.get_hub_version_info()

        if self.analyze_jobs_flag:
            self._analyze_jobs()
        self._write_results()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Sage, a program that looks at your Black Duck server and offers advice on how to get more value")

    parser.add_argument('hub_url', help="Hub server URL e.g. https://example.com")
    parser.add_argument('api_token', nargs='?', default=None, help="API access token")

    parser.add_argument('--api_token_file', dest='token_file', default=None, help="File containing access token")
    parser.add_argument('--username', dest='username', default=None, help="Hub server USERNAME")
    parser.add_argument('--password', dest='password', default=None, help="Hub server PASSWORD")

    parser.add_argument('--timeout', dest='timeout', default=15.0, help="Connection timeout in seconds")
    parser.add_argument('--retries', dest='retries', default=3, help="Maximum number of retries for a single request")

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

    default_max_versions_per_project = 20
    parser.add_argument(
        "-vp",
        "--max_versions_per_project",
        default=default_max_versions_per_project,
        type=int,
        help="Set max_versions_per_project to catch any projects having more than max_versions_per_project (default: {})".format(
            default_max_versions_per_project))

    default_max_scans_per_version = 10
    parser.add_argument(
        "-sv",
        "--max_scans_per_version",
        default=default_max_scans_per_version,
        type=int,
        help="Set max_scans to catch any project-versions with more than max_scans (default: {})".format(
            default_max_scans_per_version))

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="[%(asctime)s] {%(module)s:%(lineno)d} %(levelname)s: %(message)s"
    )

    base_url = args.hub_url
    verify = False  # TLS certificate verification
    session = HubSession(base_url, timeout=args.timeout, retries=args.retries, verify=verify)

    # De-tangle the possibilities of specifying credentials
    if args.api_token:
        access_token = args.api_token
        auth = BearerAuth(session, access_token)
    elif args.token_file:
        tf = open(args.token_file, 'r')
        access_token = tf.readline().strip()
        auth = BearerAuth(session, access_token)
    elif args.username and args.password:
        auth = CookieAuth(session, args.username, args.password)
    else:
        raise SystemError("Authentication credentials not specified")

    hub = Client(base_url=base_url, session=session, auth=auth)

    hub_25835_affected_versions = ['2020.8', '2020.10']
    hub_version_info = BlackDuckSage.get_hub_version_info()
    for h in hub_25835_affected_versions:
        if hub_version_info['version'].startswith(h):
            logging.warning("Scan summaries may be incomplete showing only 1 entry per codelocation (ref. HUB-25835)")
            logging.warning("Affected Hub versions: %s", hub_25835_affected_versions)

    sage = BlackDuckSage(
        hub,
        mode=args.mode,
        file=args.file,
        max_versions_per_project=args.max_versions_per_project,
        max_scans_per_version=args.max_scans_per_version,
        analyze_jobs=args.jobs)
    sage.analyze()
