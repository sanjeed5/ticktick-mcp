# TickTick MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for TickTick that enables interacting with your TickTick task management system directly through Claude and other MCP clients.

## Features

- 📋 View all your TickTick projects and tasks
- ✏️ Create new projects and tasks through natural language
- 🔄 Update existing task details (title, content, dates, priority)
- ✅ Mark tasks as complete
- 🗑️ Delete tasks and projects
- 🔄 Full integration with TickTick's open API
- 🔌 Seamless integration with Claude and other MCP clients

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver
- TickTick account with API access
- TickTick API credentials (Client ID, Client Secret, Access Token)

## Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/jacepark12/ticktick-mcp.git
   cd ticktick-mcp
   ```

2. **Install with uv**:
   ```bash
   # Install uv if you don't have it already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create a virtual environment
   uv venv

   # Activate the virtual environment
   # On macOS/Linux:
   source .venv/bin/activate
   # On Windows:
   .venv\Scripts\activate

   # Install the package
   uv pip install -e .
   ```

3. **Authenticate with TickTick**:
   ```bash
   # Run the authentication flow
   uv run -m ticktick_mcp.cli auth
   ```

   This will:
   - Ask for your TickTick Client ID and Client Secret
   - Open a browser window for you to log in to TickTick
   - Automatically save your access tokens to a `.env` file

4. **Test your configuration**:
   ```bash
   uv run test_server.py
   ```
   This will verify that your TickTick credentials are working correctly.

## Authentication with TickTick

This server uses OAuth2 to authenticate with TickTick. The setup process is straightforward:

1. Register your application at the [TickTick Developer Center](https://developer.ticktick.com/manage)
   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. Run the authentication command:
   ```bash
   uv run -m ticktick_mcp.cli auth
   ```

3. Follow the prompts to enter your Client ID and Client Secret

4. A browser window will open for you to authorize the application with your TickTick account

5. After authorizing, you'll be redirected back to the application, and your access tokens will be automatically saved to the `.env` file

The server handles token refresh automatically, so you won't need to reauthenticate unless you revoke access or delete your `.env` file.

## Authentication with Dida365

[滴答清单 - Dida365](https://dida365.com/home) is China version of TickTick, and the authentication process is similar to TickTick. Follow these steps to set up Dida365 authentication:

1. Register your application at the [Dida365 Developer Center](https://developer.dida365.com/manage)
   - Set the redirect URI to `http://localhost:8000/callback`
   - Note your Client ID and Client Secret

2. Add environment variables to your `.env` file:
   ```env
   TICKTICK_BASE_URL='https://api.dida365.com/open/v1'
   TICKTICK_AUTH_URL='https://dida365.com/oauth/authorize'
   TICKTICK_TOKEN_URL='https://dida365.com/oauth/token'
   ```

3. Follow the same authentication steps as for TickTick

## Usage with Claude for Desktop

