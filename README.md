# MCP LaTeX Server - Windows Installation

## 📍 Locations on your system

  - **MCP Server**: `C:\Users\username\Documents\MCP\latex-server\`
  - **LaTeX Projects**: `C:\Users\username\Documents\LaTeX\`
  - **Claude Config**: `C:\Users\username\AppData\Roaming\Claude\claude_desktop_config.json`

## ⚡ Manual Installation

1.  **Create the directories**:

    ```cmd
    mkdir C:\Users\username\Documents\MCP\latex-server
    mkdir C:\Users\username\Documents\LaTeX
    ```

2.  **Install dependencies**:

    ```cmd
    cd C:\Users\username\Documents\MCP\latex-server
    pip install mcp aiofiles
    ```

3.  **Copy the server**:

      - Place `mcp_latex_server.py` in `C:\Users\username\Documents\MCP\latex-server\`

4.  **Configure Claude Desktop**:

      - Edit `C:\Users\username\AppData\Roaming\Claude\claude_desktop_config.json`
      - Add:
        ```json
        {
          "mcpServers": {
            "latex-server": {
              "command": "python",
              "args": [
                "C:\\Users\\username\\Documents\\MCP\\latex-server\\mcp_latex_server.py",
                "--workspace",
                "C:\\Users\\username\\Documents\\LaTeX"
              ]
            }
          }
        }
        ```

5.  **Restart Claude Desktop**

## ✅ Verification

### Quick test in Claude Desktop

Type into Claude:

```
"Create a test.tex file with an article template"
```

If it works, Claude will create `C:\Users\username\Documents\LaTeX\test.tex`

### Command line test

```cmd
cd C:\Users\username\Documents\MCP\latex-server
python mcp_latex_server.py --workspace C:\Users\username\Documents\LaTeX
```

## 📂 Final Structure

```
C:\Users\username\
├── Documents\
│   ├── MCP\
│   │   └── latex-server\
│   │       ├── mcp_latex_server.py      # Main server
│   │       └── README.md                 # This file
│   │
│   └── LaTeX\                           # Your projects
│       ├── Articles\
│       ├── Presentations\
│       └── (your .tex files)
│
└── AppData\
    └── Roaming\
        └── Claude\
            └── claude_desktop_config.json  # Configuration
```

## 🎯 Daily Usage

### Essential commands in Claude

| Action | Command in Claude |
|---|---|
| Create a document | `"Create article.tex with article template"` |
| Read a file | `"Read my thesis.tex file"` |
| Compile | `"Compile main.tex with pdflatex"` |
| Validate | `"Check the syntax of document.tex"` |
| Organize | `"Organize my LaTeX files"` |
| Clean up | `"Clean up auxiliary files"` |
| Change directory | `"Change the working directory to ..."` |

### Recommended Workflows

**New article:**

1.  `"Create an article on AI with mathematical support"`
2.  `"Compile the article"`

**Existing project:**

1.  Copy your project into `C:\Users\username\Documents\LaTeX\my-project\`
2.  `"List the files in my-project"`
3.  `"Compile my-project/main.tex"`

## 🔧 Troubleshooting

### The server does not load

  - Verify that Claude Desktop has been properly closed and restarted
  - Check the JSON config file (be careful with commas and quotes)

### "python not recognized" error

  - Add Python to the system PATH
  - Or use the full path: `"command": "C:\\Python312\\python.exe"`
  - If the error persists, opt for a virtual environment and add the PATH to the JSON config

### LaTeX compilation error

  - Check that MiKTeX or TeX Live is installed
  - Test `pdflatex --version` in cmd

## 📞 Support

  - Logs: In Claude Desktop, Ctrl+Shift+I → Console
  - Test: `mcp_latex_server.py` in the server folder
  - Debug: Add `"--log-level", "DEBUG"` in the args of the JSON config

-----

*MCP LaTeX Server v1.0.0* 
*Server path: C:\\Users\\username\\Documents\\MCP\\latex-server* *LaTeX Workspace: C:\\Users\\username\\Documents\\LaTeX*
