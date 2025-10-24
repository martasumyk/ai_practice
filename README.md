# Agents practice

## Computer Use Agent (Anthropic)

### Intro

The agent takes a  task description (e.g. “Open Safari and search for apple.com website")  
and autonomously performs (well, at least tries) the corresponding  actions on your screen.

Each step is recorded with:
- A screenshot
- The model response
- The tool invocation and results

The outputs are stored in the `anthropic_trajectories/` folder, creating a trace of the task execution.


### Setup

Install requirements: 

``` 
pip install -r requirements.txt 
```

Set your Anthropic API key:

```
export ANTHROPIC_API_KEY="your_api_key_here"
```

Run the task:

```
python anthropic_computer_use.py task_description
```

For example:

```
python anthropic_computer_use.py “Open Safari and search for apple.com website"
```

## MCP 


This section shows how to connect a Google Maps MCP serve running in Docker to Claude Desktop using the MCP.  
After setup, you’ll be able to ask Claude for routes, coordinates, or nearby places.


Goal: run the official [`mcp/google-maps-comprehensive`](https://hub.docker.com/r/mcp/google-maps-comprehensive) image locally, connect it to Claude Desktop via a simple JSON config, and call Maps tools interactively.

**Tools included:**  


What you’ll nee
- Claude Desktop
- Docker Desktop*
- A valid Google Maps API key

### Setup steps (on macOS)



1. Install google maps image for Docker:

```
docker pull mcp/google-maps-comprehensive
```

or simply go to https://hub.docker.com/mcp/server/google-maps-comprehensive/config and click "Add to Docker Desktop".

2. Find Claude config
Open the config file in your editor:

```bash
open -a "Visual Studio Code" "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```


3. Paste this JSON into the config:

``` 
{
  "mcpServers": {
    "google-maps": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GOOGLE_MAPS_API_KEY",
        "mcp/google-maps-comprehensive"
      ],
      "env": {
        "GOOGLE_MAPS_API_KEY": "${input:maps_api_key}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/<your_username>/Desktop/MCP-Exports"
      ]
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "maps_api_key",
      "description": "Google Maps API Key",
      "password": true
    }
  ]
}
```

4. Restart Claude Desktop



### Prompt example

Once you have all of the above installations, you can paste the prompt into Claude Desktop console, for example:

```
Using the google-maps tools, find the coordinates and address of
Ukrainian Catholic University, Lviv. Then suggest 3 coffee shops within 1 km.
```