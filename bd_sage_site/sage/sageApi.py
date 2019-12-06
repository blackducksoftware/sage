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

def _save_run_results(job_name, message):
    new_run = JobRun()
    new_run.result = "Job '{}': {}".format(job_name, message)
    new_run.save()
    print(new_run)

def prune_versions(**kwargs):
    '''Prune versions from projects (on all Hub instances) using filters/criteria specified
    in the job arguments.
    Defaults: older_than=180d in_phases=in-development keep_only=20
    '''
    job_name = kwargs['job'].job_name if kwargs.get('job') else "Unknown"
    # older_than can be '3d' (for 3 days), '3m' (for 3 mins), '3w' (for 3 weeks), or 
    # '3w3d3m' (3 weeks + 3 days + 3 minutes) and more
    # default to 180 days old
    older_than_str = kwargs['older_than'] if 'older_than' in kwargs else '180d'
    older_than = _get_older_than_timedelta(older_than_str)
    # by default, prune "In Development" phase project-versions which is the default used by Detect, Hub
    in_phases_str = kwargs['in_phases'] if 'in_phases' in kwargs else 'in-development'
    in_phases = in_phases_str.split(',')
    # lookup the phase names returned by REST API using phase map
    in_phases = [phase_map[p] for p in in_phases]
    # default keep up to 20 newest versions, enforced AFTER other filters (i.e. older_than, in_phases)
    keep_only = int(kwargs['keep_only']) if 'keep_only' in kwargs else 20

    all_pruned_versions = []
    for hub_instance in HubInstance.objects.all():
        hub = Hub(
            hub_instance.url, 
            api_token=hub_instance.api_token, 
            insecure=hub_instance.insecure)
        for project in hub.get_projects(limit=10000).get('items', []):
            versions = hub.get_project_versions(project, limit=9999).get('items', [])
            versions = sorted(versions, key = lambda v: v['createdAt'])
            # prune versions in the phases specified
            versions_to_prune = list(filter(lambda v: v["phase"] in in_phases, versions))
            # prune versions older than a given age
            versions_to_prune = list(filter(
                lambda v: (datetime.now(timezone.utc) - parser.parse(v['createdAt'])) > older_than, versions_to_prune))
            # keep at most X (of the most recent) versions within the remaining set
            versions_to_prune = versions_to_prune[:-keep_only]
            for v in versions_to_prune:
                try:
                    hub.delete_project_version_by_name(project['name'], v['name'])
                except:
                    logger.error("Failed to delete version {} in project {} on Hub {}".format(
                        v['name'], project['name'], hub_instance))
                    continue
                all_pruned_versions.append((str(hub_instance), project['name'], v['name']))

    _save_run_results(job_name, "Pruned {} versions. List: {}".format(
        len(all_pruned_versions), all_pruned_versions))

def delete_empty_versions(**kwargs):
    job_name = kwargs['job'].job_name if kwargs.get('job') else "Unknown"
    all_deleted_versions = []
    for hub_instance in HubInstance.objects.all():
        hub = Hub(
            hub_instance.url, 
            api_token=hub_instance.api_token, 
            insecure=hub_instance.insecure)
        for project in hub.get_projects(limit=10000):
            try:
                deleted_versions = hub.delete_empty_versions(project)
            except:
                logger.exception("Failed to delete empty versions for project {} on {}".format(
                    project['name'], hub_instance))
                continue
            all_deleted_versions.extend([(str(hub_instance), project['name'], dv) for dv in deleted_versions])

    _save_run_results(job_name, "Deleted {} empty versions. List: {}".format(
        job_name, len(all_deleted_versions), all_deleted_versions))

def delete_empty_projects(**kwargs):
    job_name = kwargs['job'].job_name if kwargs.get('job') else "Unknown"
    all_deleted_projects = []
    for hub_instance in HubInstance.objects.all():
        hub = Hub(
            hub_instance.url, 
            api_token=hub_instance.api_token, 
            insecure=hub_instance.insecure)
        try:
            deleted_projects = hub.delete_empty_projects()
        except:
            logger.exception("Failed to delete empty projects on {}".format(hub_instance))
            continue
        all_deleted_projects.extend([(str(hub_instance), dp) for dp in deleted_projects])
    _save_run_results(job_name, "Deleted {} empty projects. List: {}".format(len(all_deleted_projects), all_deleted_projects))

def delete_unmapped_scans(**kwargs):
    job_name = kwargs['job'].job_name if kwargs.get('job') else "Unknown"
    # older_than can be '3d' (for 3 days), '3m' (for 3 mins), '3w' (for 3 weeks), or 
    # '3w3d3m' (3 weeks + 3 days + 3 minutes) and more
    older_than_str = kwargs['older_than'] if 'older_than' in kwargs else '0s'
    older_than = _get_older_than_timedelta(older_than_str)
    for hub_instance in HubInstance.objects.all():
        hub = Hub(
            hub_instance.url, 
            api_token=hub_instance.api_token, 
            insecure=hub_instance.insecure)
        unmapped_code_locations = hub.get_codelocations(unmapped=True).get('items', [])
        logger.info("Found {} unmapped code locations at {}".format(
            len(unmapped_code_locations), hub.get_urlbase()))
        deleted_unmapped_code_locations = []
        for unmapped_code_location in unmapped_code_locations:
            age = datetime.now(timezone.utc) - parser.parse(unmapped_code_location['updatedAt'])
            if age > older_than:
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
    _save_run_results(job_name, "Deleted {} unmapped scans. List: {}".format(
        len(deleted_unmapped_code_locations), unmapped_code_locations))

def run_sage(**kwargs):
    job_name = kwargs['job'].job_name if kwargs.get('job') else "Unknown"
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
        logger.info("Running sage analysis on hub {}".format(hub.get_urlbase()))
        sage_obj.analyze()

        new_sage = Sage()
        new_sage.filepath = "{}/{}".format(os.getcwd(), sage_file_name)
        new_sage.save()
        _save_run_results(job_name, "Ran sage at {} on hub {}, results were written to {}".format(
            job_name, now.isoformat(), str(hub_instance), sage_file_name))

