from django.apps import AppConfig


class LessonsConfig(AppConfig):
    name = "apps.lessons"

    def ready(self):
        import apps.lessons.signals
