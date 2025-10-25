# MCP

Here we describe how to connect the Filesystem MCP server to Claude Desktop on macOS.  
It enables Claude to read and write local files (for example: text, CSV, or JSON) directly from your computer.

## 1. Requirements

- macOS with Claude Desktop installed  
- Node.js and npm (install via Homebrew if missing)
  ```bash
  brew install node
  ```
- A folder where Claude will be allowed to read and write files
Example: ~/Desktop/MCP-Exports

## 2. Installation

1. Install the Filesystem MCP server globally:

```
npm install -g @modelcontextprotocol/server-filesystem
```

2. Create the Claude config folder and file if it does not exist:

```
mkdir -p "$HOME/Library/Application Support/Claude"
touch "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```

3. Open the config file in TextEdit:

```
open -a TextEdit "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```

4. Paste the following JSON configuration:

```
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/{your_username}/Desktop/MCP-Exports"
      ]
    }
  }
}
```
Adjust the path if you use a different export folder.

5. Save the file and restart Claude Desktop.

## 3. Usage

You can now ask Claude to interact with files in the configured folder (note that you'll also need to give some permissions through the process).

### Example prompts

- Create a text file:

``` 
Write a file named test.txt containing the line “MCP is working!” in my Desktop export folder.
```

- Read a file:

```
Read the contents of test.txt from my export folder.
```

- List files:
```
Show all files currently stored in the export folder.
```