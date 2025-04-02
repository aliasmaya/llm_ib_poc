# llm_ib_poc: LLM with IB Tools PoC

## Overview

This Proof of Concept (PoC) project integrates a Large Language Model (LLM) using a locally deployed DeepSeek model via Ollama with Interactive Brokers (IB) TWS API tools via `ib_insync` and FastMCP. The IB tools are embedded directly within the LLM application, allowing the AI to discover and use these tools for natural language processing (NLP) tasks such as trading, market data retrieval, and account management.

## Features

- Uses DeepSeek via Ollama for local NLP to interpret user commands.
- Integrates [ib-mcp](https://github.com/aliasmaya/ib-mcp) tools internally for direct invocation within the same application.
- Discovers and calls tools dynamically using FastMCP.
- Handles IB TWS API interactions locally.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/aliasmaya/llm_ib_poc.git
   cd llm_ib_poc
   ```

2. Install dependencies:

   ```bash
   pip install fastmcp ib_insync python-dotenv openai asyncio
   ```

3. Install and run Ollama locally, and pull the DeepSeek model:

   ```bash
   ollama pull deepseek
   ollama serve  # Run Ollama in the background
   ```

4. Create a `.env` file in the project root with:

   ```ini
   IB_HOST=127.0.0.1
   IB_PORT=7497
   IB_CLIENT=1
   OPENAI_API_KEY=sk-...
   MODEL=qwen2.5:14b
   BASE_URL=http://localhost:11434/v1
   ```

## Usage

Run the LLM application:

```bash
python app.py
```

Interact with the assistant by typing commands like:

- "What’s the current price of AAPL?"
- "Buy 100 shares of AAPL at $150"

The application will use DeepSeek via Ollama to interpret your command and call the appropriate IB tool if needed.

## Contributing

Contributions are welcome! Please fork the repository, make changes, and submit a pull request.

## License

MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Ollama](https://ollama.com) for local LLM deployment.
- [FastMCP](https://github.com/jlowin/fastmcp) for tool discovery.
- [ib_insync](https://github.com/erdewit/ib_insync) for IB TWS API integration.
