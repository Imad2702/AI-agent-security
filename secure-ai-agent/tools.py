from typing import Optional

# Mock database
DB = {
    "customers": {
        "cust_001": {"name": "Alice Johnson", "email": "alice@example.com", "tier": "gold"},
        "cust_002": {"name": "Bob Smith", "email": "bob@example.com", "tier": "silver"},
    },
    "orders": {
        "ord_1001": {"customer_id": "cust_001", "item": "Wireless Mouse", "amount": 29.99, "status": "delivered"},
        "ord_1002": {"customer_id": "cust_002", "item": "Keyboard", "amount": 49.99, "status": "shipped"},
    },
    "refunds": {},
}

# Mock product database
PRODUCTS_DB = {
    "prod_macbook": {"name": "MacBook Pro 14\"", "price": 1999.99},
    "prod_iphone": {"name": "iPhone 16 Pro", "price": 999.99},
}

def answer_user_query(query: str) -> str:
    """Return a canned answer to a user's question"""
    return f"Thanks for your question: '{query}'. A support agent will get back to you shortly."

# create a simple list customer tool
def list_customer() -> list[dict]:
    """Return a list of all customers"""
    return [{"customer_id": cid, **info} for cid, info in DB["customers"].items()]

def get_order_id(customer_id: str) -> Optional[str]:
    """Look up the order ID for a given customer ID"""
    for order_id, order in DB["orders"].items():
        if order["customer_id"] ==customer_id:
            return order_id
    return None

def lookup_customer_info(customer_id: str) -> Optional[dict]:
    """Return customer info for a given customer ID"""
    return DB["customers"].get(customer_id)

def get_product_info(product: str) -> Optional[dict]:
    """Return product info (name, price) for a product ID or name."""
    product = product.strip().lower()
    for product_id, info in PRODUCTS_DB.items():
        if product == product.lower() or product in info["name"].lower():
            return info
    return None         

def process_refund(order_id: str) -> dict:
    """process a refund for a given order ID."""
    order = DB["orders"].get(order_id)
    if order is None:
        return {"success": False, "message": f"Order '{order_id}' not found."}
    if order_id in DB["refunds"]:
        return {"success": False, "message": f"Order '{order_id}' was already refunded."}
    DB["refunds"][order_id] = {"amount": order["amount"], "status": "refunded"}
    return {"success": True, "message": f"Refunded ${order['amount']:.2f} for order '{order_id}'."}