1. Install [Claude for Desktop](https://claude.ai/download)
2. Edit your Claude for Desktop configuration file:

   **macOS**:
   ```bash
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   **Windows**:
   ```bash
   notepad %APPDATA%\Claude\claude_desktop_config.json
   ```

3. Add the TickTick MCP server configuration, using absolute paths:
   ```json
   {
      "mcpServers": {
         "ticktick": {
            "command": "<absolute path to uv>",
            "args": ["run", "--directory", "<absolute path to ticktick-mcp directory>", "-m", "ticktick_mcp.cli", "run"]
         }
      }
   }
   ```

4. Restart Claude for Desktop

Once connected, you'll see the TickTick MCP server tools available in Claude, indicated by the 🔨 (tools) icon.

## Available MCP Tools

The TickTick MCP server provides **12 tools** for managing your tasks and projects:

### Projects

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_projects` | List all your TickTick projects | None |
| `get_project` | Get details about a specific project | `project_id` |
| `create_project` | Create a new project | `name`, `color` (optional), `view_mode` (optional) |
| `delete_project` | Delete a project | `project_id` |

### Tasks

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_project_tasks` | List all tasks in a project | `project_id` |
| `get_task` | Get details about a specific task | `project_id`, `task_id` |
| `create_task` | Create a new task | `title`, `project_id`, `content` (optional), `start_date` (optional), `due_date` (optional), `priority` (optional) |
| `update_task` | Update an existing task | `task_id`, `project_id`, `title` (optional), `content` (optional), `start_date` (optional), `due_date` (optional), `priority` (optional) |
| `complete_task` | Mark a task as complete | `project_id`, `task_id` |
| `delete_task` | Delete a task | `project_id`, `task_id` |
| `create_subtask` | Create a subtask for a parent task | `subtask_title`, `parent_task_id`, `project_id`, `content` (optional), `priority` (optional) |

### Task Filtering

| Tool | Description | Parameters |
|------|-------------|------------|
| `filter_tasks` | Filter tasks with flexible criteria | `date_filter` (optional), `priority` (optional), `search_term` (optional), `project_id` (optional) |

**Filter Parameters:**
- `date_filter`: `"all"`, `"today"`, `"tomorrow"`, `"overdue"`, `"this_week"`, or `"next_7_days"` (default: `"all"`)
- `priority`: `0` (None), `1` (Low), `3` (Medium), or `5` (High) (default: `None` = any priority)
- `search_term`: Text to search in task titles, content, or subtasks (case-insensitive)
- `project_id`: Filter to a specific project or `"inbox"` (default: `None` = all projects)

**Examples:**
- `filter_tasks(date_filter="overdue")` - All overdue tasks
- `filter_tasks(priority=5)` - All high priority tasks
- `filter_tasks(date_filter="today", priority=5)` - High priority tasks due today
- `filter_tasks(search_term="client meeting")` - Search for tasks about client meetings
- `filter_tasks(project_id="inbox", date_filter="this_week")` - Inbox tasks due this week
- `filter_tasks(priority=3, search_term="review")` - Medium priority tasks containing "review"

### Special Project IDs

**Inbox**: You can use `"inbox"` as a project ID to access your TickTick inbox tasks. For example:
- `get_project_tasks("inbox")` - Get all tasks in your inbox
- `create_task("My Task", "inbox")` - Create a task in your inbox

## MCP Prompts

The server also provides **2 prompts** for workflow helpers:

| Prompt | Description | Usage |
|--------|-------------|-------|
| `/engaged` | Show tasks that need immediate attention (GTD "Engaged" workflow) | High priority tasks, overdue tasks, and tasks due today |
| `/next` | Show tasks for next actions (GTD "Next" workflow) | Medium priority tasks and tasks due tomorrow |

These prompts are user-driven and can be invoked in Cursor or other MCP clients that support prompts. They use the `filter_tasks` tool internally to provide GTD workflow assistance.

## Example Prompts for Claude

Here are some example prompts to use with Claude after connecting the TickTick MCP server:

### General

- "Show me all my TickTick projects"
- "Create a new task called 'Finish MCP server documentation' in my work project with high priority"
- "List all tasks in my personal project"
- "Mark the task 'Buy groceries' as complete"
- "Create a new project called 'Vacation Planning' with a blue color"
- "When is my next deadline in TickTick?"

### Task Filtering Queries

- "Show me all overdue tasks" → `filter_tasks(date_filter="overdue")`
- "What tasks do I have due today?" → `filter_tasks(date_filter="today")`
- "Show me all tasks due this week" → `filter_tasks(date_filter="this_week")`
- "Show me all my high priority tasks" → `filter_tasks(priority=5)`
- "Search for tasks about 'project alpha'" → `filter_tasks(search_term="project alpha")`
- "Show me high priority tasks due today in my inbox" → `filter_tasks(project_id="inbox", date_filter="today", priority=5)`

### GTD Workflow

Following David Allen's "Getting Things Done" framework:

- **Engaged tasks**: Use the `/engaged` prompt or `filter_tasks` with multiple criteria
  - "Show me my engaged tasks" → Use `/engaged` prompt
  - "What needs my immediate attention?" → `filter_tasks(date_filter="overdue")` or `filter_tasks(priority=5)`

- **Next actions**: Use the `/next` prompt
  - "Show me my next actions" → Use `/next` prompt
  - "What should I work on tomorrow?" → `filter_tasks(date_filter="tomorrow")`

## Development

### Project Structure

```
ticktick-mcp/
├── .env.template          # Template for environment variables
├── README.md              # Project documentation
├── requirements.txt       # Project dependencies
├── setup.py               # Package setup file
├── test_server.py         # Test script for server configuration
└── ticktick_mcp/          # Main package
    ├── __init__.py        # Package initialization
    ├── authenticate.py    # OAuth authentication utility
    ├── cli.py             # Command-line interface
    └── src/               # Source code
        ├── __init__.py    # Module initialization
        ├── auth.py        # OAuth authentication implementation
        ├── server.py      # MCP server implementation
        └── ticktick_client.py  # TickTick API client
```

### Authentication Flow

The project implements a complete OAuth 2.0 flow for TickTick:

1. **Initial Setup**: User provides their TickTick API Client ID and Secret
2. **Browser Authorization**: User is redirected to TickTick to grant access
3. **Token Reception**: A local server receives the OAuth callback with the authorization code
4. **Token Exchange**: The code is exchanged for access and refresh tokens
5. **Token Storage**: Tokens are securely stored in the local `.env` file
6. **Token Refresh**: The client automatically refreshes the access token when it expires

This simplifies the user experience by handling the entire OAuth flow programmatically.

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
