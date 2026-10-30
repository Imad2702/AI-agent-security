"""MCP server exposing the support-agent tools vis FastMCP."""

from fastmcp import FastMCP
import tools
mcp = FastMCP("Support Tools Server")


@mcp.tool
def answer_user_query(query: str) -> str:
    """Return a canned answer to a user's question."""
    return tools.answer_user_query(query)

@mcp.tool
def process_refund(order_id: str) -> dict:
    """process refund for a given order ID"""
    return tools.process_refund(order_id)

@mcp.tool
def get_order_id(customer_id: str) -> str | None:
    """Look up the order ID for a given customer ID."""
    return tools.get_order_id(customer_id)

@mcp.tool
def lookup_customer_info(customer_id: str) -> dict | None:
    """Return customer info for a given customer ID."""
    return tools.lookup_customer_info(customer_id)

@mcp.tool
def list_customers() -> list[dict]:
    """Return a list of all customers."""
    return tools.list_customers()


@mcp.tool
def get_product_info(product: str) -> dict | None:
    """Return product info (name, price) for a product ID or name (e.g. 'macbook', 'iPhone')."""
    return tools.get_product_info(product)


app = mcp.http_app(path="/mcp", transport="streamable-http", stateless_http=True, json_response=True)


if __name__ == "__main__":
    mcp.run()
