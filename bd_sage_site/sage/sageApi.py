from datetime import datetime, timedelta, timezone
from dateutil import parser
import logging
import os
# ref: https://github.com/wroberts/pytimeparse, and https://stackoverflow.com/questions/4628122/how-to-construct-a-timedelta-object-from-a-simple-string
from pytimeparse.timeparse import timeparse


from bd_sage_app.models import JobRun, HubInstance, Sage
from blackduck.HubRestApi import HubInstance as Hub
from sage.sage import BlackDuckSage

logger = logging.getLogger('django')


TEST_MODE_MESSAGE_PREFIX = "In TEST MODE so no action taken. Here's what we would have done: " 

# Translate from what user-specified phase to what the REST API recognizes
phase_map = {
    "in-development": "DEVELOPMENT",
    "in-planning": "PLANNING",
    "pre-release": "PRERELEASE",
    "released": "RELEASED",
    "deprecated": "DEPRECATED",
    "archived": "ARCHIVED"
}

def _get_older_than_timedelta(older_than_str):
    older_than = timeparse(older_than_str) # convert to seconds from string
    return timedelta(seconds=older_than)

def _get_older_than(**kwargs):
    '''
    older_than can be '3d' (for 3 days), '3m' (for 3 mins), '3w' (for 3 weeks), or 
    '3w3d3m' (3 weeks + 3 days + 3 minutes) and more
    default to 180 days old

    ref: https://github.com/wroberts/pytimeparse, and https://stackoverflow.com/questions/4628122/how-to-construct-a-timedelta-object-from-a-simple-string

    '''
    older_than_str = kwargs['older_than'] if 'older_than' in kwargs else '180d'
    if older_than_str:
        older_than = _get_older_than_timedelta(older_than_str)
    else:
        older_than = timedelta(days=180)
    return older_than

def _save_run_results(job_name, message):
    new_run = JobRun()
    new_run.result = "Job '{}': {}".format(job_name, message)
    new_run.save()
    logger.info(new_run)

def _get_project_version_phases(**kwargs):
    '''
    By default, we will prune 'in-development' project-versions
    If user supplies a command separated list we will use that instead
    '''
    phases_str = kwargs['phases'] if 'phases' in kwargs else 'in-development'
    if phases_str:
        phases = phases_str.split(",")
    else:
        phases = ['in-development']
    # TODO: Think about handling KeyError
    phases = [phase_map[p] for p in phases]
    return phases

def _get_project_list(**kwargs):
    # provide a list of project names that the pruning will be restricted to
    project_list_str = kwargs['project_list'] if 'project_list' in kwargs else None
    if project_list_str:
        project_list = project_list_str.split(",")
    else:
        project_list = []
    return project_list

def _get_keep_only(**kwargs):
    '''
    default keep up 20 versions
    '''
    return int(kwargs['keep_only']) if 'keep_only' in kwargs else 20

def _get_job_info(**kwargs):
    job = kwargs['job'] if kwargs.get('job') else None
    if job:
        job_name = job.job_name
    else:
        job_name = "Unknown"

    if job:
        test_mode = job.test_mode
    else:
        test_mode = True # err on the side of caution and don't actually delete anything if the job info isn't avail
    return job, job_name, test_mode

