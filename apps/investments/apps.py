from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InvestmentsConfig(AppConfig):
    name = 'apps.investments'
    verbose_name = _('Investissements')
    verbose_name_plural = _('Investissements')

    def ready(self):
        import apps.investments.signals  # noqa 