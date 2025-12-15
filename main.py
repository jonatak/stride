import click
import uvicorn
from loguru import logger

from stride.api import create_fast_api_app
from stride.dao import init_connection
from stride.logger import init_logger, init_logging_override
from stride.types import AppContext


@click.command()
@click.option("--host", default="0.0.0.0", help="Api host.")
@click.option("--port", default=8080, help="Api port.")
@click.option("--influx-host", envvar="INFLUX_HOST", required=True)
@click.option("--influx-port", envvar="INFLUX_PORT", type=int, required=True)
@click.option("--influx-user", envvar="INFLUX_USER", required=True)
@click.option("--influx-password", envvar="INFLUX_PASSWORD", required=True)
@click.option("--influx-db", envvar="INFLUX_DB", required=True)
@click.option("--max-hr", envvar="MAX_HR", type=int, required=True)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["INFO", "ERROR", "DEBUG", "WARN"]),
    help="Set the log level of the application.",
)
def main(
    host: str,
    port: int,
    influx_host: str,
    influx_port: int,
    influx_user: str,
    influx_password: str,
    influx_db: str,
    max_hr: int,
    log_level: str,
):
    init_logger(log_level)
    init_logging_override()

    influx_conn = init_connection(
        host=influx_host,
        port=influx_port,
        user=influx_user,
        password=influx_password,
        db=influx_db,
    )

    ctx = AppContext(
        influx_conn=influx_conn,
        max_hr=max_hr,
    )

    logger.info("Stride started...")
    app = create_fast_api_app(ctx)
    uvicorn.run(
        app,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    main()
