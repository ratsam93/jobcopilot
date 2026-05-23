from apps.backend.app.config import settings


def main() -> None:
    print(f"Job Copilot worker starting with database={settings.database_url}")
    print(f"Job Copilot worker using redis={settings.redis_url}")


if __name__ == "__main__":
    main()
