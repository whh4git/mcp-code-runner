# Execute code in a container or virtual machine environment.

```json
{
  "mcpServers": {
    "HhRwXh-Ka1FQjOFHoDM5E": {
      "name": "mcp-code-runner",
      "type": "stdio",
      "isActive": true,
      "registryUrl": "",
      "longRunning": true,
      "tags": [],
      "command": "uv",
      "args": [
        "--directory",
        "<path>",
        "run",
        "main.py",
        "--name=<container>"
      ]
    },
  }
}
```