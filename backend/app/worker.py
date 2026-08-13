import asyncio

from app.core.logging_config import configure_logging


async def main() -> None:
    configure_logging()
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
