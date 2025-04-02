import asyncio
import openai
from dotenv import load_dotenv
import os
from ib import TOOLS
from typing import Dict, Any
import re
import inspect

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("BASE_URL")
model = os.getenv("MODEL")
client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)

def get_tool_schema(tool_name: str, tool_func: callable) -> str:
    """Generate a schema description for a tool based on its signature and docstring."""
    sig = inspect.signature(tool_func)
    params = []
    for param_name, param in sig.parameters.items():
        param_type = param.annotation.__name__ if param.annotation != inspect.Parameter.empty else "unknown"
        default = f", default '{param.default}'" if param.default != inspect.Parameter.empty else ""
        params.append(f"{param_name} ({param_type}{default})")
    
    docstring = inspect.getdoc(tool_func) or "No description available."
    docstring = " ".join(docstring.split())
    return f"{tool_name}: Parameters: {', '.join(params) if params else 'No parameters'}. {docstring}"

async def call_openai(prompt: str, is_connected: bool = False) -> Dict[str, Any]:
    """Call OpenAI API to process NLP and determine tool calls."""
    connection_status = "already connected" if is_connected else "not connected"
    tool_schemas = {name: get_tool_schema(name, func) for name, func in TOOLS.items()}
    system_prompt = (
        f"You are a financial assistant that executes trading commands and retrieves market data. "
        f"The connection status to IB TWS is currently {connection_status}. "
        "If the connection is not established (i.e., connection status is 'not connected'), include a 'connect' tool call as the first action in the sequence, "
        "followed by the tool call for the user's request. "
        "If the connection is already established (i.e., connection status is 'already connected'), only include the tool call for the user's request. "
        "Use only the following tools with their exact parameters as defined in their schemas (no extra fields): " +
        ", ".join(tool_schemas.values()) + ". "
        "Respond with a JSON object containing 'actions' (a list of tool calls). Each tool call in the list must have 'name' (tool name) and 'parameters'. "
        "Execute all actions in the list sequentially. "
        "Examples: "
        "- If user says 'What’s the current price of AAPL?' and connection is not established: "
        "{'actions': [{'name': 'connect', 'parameters': {}}, {'name': 'reqMktData', 'parameters': {'symbol': 'AAPL', 'secType': 'STK', 'exchange': 'SMART', 'currency': 'USD'}}]} "
        "- If connection is already established: "
        "{'actions': [{'name': 'reqMktData', 'parameters': {'symbol': 'AAPL', 'secType': 'STK', 'exchange': 'SMART', 'currency': 'USD'}}]} "
        "- If user says 'Disconnect': "
        "{'actions': [{'name': 'disconnect', 'parameters': {}}]}"
    )
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        stream=True
    )
    collected_messages = []
    async for chunk in response:
        chunk_message = chunk.choices[0].delta.content or ""
        collected_messages.append(chunk_message)
        print(chunk_message, end="", flush=True)

    print()
    full_response = "".join(collected_messages).strip()
    if not full_response:
        raise ValueError("Empty response from streaming LLM")
    full_response = re.sub('false', 'False', full_response)
    full_response = re.sub('true', 'True', full_response)
    return full_response

def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the specified tool with given parameters."""
    if tool_name not in TOOLS:
        return {"result": "failed", "message": f"Unknown tool: {tool_name}"}
    
    tool = TOOLS[tool_name]
    try:
        print(f'Activate tool: {tool_name}, with arguments: {params}')
        result = tool(**params)
        return result
    except Exception as e:
        return {"result": "failed", "message": f"Error executing {tool_name}: {str(e)}"}

async def main():
    is_connected = False
    print("Financial Assistant: How can I help you today? (type 'exit' to quit)")
    while True:
        user_input = input("> ")
        if user_input.lower() == 'exit':
            break

        ai_response = await call_openai(user_input, is_connected)
        try:
            response_data = eval(ai_response)
            actions = response_data.get("actions", [])

            if not actions:
                print("Assistant: No actions returned by the LLM.")
                continue

            for action in actions:
                tool_name = action.get("name")
                params = action.get("parameters", {})

                tool_result = execute_tool(tool_name, params)
                print(f"Tool Result ({tool_name}): {tool_result}")

                if tool_name == "connect":
                    if tool_result["result"] == "success":
                        is_connected = True
                elif tool_name == "disconnect":
                    if tool_result["result"] == "success":
                        is_connected = False
        except Exception as e:
            print(f"Error processing response: {e}")

if __name__ == "__main__":
    asyncio.run(main())