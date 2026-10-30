"""Descope-protected MCP server with explicit per-tool scope checks."""

import os

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.utilities.authorization import require_scopes

import tools


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


DESCOPE_PROJECT_ID = required_env("DESCOPE_PROJECT_ID")
DESCOPE_MCP_SERVER_ID = required_env("DESCOPE_MCP_SERVER_ID")
DESCOPE_BASE_URL = os.getenv("DESCOPE_BASE_URL", "https://api.descope.com").rstrip("/")
DESCOPE_JWKS_URI = os.getenv(
    "DESCOPE_JWKS_URI",
    f"{DESCOPE_BASE_URL}/{DESCOPE_PROJECT_ID}/.well-known/jwks.json",
)
DESCOPE_ISSUER = os.getenv("DESCOPE_ISSUER", f"{DESCOPE_BASE_URL}/{DESCOPE_PROJECT_ID}")

auth = JWTVerifier(
    jwks_uri=DESCOPE_JWKS_URI,
    issuer=DESCOPE_ISSUER,
    audience=DESCOPE_MCP_SERVER_ID,
)

mcp = FastMCP("Scoped Support Tools Server", auth=auth)


@mcp.tool(auth=require_scopes("support:tools"))
def answer_user_query(query: str) -> str:
    """Return a canned answer to a user's question."""
    return tools.answer_user_query(query)


@mcp.tool(auth=require_scopes("support:tools", "refunds:create"))
def process_refund(order_id: str) -> dict:
    """Process a refund for a given order ID."""
    return tools.process_refund(order_id)


@mcp.tool(auth=require_scopes("support:tools"))
def get_order_id(customer_id: str) -> str | None:
    """Look up the order ID for a given customer ID."""
    return tools.get_order_id(customer_id)


@mcp.tool(auth=require_scopes("support:tools"))
def lookup_customer_info(customer_id: str) -> dict | None:
    """Return customer info for a given customer ID."""
    return tools.lookup_customer_info(customer_id)


@mcp.tool(auth=require_scopes("support:tools"))
def get_product_info(product: str) -> dict | None:
    """Return product info (name, price) for a product ID or name (e.g. 'macbook', 'iPhone')."""
    return tools.get_product_info(product)


app = mcp.http_app(
    path="/mcp",
    transport="streamable-http",
    stateless_http=True,
    json_response=True,
)


if __name__ == "__main__":
    mcp.run()