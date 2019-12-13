
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

import logging
import os

logger = logging.getLogger('django')

def supported_job_type(value):
    supported_job_types = [a[0] for a in Job.JOB_TYPES]

    if value not in supported_job_types:
        raise ValidationError("{} must be one of {}".format(
            value, supported_job_types))

def supported_trigger_type(value):
    supported_trigger_types = [t[0] for t in Job.TRIGGER_TYPES]

    if value not in supported_trigger_types:
        raise ValidationError("{} must be one of {}".format(
            value, supported_trigger_types))

class HubInstance(models.Model):
    url = models.URLField(unique=True)
    api_token = models.CharField(max_length=200)
    insecure = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "url: {}".format(self.url)

# Create your models here.
class JobRun(models.Model):
    result = models.TextField(max_length=2048, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    # TODO: Relate this to HubInstance
    # TODO: Relate this to a Job
    
    def __str__(self):
        return "{}: {}".format(self.created_at, self.result)

class JobQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):
        from sage.job_management import delete_job
        for obj in self:
            delete_job(obj)
        super().delete(*args, **kwargs)

class Job(models.Model):
    JOB_TYPES = [
        ('DEP', 'Delete Empty Projects'),
        ('DEV', 'Delete Empty Versions'),
        ('DUS', 'Delete Unmapped Scans'),
        ('PRUNEV', 'Prune versions from projects'),
        ('Sage', 'Sage Analysis'),
    ]
    TRIGGER_TYPES = [
        ("date", "date"),
        ("interval", "interval"),
        ("cron", "cron"),
    ]
    objects = JobQuerySet.as_manager()

    job_name = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Must be unique") # will be used as job id in apscheduler
    job_type = models.CharField(
        max_length=30, 
        choices=JOB_TYPES, 
        validators=[supported_job_type],
        help_text="Must be one of {}".format(", ".join([j[1] for j in JOB_TYPES])))
    job_args = models.CharField(
        max_length=200,
        blank=True,
        help_text="Space separated key-value pairs that provide job-specific arguments")
    description = models.TextField(max_length=200, blank=True)
    running = models.BooleanField(default=True)
    test_mode = models.BooleanField(default=True, help_text='If enabled, the job will only do a test run. Enabled by default beacuse many of the jobs delete data. Disable this to allow the job to perform the action.')
    trigger_type = models.CharField(
        max_length=20, 
        choices=TRIGGER_TYPES,
        validators=[supported_trigger_type], 
        help_text="Must be one of {}".format(", ".join([t[1] for t in TRIGGER_TYPES])))
    trigger_args = models.CharField(
        max_length=200, 
        help_text="Space separated key-value pairs, e.g. 'second=0 minute=0 hour=0'. See https://apscheduler.readthedocs.io/en/latest/py-modindex.html for details.")
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    # TODO: Allow jobs to be associated with one or more instances, default to all

    def __str__(self):
        return "job_name: {}, job_type: {}, running: {}".format(
            self.job_name, self.job_type, self.running)

    def save(self, *args, **kwargs):
        from sage.job_management import add_or_update_job

        add_or_update_job(self)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from sage.job_management import delete_job
        delete_job(self)
        super().delete(*args, **kwargs)


# Pointers to Sage analysis results stored in the file system
# Entries in this table are created when an analysis is performed
# tyipcally once per day, week, month, etc
# The analysis output is relatively large (e.g. 1M+) and in JSON
# format so keeping the data in the file system as opposed to BLOB
# or JSONField (only suppoted by PostgreSQL)
class SageQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):
        for obj in self:
            try:
                os.remove(obj.filepath)
                logger.info("removed {}".format(obj.filepath))
            except:
                logger.error("Exception occurred when trying to delete {}".format(obj.filepath))
        super().delete(*args, **kwargs)

class Sage(models.Model):
    objects = SageQuerySet.as_manager()

    # TODO: Relate this to HubInstance

    filepath = models.CharField(max_length=1028, unique=True, help_text="The path to the JSON-formatted sage results")
    created_at = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        try:
            os.remove(self.filepath)
            logger.info("removed {}".format(self.filepath))
        except:
            logger.error("Exception occurred when trying to delete {}".format(obj.filepath))
        super().delete(*args, **kwargs)
