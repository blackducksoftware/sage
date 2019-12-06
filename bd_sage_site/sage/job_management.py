import logging
import shlex

from apscheduler.jobstores.base import JobLookupError

from sage import sageApi
from sage.scheduler import job_scheduler # a global variable that points to the one, and only one, job scheduler

job_types = {
    'DEP': sageApi.delete_empty_projects,
    'DEV': sageApi.delete_empty_projects,
    'DUS': sageApi.delete_unmapped_scans,
    'PRUNEV': sageApi.prune_versions,
    'Sage': sageApi.run_sage,
}

logger = logging.getLogger('django')

def add_or_update_job(job):
    # translate from Job model/table info to call the scheduler and
    # add or update the job
    trigger_kwargs = dict(token.split('=') for token in shlex.split(job.trigger_args))
    job_kwargs = dict(token.split('=') for token in shlex.split(job.job_args))
    job_kwargs['job'] = job

    if job.trigger_type == 'interval':
        # convert strings to int for kwargs that require int
        for k,v in trigger_kwargs.items():
            if k in ['weeks', 'days', 'hours', 'minutes', 'seconds']:
                trigger_kwargs[k] = int(v)
    logger.info(
        "adding or updating job ({}), using job_kwargs: {}, using trigger_kwargs: {}".format(
        job, job_kwargs, trigger_kwargs))

    if job.running:
        job_scheduler.add_job(
            job_types[job.job_type],
            replace_existing=True,
            id=job.job_name,
            name=job.job_name,
            trigger=job.trigger_type,
            kwargs=job_kwargs,
            **trigger_kwargs
            )
    else:
        # Since it is currently not marked for running, it should be removed from the scheduler
        try:
            job_scheduler.remove_job(job.job_name)
        except JobLookupError:
            logger.info("Did not find job {} in the scheduler, but that's ok cause we were trying to remove it anyhow".format(
                job.job_name))
    job_scheduler.print_jobs()

def delete_job(job):
    logger.info("deleting job {}".format(job.job_name))
    try:
        job_scheduler.remove_job(job.job_name)
    except JobLookupError:
        logger.info("While deleting job {}, we did not find it in the scheduler, but that's ok cause we were trying to remove it anyhow".format(
            job.job_name))
    job_scheduler.print_jobs()


