import signal
import sys
from django.core.management.base import BaseCommand
from apps.lessons.event_handlers import start_event_listener


class Command(BaseCommand):
    help = "Run Redis event listener"

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        self.stdout.write(self.style.WARNING("\nShutting down event listener..."))
        sys.exit(0)

    def handle(self, *args, **kwargs):
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.stdout.write(self.style.SUCCESS("Starting event listener..."))

        try:
            start_event_listener()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nEvent listener stopped"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            sys.exit(1)
