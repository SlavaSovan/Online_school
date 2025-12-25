from django.apps import AppConfig


class ModulesConfig(AppConfig):
    name = "apps.modules"

    def ready(self):
        import apps.modules.signals