def prune_versions(**kwargs):
    '''Prune versions from projects (on all Hub instances) using filters/criteria specified
    in the job arguments. Job arguments include:
        * older_than which defines the age beyond which versions will be deleted
        * phases which defines the version phases that will be deleted, assuming the version
            meets the other criteria
        * project_list which defines a comma separated list of project names to prune
            versions from, default is 'all' projects
        * keep_only which defines how many (of the most recent) versions to keep

    Defaults: older_than=180d phases=in-development keep_only=20
    '''
    job, job_name, test_mode = _get_job_info(**kwargs)

    older_than = _get_older_than(**kwargs)

    # Get the phases we will prune
    phases = _get_project_version_phases(**kwargs)

    # provide a list of project names that the pruning will be restricted to
    project_list = self._get_project_list(**kwargs)

    # keep only X most-recent versions
    keep_only = _get_keep_only(**kwargs)

    all_pruned_versions = []
    for hub_instance in HubInstance.objects.all():
        hub = Hub(
            hub_instance.url, 
            api_token=hub_instance.api_token, 
            insecure=hub_instance.insecure)
        projects = hub.get_projects(limit=10000).get('items', [])
        if project_list:
            # prune the projects to just those in the list
            projects = list(filter(lambda p: p['name'] in project_list, projects))
        for project in projects:
            versions = hub.get_project_versions(project, limit=9999).get('items', [])
            versions = sorted(versions, key = lambda v: v['createdAt'])
            # prune versions in the phases specified
            versions_to_prune = list(filter(lambda v: v["phase"] in phases, versions))
            # prune versions older than a given age
            versions_to_prune = list(filter(
                lambda v: (datetime.now(timezone.utc) - parser.parse(v['createdAt'])) > older_than, versions_to_prune))
            # keep at most X (of the most recent) versions within the remaining set
            versions_to_prune = versions_to_prune[:-keep_only]
            for v in versions_to_prune:
                if test_mode:
                    logger.debug("In test mode so won't delete version {} from project {} on hub instance {}".format(
                        v['versionName'], project['name'], hub_instance))
                else:
                    try:
                        hub.delete_project_version_by_name(project['name'], v['versionName'])
                    except:
                        logger.error("Failed to delete version {} in project {} on Hub {}".format(
                            v['versionName'], project['name'], hub_instance))
                        continue
                all_pruned_versions.append((str(hub_instance), project['name'], v['name']))

    if HubInstance.objects.all():
        message = "Pruned {} versions. List: {}".format(len(all_pruned_versions), all_pruned_versions)
    else:
        message = "There were no hub instances so we didn't prune any versions"
    if test_mode:
        message = TEST_MODE_MESSAGE_PREFIX + message
    _save_run_results(job_name, message)

def delete_empty_versions(**kwargs):
    job, job_name, test_mode = _get_job_info(**kwargs)

    project_list = _get_project_list(**kwargs)

    all_deleted_versions = []
    for hub_instance in HubInstance.objects.all():
        hub = Hub(
            hub_instance.url, 
            api_token=hub_instance.api_token, 
            insecure=hub_instance.insecure)
        projects = hub.get_projects(limit=10000).get('items', [])
        # restrict to projects specified by user if needed
        if project_list:
            projects = list(filter(lambda p: p['name'] in project_list, projects))
        for project in projects:
            if test_mode:
                logger.debug("In test mode so we won't delete empty versions in project {} on hub instance {}".format(
                    project['name'], hub_instance))
            else:
                try:
                    deleted_versions = hub.delete_empty_versions(project)
                except:
                    logger.exception("Failed to delete empty versions for project {} on {}".format(
                        project['name'], hub_instance))
                    continue
            all_deleted_versions.extend([(str(hub_instance), project['name'], dv) for dv in deleted_versions])

    if HubInstance.objects.all():
        message = "Deleted {} empty versions. List: {}".format(
            job_name, len(all_deleted_versions), all_deleted_versions)
    else:
        message = "There were no hub instances so we didn't delete any empty versions from projects"

    if test_mode:
        message = TEST_MODE_MESSAGE_PREFIX + message
    _save_run_results(job_name, message)

