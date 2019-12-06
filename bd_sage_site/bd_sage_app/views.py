from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView

from sage.scheduler import job_scheduler

class MainPage(TemplateView):
    def get(self, request, **kwargs):
        message = "Sage is really alive {}".format(datetime.now())
        print(job_scheduler.print_jobs())
        return render(
            request,
            'index.html',
            {'message': message})