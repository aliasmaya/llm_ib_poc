from fastmcp import FastMCP
from ib_insync import IB, Stock, LimitOrder
from dotenv import load_dotenv
import os
from typing import Dict, Any, Callable

load_dotenv()
IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT = int(os.getenv("IB_PORT", 7497))
IB_CLIENT = int(os.getenv("IB_CLIENT", 1))

mcp = FastMCP("IB_TWS_MCP")

ib = None
TOOLS: Dict[str, Callable] = {}

def create_response(result: str, message: str) -> Dict[str, Any]:
    """Helper function to create a standardized response."""
    return {"result": result, "message": message}

@mcp.tool()
def connect() -> Dict[str, Any]:
    """Connect to IB TWS or Gateway using values from .env file.

    This tool establishes a connection to the Interactive Brokers TWS or Gateway using 
    configuration values loaded from a .env file (IB_HOST, IB_PORT, IB_CLIENT).

    Returns:
        Dict[str, Any]: A dictionary with 'result' ('success' or 'failed') and 'message' 
        describing the connection status or error.
    """
    global ib
    try:
        ib = IB()
        ib.connect(IB_HOST, IB_PORT, IB_CLIENT)
        return create_response("success", f"Connected to IB TWS at {IB_HOST}:{IB_PORT} with client ID {IB_CLIENT}")
    except Exception as e:
        return create_response("failed", f"Failed to connect: {str(e)}")

TOOLS["connect"] = connect

@mcp.tool()
def disconnect() -> Dict[str, Any]:
    """Disconnect from IB TWS or Gateway.

    This tool terminates the current connection to the Interactive Brokers TWS or Gateway.

    Returns:
        Dict[str, Any]: A dictionary with 'result' ('success' or 'failed') and 'message' 
        describing the disconnection status or error.
    """
    global ib
    if ib is not None and ib.isConnected():
        ib.disconnect()
        return create_response("success", "Disconnected from IB TWS")
    return create_response("failed", "No active connection to disconnect")

TOOLS["disconnect"] = disconnect

@mcp.tool()
def qualifyContracts(symbol: str, secType: str = "STK", exchange: str = "SMART", currency: str = "USD") -> Dict[str, Any]:
    """Qualify a contract by filling in missing fields.

    Args:
        symbol (str): The trading symbol of the contract (e.g., "AAPL" for Apple Inc.).
        secType (str, optional): Security type. Defaults to "STK" (Stock). Other options include "OPT", "FUT", etc.
        exchange (str, optional): The exchange where the contract is traded. Defaults to "SMART" (Smart routing).
        currency (str, optional): The currency of the contract. Defaults to "USD".

    Returns:
        Dict[str, Any]: A dictionary with 'result' ('success' or 'failed') and 'message' 
        containing the qualified contract details or an error message.
    """
    global ib
    if ib is None or not ib.isConnected():
        return create_response("failed", "Not connected to IB TWS. Use 'connect' first.")

    contract = Stock(symbol, exchange, currency)
    try:
        qualified_contracts = ib.qualifyContracts(contract)
        if qualified_contracts:
            return create_response("success", {"contract": vars(qualified_contracts[0])})
        return create_response("failed", "Contract qualification failed")
    except Exception as e:
        return create_response("failed", str(e))
    
TOOLS["qualifyContracts"] = qualifyContracts

