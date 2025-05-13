# mcp-ws

A CLI tool to connect local stdio (standard input/output) to a remote WebSocket server.

## Overview

`mcp-ws` is designed to be complementary to [ws-mcp](https://github.com/nick1udwig/ws-mcp), which wraps stdio servers with websockets. This tool provides the client-side functionality, allowing you to connect to those websocket servers from your terminal.

Unlike [wscat](https://github.com/websockets/wscat), `mcp-ws` doesn't output prompts like `>` and `<` which can confuse MCP clients.

## Installation

### Using pip

```bash
pip install mcp-ws
```

### Using UVX

```bash
uvx install mcp-ws
```

## Usage

```bash
mcp-ws <websocket-url>
```

Example:

```bash
mcp-ws wss://example.com/socket
```

## Features

- Clean bidirectional communication between stdio and websockets
- No confusing prompts or formatting that could interfere with MCP clients
- Asynchronous handling of input/output
- Proper error handling and connection management

## Development

```bash
# Clone the repository
git clone <repository-url>
cd mcp-ws

# Install dependencies
uv pip install -e .

# Run the application
python -m mcp_ws <websocket-url>
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.