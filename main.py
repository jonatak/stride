import click
import uvicorn
from loguru import logger

from stride.api import create_fast_api_app
from stride.logger import init_logger, init_logging_override


@click.command()
@click.option("--host", default="0.0.0.0", help="Api host.")
@click.option("--port", default=8080, help="Api port.")
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["INFO", "ERROR", "DEBUG", "WARN"]),
    help="Set the log level of the application.",
)
def main(host: str, port: int, log_level: str):
    init_logger(log_level)
    init_logging_override()
    logger.info("Stide started...")
    app = create_fast_api_app()
    uvicorn.run(
        app,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    main()
