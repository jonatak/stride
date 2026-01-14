import click
import uvicorn
from loguru import logger

from stride.agent import build_chat_agent, build_summary_agent
from stride.agent.types import AgentContext
from stride.app import create_fast_api_app
from stride.infra.influx import init_influx_connection
from stride.infra.postgres import init_postgres_connection
from stride.logger import init_logger, init_logging_override
from stride.types import AppContext


@click.command()
@click.option("--host", envvar="STRIDE_HOST", default="0.0.0.0", help="Api host.")
@click.option("--port", envvar="STRIDE_PORT", default=8080, help="Api port.")
@click.option("--influx-host", envvar="INFLUX_HOST", required=True)
@click.option("--influx-port", envvar="INFLUX_PORT", type=int, required=True)
@click.option("--influx-user", envvar="INFLUX_USER", required=True)
@click.option("--influx-password", envvar="INFLUX_PASSWORD", required=True)
@click.option("--influx-db", envvar="INFLUX_DB", required=True)
@click.option("--agent-model", envvar="AGENT_MODEL", required=True)
@click.option("--agent-summary-model", envvar="AGENT_SUMMARY_MODEL", required=True)
@click.option("--agent-base-url", envvar="AGENT_BASE_URL", required=True)
@click.option("--agent-api-key", envvar="AGENT_API_KEY", required=True)
@click.option("--mcp-url", envvar="MCP_URL", required=True)
@click.option("--pg-conn-url", envvar="POSTGRES_URL", required=True)
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
    agent_model: str,
    agent_summary_model: str,
    agent_base_url: str,
    agent_api_key: str,
    mcp_url: str,
    pg_conn_url: str,
    log_level: str,
):
    init_logger(log_level)
    init_logging_override()
    influx_conn = init_influx_connection(
        host=influx_host,
        port=influx_port,
        user=influx_user,
        password=influx_password,
        db=influx_db,
    )

    agent_ctx = AgentContext(
        agent_model=agent_model,
        agent_summary_model=agent_summary_model,
        agent_base_url=agent_base_url,
        agent_api_key=agent_api_key,
        mcp_url=mcp_url,
    )

    agent = build_chat_agent(agent_ctx)
    summary_agent = build_summary_agent(agent_ctx)

    pg_pool = init_postgres_connection(pg_conn_url)

    ctx = AppContext(
        influx_conn=influx_conn,
        pg_pool=pg_pool,
        agent=agent,
        summary_agent=summary_agent,
    )

    logger.info("Stride started...")
    app = create_fast_api_app(ctx)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_config=None,
        log_level=None,
    )


if __name__ == "__main__":
    main()
