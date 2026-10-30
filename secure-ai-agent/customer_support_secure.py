import asyncio
import base64
import json
import os
from urllib import error, parse, request

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.mcp import MCPAdapter

load_dotenv()


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


MCP_SERVER_URL = required_env("MCP_SERVER_URL")
DESCOPE_REQUIRED_SCOPES = os.getenv("DESCOPE_REQUIRED_SCOPES", "support:tools") #refunds:create"
DESCOPE_TOKEN_RESOURCE = os.getenv("DESCOPE_TOKEN_RESOURCE", MCP_SERVER_URL)

SYSTEM_PROMPT = (
    "You are a helpful customer support agent. Use available tools to look up "
    "customer information, order IDs, and product information. "
    "Always verify details using tools before answering. Never invent information. "
    "For refund requests, call process_refund when authorized and appropriate. "
    "Report the actual result returned by the tool. "
    "Never claim a refund succeeded if it failed or was already processed. "
    "If you cannot process a refund, explain why."
)


def fetch_json(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None) -> dict:
    request_headers = {"User-Agent": "customer-support-secure/1.0"}
    if headers:
        request_headers.update(headers)
    req = request.Request(url, data=data, headers=request_headers)
    try:
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Request to {url} failed with {exc.code}: {body}") from exc


def get_token_endpoint() -> str:
    override = os.getenv("DESCOPE_TOKEN_ENDPOINT")
    if override:
        return override

    config_url = required_env("DESCOPE_WELL_KNOWN_URL")
    metadata = fetch_json(config_url)
    token_endpoint = metadata.get("token_endpoint")
    return token_endpoint


def get_access_token() -> str:
    existing_token = os.getenv("DESCOPE_ACCESS_TOKEN")
    if existing_token:
        return existing_token

    client_id = required_env("DESCOPE_CLIENT_ID")
    client_secret = required_env("DESCOPE_CLIENT_SECRET")
    token_endpoint = get_token_endpoint()

    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    payload_params = {
        "grant_type": "client_credentials",
    }
    if DESCOPE_REQUIRED_SCOPES:
        payload_params["scope"] = DESCOPE_REQUIRED_SCOPES
    if DESCOPE_TOKEN_RESOURCE:
        payload_params["resource"] = DESCOPE_TOKEN_RESOURCE
    payload = parse.urlencode(payload_params).encode("utf-8")
    token_response = fetch_json(
        token_endpoint,
        data=payload,
        headers={
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "customer-support-secure/1.0",
        },
    )
    access_token = token_response.get("access_token")
    if not access_token:
        raise RuntimeError(f"Descope token response did not include access_token: {token_response}")
    return access_token


def get_mcp_server_config(access_token: str) -> dict:
    return {
        "mcpServers": {
            "support": {
                "url": MCP_SERVER_URL,
                "transport": "streamable-http",
                "headers": {
                    "Authorization": f"Bearer {access_token}",
                },
                "tools": ["*"],
            }
        }
    }

async def main() -> None:
    print("STEP 1: Getting Descope access token...")
    access_token = get_access_token()
    print("STEP 2: Access token obtained.")

    print("STEP 3: Connecting to MCP server...")

    config = get_mcp_server_config(access_token)

    async with MCPAdapter(config) as client:
        print("STEP 4: MCP connection successful!")

        mcp_tools = await client.list_tools()

        print("\nAvailable MCP tools:")
        for tool in mcp_tools:
            print("-", tool.name)

        agent = create_agent(
            ChatOpenAI(
                model="gpt-4.1-mini",
                temperature=0,
            ),
            mcp_tools,
            system_prompt=SYSTEM_PROMPT,
        )

        query = (
            'Hi, my order ID is ord_1001. I want a refund. '
            'The order details are: customer_id cust_001, '
            'item Wireless Mouse, amount 29.99, status delivered. '
            'Please process the refund if authorized.'
        )

        result = await agent.ainvoke({
            "messages": [("user", query)]
        })

        print("\nCUSTOMER SUPPORT RESPONSE:")
        print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())