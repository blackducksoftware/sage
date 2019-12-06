from django.contrib import admin

# Register your models here.
from .models import Job, JobRun, HubInstance, Sage

class JobAdmin(admin.ModelAdmin):
    fields = [
        'job_name', 
        'job_type', 
        'job_args', 
        'description', 
        'running', 
        'trigger_type', 
        'trigger_args',
        'created_at',
        'updated_at',
    ]
    readonly_fields = ('created_at', 'updated_at')

class HubInstanceAdmin(admin.ModelAdmin):
    fields = [
        'url',
        'api_token',
        'insecure',
        'created_at',
        'updated_at'
    ]
    readonly_fields = ('created_at', 'updated_at')

class JobRunAdmin(admin.ModelAdmin):
    fields = ['result', 'created_at']
    readonly_fields = ['result', 'created_at']

admin.site.register(Job, JobAdmin)
admin.site.register(JobRun, JobRunAdmin)
admin.site.register(HubInstance, HubInstanceAdmin)
admin.site.register(Sage)