@mcp.tool()
def reqMktData(symbol: str, secType: str = "STK", exchange: str = "SMART", currency: str = "USD") -> Dict[str, Any]:
    """Request market data for a contract.

    Args:
        symbol (str): The trading symbol of the contract (e.g., "AAPL" for Apple Inc.).
        secType (str, optional): Security type. Defaults to "STK" (Stock). Other options include "OPT", "FUT", etc.
        exchange (str, optional): The exchange where the contract is traded. Defaults to "SMART" (Smart routing).
        currency (str, optional): The currency of the contract. Defaults to "USD".

    Returns:
        Dict[str, Any]: A dictionary with 'result' ('success' or 'failed') and 'message' 
        containing market data (bid, ask, last, volume) or an error message.
    """
    global ib
    if ib is None or not ib.isConnected():
        return create_response("failed", "Not connected to IB TWS. Use 'connect' first.")

    contract = Stock(symbol, exchange, currency)
    ib.qualifyContracts(contract)
    try:
        ticker = ib.reqMktData(contract)
        ib.sleep(1)  # Wait briefly for data to arrive
        return create_response("success", {
            "symbol": symbol,
            "bid": ticker.bid,
            "ask": ticker.ask,
            "last": ticker.last,
            "volume": ticker.volume
        })
    except Exception as e:
        return create_response("failed", str(e))
    
TOOLS["reqMktData"] = reqMktData

@mcp.tool()
def placeOrder(symbol: str, action: str, quantity: float, limitPrice: float, secType: str = "STK", exchange: str = "SMART", currency: str = "USD") -> Dict[str, Any]:
    """Place a limit order for a contract.

    Args:
        symbol (str): The trading symbol of the contract (e.g., "AAPL" for Apple Inc.).
        action (str): The order action ("BUY" or "SELL").
        quantity (float): The number of shares or contracts to trade.
        limitPrice (float): The limit price for the order.
        secType (str, optional): Security type. Defaults to "STK" (Stock). Other options include "OPT", "FUT", etc.
        exchange (str, optional): The exchange where the contract is traded. Defaults to "SMART" (Smart routing).
        currency (str, optional): The currency of the contract. Defaults to "USD".

    Returns:
        Dict[str, Any]: A dictionary with 'result' ('success' or 'failed') and 'message' 
        containing the order ID and details or an error message.
    """
    global ib
    if ib is None or not ib.isConnected():
        return create_response("failed", "Not connected to IB TWS. Use 'connect' first.")

    contract = Stock(symbol, exchange, currency)
    ib.qualifyContracts(contract)
    order = LimitOrder(action, quantity, limitPrice)
    try:
        trade = ib.placeOrder(contract, order)
        ib.sleep(1)  # Wait briefly for order to be placed
        return create_response("success", {"orderId": trade.order.orderId, "details": vars(trade.order)})
    except Exception as e:
        return create_response("failed", str(e))
    
TOOLS["placeOrder"] = placeOrder

@mcp.tool()
def positions(account: str = "") -> Dict[str, Any]:
    """Retrieve current positions for the account.

    Args:
        account (str, optional): The account ID. If empty, uses the default account. Defaults to "".

    Returns:
        Dict[str, Any]: A dictionary with 'result' ('success' or 'failed') and 'message' 
        containing a list of positions (symbol, quantity, avgCost) or an error message.
    """
    global ib
    if ib is None or not ib.isConnected():
        return create_response("failed", "Not connected to IB TWS. Use 'connect' first.")

    try:
        positions_list = ib.positions(account)
        return create_response("success", [{"symbol": pos.contract.symbol, "quantity": pos.position, "avgCost": pos.avgCost} for pos in positions_list])
    except Exception as e:
        return create_response("failed", str(e))
    
TOOLS["positions"] = positions

@mcp.tool()
def accountValues(account: str = "") -> Dict[str, Any]:
    """Retrieve account values for the specified account.

    Args:
        account (str, optional): The account ID. If empty, uses the default account. Defaults to "".

    Returns:
        Dict[str, Any]: A dictionary with 'result' ('success' or 'failed') and 'message' 
        containing a list of account values (key, value, currency) or an error message.
    """
    global ib
    if ib is None or not ib.isConnected():
        return create_response("failed", "Not connected to IB TWS. Use 'connect' first.")

    try:
        values = ib.accountValues(account)
        return create_response("success", [{"key": val.tag, "value": val.value, "currency": val.currency} for val in values])
    except Exception as e:
        return create_response("failed", str(e))
    
TOOLS["accountValues"] = accountValues

__all__ = ["TOOLS"]