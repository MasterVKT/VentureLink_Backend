from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ProjectsConfig(AppConfig):
    name = 'apps.projects'
    verbose_name = _('Projets')
    verbose_name_plural = _('Projets')

    def ready(self):
        import apps.projects.signals 