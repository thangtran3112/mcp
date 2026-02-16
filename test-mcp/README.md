# Flight Simulator MCP Server

An enhanced Model Context Protocol (MCP) server for comprehensive airline booking operations, built with FastMCP 2.0 and Python. Supports both stdio (local) and Streamable HTTP (remote/AWS) transports.

## Features

### Core Booking Tools

- **Flight Search & Booking**: Multi-criteria search, booking creation, modifications
- **Check-in & Services**: Online check-in, seat selection, baggage, meal preferences
- **Real-time Operations**: Flight tracking, price alerts, disruption handling
- **Loyalty & Groups**: Frequent flyer integration, group bookings, special assistance

### Information Resources

- Airport information with timezones
- Real-time flight status
- Seat maps and availability
- Weather impact data
- Airline policies
- Gate information

### AI-Powered Prompts

- Intelligent flight search assistance
- Complete booking workflow guidance
- Disruption management

## Installation

### Prerequisites

- Python 3.10 or higher
- UV package manager (recommended) or pip

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd flight-mcp-demo
```

2. Install dependencies using UV (recommended):

```bash
uv pip install -r requirements.txt
```

Or using pip:

```bash
pip install -r requirements.txt
```

3. Copy environment configuration:

```bash
cp .env.example .env
```

## Usage

### Running the Server

The easiest way to start the server is using the interactive startup script:

```bash
./start.sh
```

This will prompt you to choose:

1. **stdio** - For local development / Claude Desktop
2. **Streamable HTTP** - For remote/AWS deployment (with host/port prompts)
3. **MCP Inspector** - For debugging and testing

#### Non-interactive Mode

You can also pass arguments directly:

```bash
./start.sh http               # Start HTTP on 0.0.0.0:8000
./start.sh http 0.0.0.0 8080  # Start HTTP on custom host:port
```

#### Direct Python Command

```bash
# stdio
python src/server.py

# Streamable HTTP
python src/server.py --transport streamable-http --host 0.0.0.0 --port 8000
```

### Integration with Claude Desktop

1. Open your Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the flight simulator server:

```json
{
  "mcpServers": {
    "flight-simulator": {
      "command": "python",
      "args": ["/path/to/flight-mcp-demo/src/server.py"],
      "env": {}
    }
  }
}
```

3. Restart Claude Desktop

### Connecting to Remote Server

For Streamable HTTP transport, the MCP endpoint is:

```
http://<host>:<port>/mcp
```

#### Using MCP Inspector with HTTP

1. Start the server in HTTP mode:

```bash
./start.sh http
# Enter host: 127.0.0.1
# Enter port: 8000
```

2. Open MCP Inspector: `npx @modelcontextprotocol/inspector`

3. Configure connection:
   - **Transport Type**: `Streamable HTTP`
   - **URL**: `http://127.0.0.1:8000/mcp`
   - Click **Connect**

#### Claude Desktop with Remote Server

Use `mcp-remote` to connect Claude Desktop to a remote HTTP server:

```json
{
  "mcpServers": {
    "flight-simulator-remote": {
      "command": "npx",
      "args": ["mcp-remote", "http://your-server:8000/mcp"]
    }
  }
}
```

### Example Interactions

**Flight Search:**

```
"Find me a flight from San Francisco to New York next Friday"
```

**Group Booking:**

```
"I need to book flights for 8 people from SFO to JFK on March 15th"
```

**Check-in:**

```
"Check me in for booking BK12345ABC"
```

## Available Tools

### Flight Search & Booking

- `search_flights` - Search with multiple criteria
- `get_flight_details` - Detailed flight information
- `create_booking` - Book flights
- `get_booking` - Retrieve booking details
- `cancel_booking` - Cancel with refund calculation

### Check-in & Services

- `check_in` - Online check-in with boarding passes

## Testing

### Using MCP Inspector

```bash
npx @modelcontextprotocol/inspector python src/server.py
```

### Running Unit Tests

```bash
pytest tests/
```

## Project Structure

```
flight-mcp-demo/
├── src/
│   ├── server.py           # Main MCP server
│   ├── tools/              # Tool implementations
│   ├── resources/          # Resource endpoints
│   ├── models/             # Pydantic data models
│   ├── data/               # Mock database
│   └── prompts/            # AI prompt templates
├── tests/                  # Test files
├── pyproject.toml          # Project configuration
├── requirements.txt        # Dependencies
└── README.md               # This file
```

## Deployment

### Local Development

The default stdio transport is perfect for local development and testing with Claude Desktop.

### AWS Deployment (Streamable HTTP)

1. Set environment variables:

```bash
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8000
```

2. Deploy options:
   - **ECS/Fargate**: Recommended for production, supports auto-scaling
   - **App Runner**: Simple container deployment
   - **EC2**: Full control over infrastructure

3. Example Docker deployment:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
EXPOSE 8000
CMD ["python", "src/server.py", "--transport", "streamable-http"]
```

### Debugging AWS Deployments

#### Option 1: Public Endpoint (ALB/API Gateway)

If your service has a public endpoint, connect MCP Inspector directly:

```
http://<alb-dns-name>:8000/mcp
```

#### Option 2: SSH Tunnel (Private VPC)

For services in a private subnet, tunnel through a bastion host:

```bash
# Create SSH tunnel
ssh -L 8000:<ecs-task-private-ip>:8000 ec2-user@bastion-host

# Connect MCP Inspector to:
# http://127.0.0.1:8000/mcp
```

#### Option 3: AWS Systems Manager (No SSH)

For ECS/Fargate without SSH access:

```bash
# Port forward through SSM
aws ssm start-session \
  --target <instance-id> \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{"host":["<task-ip>"],"portNumber":["8000"],"localPortNumber":["8000"]}'

# Connect to http://127.0.0.1:8000/mcp
```

#### Option 4: ECS Exec (Direct Container Access)

Enable ECS Exec on your service, then:

```bash
# Get a shell in the container
aws ecs execute-command \
  --cluster <cluster-name> \
  --task <task-id> \
  --container flight-mcp \
  --interactive \
  --command "/bin/sh"
```

### Health Check Endpoint

The Streamable HTTP server exposes a health check at:

```
GET http://<host>:<port>/health
```

Use this for ALB/ECS health checks.

## Security Considerations

- API tokens should be stored in environment variables
- Payment tokens are mocked - implement real payment integration for production
- Rate limiting is recommended for production deployments
- Use HTTPS in production (via load balancer or reverse proxy)
- For production, add authentication to the MCP endpoint

## License

MIT License
