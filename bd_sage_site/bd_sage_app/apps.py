from django.apps import AppConfig
from django.conf import settings

class BdSageAppConfig(AppConfig):
    name = 'bd_sage_app'

    def ready(self):
        from sage import scheduler

        if settings.SCHEDULER_AUTOSTART:
            scheduler.start()
