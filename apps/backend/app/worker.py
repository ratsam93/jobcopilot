import signal
import time

from apps.backend.app.config import settings


_running = True


def _handle_shutdown(*_: object) -> None:
    global _running
    _running = False


def main() -> None:
    print(f"Job Copilot worker starting with database={settings.database_url}")
    print(f"Job Copilot worker using redis={settings.redis_url}")
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)
    while _running:
        time.sleep(5)
    print("Job Copilot worker stopping")


if __name__ == "__main__":
    main()
