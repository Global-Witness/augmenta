# Tools

By default, Augmenta has access to two tools: a search engine and a tool for retrieving text from the internet.

However, you may be interested in empowering it to do more. For example, you may want to give it access to a database, or give it the power to write code or do complex calculations.

Augmenta supports this through [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) servers.

MCP servers are a standardised way to give LLMs access to tools and data. A few examples of MCP servers are:

- [Google Maps](https://github.com/modelcontextprotocol/servers/tree/main/src/google-maps) - Provides access to the Google Maps API, meaning you can use it to geocode addresses, get directions, find points of interest, etc.
- [Maigret](https://github.com/BurtTheCoder/mcp-maigret) - An OSINT tool for finding information about people online.
- [AWS KB Retrieval](https://github.com/modelcontextprotocol/servers/tree/main/src/aws-kb-retrieval-server) - Store your data in AWS and use Augmenta to retrieve it.
- [Filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) - Allow Augmenta to create and edit local files.

There's no official repository of MCP servers, but [several third-party ones are available](https://smithery.ai/). You can even [write your own MCP servers](https://modelcontextprotocol.io/quickstart/server)!

## Adding a tool to Augmenta

To add a new tool to Augmenta, you need to add it to an `mcpServers` section of your `config.yml` file. For example, to add the [Google Maps MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/google-maps), you would do the following:

```yaml
mcpServers:
  - name: google-maps
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-google-maps"
```

Note that the Google Maps server needs a `GOOGLE_MAPS_API_KEY` environment variable. You can add this to your `.env` file:

```bash
GOOGLE_MAPS_API_KEY=XXXXX
```

Augmenta will now have access to Google Maps. However, it will still have access to the default search tool, meaning it may decide to use it instead of the Google Maps server. You can explicitly tell the LLM to use the newly added tool in the prompts.