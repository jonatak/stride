import click
import uvicorn
from loguru import logger

from stride.agent import build_agent
from stride.app import create_fast_api_app
from stride.domain.dao import init_connection
from stride.logger import init_logger, init_logging_override
from stride.agent.types import AgentContext
from stride.types import AppContext


@click.group()
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["INFO", "ERROR", "DEBUG", "WARN"]),
    help="Set the log level of the application.",
)
def cli(
    log_level: str,
):
    init_logger(log_level)
    init_logging_override()


@cli.command()
@click.option("--host", envvar="STRIDE_HOST", default="0.0.0.0", help="Api host.")
@click.option("--port", envvar="STRIDE_PORT", default=8080, help="Api port.")
@click.option("--influx-host", envvar="INFLUX_HOST", required=True)
@click.option("--influx-port", envvar="INFLUX_PORT", type=int, required=True)
@click.option("--influx-user", envvar="INFLUX_USER", required=True)
@click.option("--influx-password", envvar="INFLUX_PASSWORD", required=True)
@click.option("--influx-db", envvar="INFLUX_DB", required=True)
@click.option("--agent-model", envvar="AGENT_MODEL", required=True)
@click.option("--agent-base-url", envvar="AGENT_BASE_URL", required=True)
@click.option("--agent-api-key", envvar="AGENT_API_KEY", required=True)
@click.option("--mcp-url", envvar="MCP_URL", required=True)
def api(
    host: str,
    port: int,
    influx_host: str,
    influx_port: int,
    influx_user: str,
    influx_password: str,
    influx_db: str,
    agent_model: str,
    agent_base_url: str,
    agent_api_key: str,
    mcp_url: str,
):
    influx_conn = init_connection(
        host=influx_host,
        port=influx_port,
        user=influx_user,
        password=influx_password,
        db=influx_db,
    )

    agent_ctx = AgentContext(
        agent_model=agent_model,
        agent_base_url=agent_base_url,
        agent_api_key=agent_api_key,
        mcp_url=mcp_url,
    )

    agent = build_agent(agent_ctx)

    ctx = AppContext(
        influx_conn=influx_conn,
        agent=agent,
    )

    logger.info("Stride started...")
    app = create_fast_api_app(ctx)

    uvicorn.run(
        app,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    cli()