def delete_empty_projects(**kwargs):
    job, job_name, test_mode = _get_job_info(**kwargs)
    all_deleted_projects = []
    for hub_instance in HubInstance.objects.all():
        hub = Hub(
            hub_instance.url, 
            api_token=hub_instance.api_token, 
            insecure=hub_instance.insecure)
        if test_mode:
            logger.debug("In test mode so we won't execute 'delete_empty_projects' on hub instance {}".format(
                hub_instance))
        else:
            try:
                deleted_projects = hub.delete_empty_projects()
            except:
                logger.exception("Failed to delete empty projects on {}".format(hub_instance))
                continue
        all_deleted_projects.extend([(str(hub_instance), dp) for dp in deleted_projects])

    if HubInstance.objects.all():
        message = "Deleted {} empty projects. List: {}".format(len(all_deleted_projects), all_deleted_projects)
    else:
        message = "There were no hub instances so we didn't delete any empty projects"

    if test_mode:
        message = TEST_MODE_MESSAGE_PREFIX + message
    _save_run_results(job_name, message)

def delete_unmapped_scans(**kwargs):
    job, job_name, test_mode = _get_job_info(**kwargs)
    # older_than can be '3d' (for 3 days), '3m' (for 3 mins), '3w' (for 3 weeks), or 
    # '3w3d3m' (3 weeks + 3 days + 3 minutes) and more
    older_than_str = kwargs['older_than'] if 'older_than' in kwargs else '0s'
    older_than = _get_older_than_timedelta(older_than_str)
    deleted_unmapped_code_locations = []
    unmapped_code_locations = []
    for hub_instance in HubInstance.objects.all():
        hub = Hub(
            hub_instance.url, 
            api_token=hub_instance.api_token, 
            insecure=hub_instance.insecure)
        unmapped_code_locations = hub.get_codelocations(unmapped=True).get('items', [])
        logger.info("Found {} unmapped code locations at {}".format(
            len(unmapped_code_locations), hub.get_urlbase()))

        for unmapped_code_location in unmapped_code_locations:
            age = datetime.now(timezone.utc) - parser.parse(unmapped_code_location['updatedAt'])
            if age > older_than:
                if test_mode:
                    logger.debug("In test mode so not deleting unmapped code location {} on hub instance {}".format(
                        unmapped_code_location['_meta']['href'], hub_instance))
                else:
                    try:
                        hub.execute_delete(unmapped_code_location['_meta']['href'])
                    except:
                        logger.error("Failed to delete unmapped code location {}".format(unmapped_code_location))
                        continue
                deleted_unmapped_code_locations.append((str(hub_instance), unmapped_code_location['name']))
            else:
                logger.info(
                    "Not deleting unmapped code location({}) on {} because age {} is not greater than 'older_than' threshold of {}".format(
                    unmapped_code_location['name'], hub.get_urlbase(), age, older_than))

    if HubInstance.objects.all():
        message = "Deleted {} unmapped scans. List: {}".format(
            len(deleted_unmapped_code_locations), unmapped_code_locations)
    else:
        message = "There were no hub instances so we didn't delete any unmapped scans"

    if test_mode:
        message = TEST_MODE_MESSAGE_PREFIX + message
    _save_run_results(job_name, message)

def run_sage(**kwargs):
    job, job_name, test_mode = _get_job_info(**kwargs)
    messages = ["There were no hub instances so we didn't run Sage"]
    for hub_instance in HubInstance.objects.all():
        hub = Hub(
            hub_instance.url, 
            api_token=hub_instance.api_token, 
            insecure=hub_instance.insecure)
        now = datetime.now()
        sage_file_name = "sage_says_{}".format(now.isoformat().replace(":", "-"))
        sage_obj = BlackDuckSage(
            hub,
            file=sage_file_name,
            analyze_jobs=True)
        if test_mode:
            logger.debug("In test mode so not running sage on hub instance {}".format(hub_instance))
        else:
            logger.info("Running sage analysis on hub {}".format(hub.get_urlbase()))
            sage_obj.analyze()

            new_sage = Sage()
            new_sage.filepath = "{}/{}".format(os.getcwd(), sage_file_name)
            new_sage.save()

        message = "Ran sage at {} on hub {}, results were written to {}".format(
            now.isoformat(), hub_instance, sage_file_name)
        if test_mode:
            message = TEST_MODE_MESSAGE_PREFIX + message
        messages.append(message)
    _save_run_results(job_name, ";".join(messages))

