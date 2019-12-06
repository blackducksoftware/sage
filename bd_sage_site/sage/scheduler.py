import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from django.conf import settings

job_scheduler = None

logger = logging.getLogger("django")


def start():
    global job_scheduler
    if job_scheduler == None:
        job_stores = {'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')}
        job_scheduler = BackgroundScheduler(jobstores=job_stores)

    job_scheduler.start()
    print("In scheduler")
    job_scheduler.print_jobs()


    