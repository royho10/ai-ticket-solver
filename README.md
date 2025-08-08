# 🤖 Claude Sonnet 4 + Official Atlassian MCP Jira Agent

A modern AI-powered Jira ticket management system using **Claude Sonnet 4** and the **Official Atlassian MCP Server** for secure, standardized AI-to-system integration.

## ⚡ **LATEST**: Official Atlassian MCP Architecture

This project uses the **official Atlassian MCP server** for seamless integration:
- **🧠 Claude Sonnet 4** (Anthropic's latest model) for natural language understanding
- **🏢 Official Atlassian MCP Server** - no custom server required!
- **🔌 Model Context Protocol (MCP)** for standardized AI-system integration
- **🔒 OAuth 2.0 Authentication** through official Atlassian APIs
- **⚡ Real-time Access** to 20+ official Jira and Confluence tools

## 🚀 Features

- **🗣️ Natural Language Processing**: Ask questions in plain English about your Jira tickets
- **🏢 Official Atlassian Integration**: Uses official Atlassian MCP server (mcp.atlassian.com)
- **🧠 Claude Sonnet 4**: Latest AI model for superior understanding and responses  
- **🔌 20+ MCP Tools**: Access to official Jira and Confluence tools via MCP
- **🔒 OAuth 2.0 Security**: Secure authentication through Atlassian's official APIs
- **🎯 Smart Query Understanding**: Automatically chooses the right tools for your requests
- **📊 Multiple Query Types**: Get ticket details, search issues, create tickets, add comments, and more

## 📁 Modern Project Structure

```
ticket_solver/
├── src/
│   └── mcp_client/           # 🧠 Claude Sonnet 4 MCP Client
│       ├── __init__.py      
│       └── agent.py         # Main Claude + Official Atlassian MCP agent
├── configs/
│   └── config.yaml          # Configuration settings
├── claude_chat.py           # 🆕 Modern chat interface
├── .env                    # Environment variables (OAuth tokens)
└── requirements.txt        # Dependencies (Claude + MCP)
```

**Key Components:**
- **`src/mcp_client/agent.py`**: Main agent that connects to official Atlassian MCP server
- **`claude_chat.py`**: Interactive chat interface for testing
- **`.env`**: OAuth credentials for Atlassian authentication
- **No custom server needed** - uses `mcp.atlassian.com` directly!

## 🛠️ Setup

### 1. Environment Setup

```bash
# Create virtual environment (if not already created)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies for Claude + Official Atlassian MCP
pip install anthropic "mcp[cli]" python-dotenv requests pydantic
```

### 2. Get API Keys

#### Anthropic API Key (Required for Claude Sonnet 4)
1. Go to [Anthropic Console](https://console.anthropic.com/account/keys)
2. Create a new API key
3. Copy the key (starts with `sk-ant-`)

#### Atlassian OAuth Setup (Required for official MCP server)
1. **IMPORTANT**: You need OAuth authentication for the official Atlassian MCP server
2. The MCP server will guide you through OAuth setup on first connection
3. Your browser will open to complete authentication with Atlassian

### 3. Configuration

Update your `.env` file with the required credentials:

```env
# Claude Sonnet 4 Configuration (Anthropic)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Jira credentials (for reference - OAuth handled by MCP server)
JIRA_BASE_URL=https://your-domain.atlassian.net/rest/api/3
JIRA_EMAIL=your.email@example.com
JIRA_API_TOKEN=your_jira_api_token_here
```

**Note**: The official Atlassian MCP server handles authentication through OAuth, so you don't need to manually configure Jira credentials in most cases.

### 4. Quick Start

#### 🆕 Modern Claude + Official Atlassian MCP Interface

```bash
# Start the modern chat interface
python claude_chat.py
```

The first time you run this, your browser will open for OAuth authentication with Atlassian.

### 5. Test Installation

```bash
# Test the agent functionality
python -c "
import asyncio
from src.mcp_client.agent import ClaudeJiraAgent

async def test():
    agent = ClaudeJiraAgent(verbose=True)
    result = await agent.run('show me my jira tickets')
    print(result)

asyncio.run(test())
"
```

## 📝 Usage

### Basic Usage

```python
import asyncio
from src.mcp_client.agent import ClaudeJiraAgent

async def main():
    # Create agent (connects to official Atlassian MCP server)
    agent = ClaudeJiraAgent()
    
    # Ask natural language questions
    result = await agent.run("show me my jira tickets")
    print(result)
    
    result = await agent.run("what is the status of ticket PROJ-123?")
    print(result)

# Run the async function
asyncio.run(main())
```

### Interactive Chat

```bash
python claude_chat.py
```

## 🔧 Available Queries

The agent can handle various types of natural language queries using official Atlassian tools:

- **"show me my jira tickets"** - Lists all your assigned tickets via `searchJiraIssuesUsingJql`
- **"what tickets do I have?"** - Same as above  
- **"get details for ticket KAN-4"** - Full details via `getJiraIssue`
- **"create a new ticket"** - Creates tickets via `createJiraIssue`
- **"add comment to KAN-1"** - Adds comments via `addCommentToJiraIssue`
- **"what projects can I see?"** - Lists projects via `getVisibleJiraProjects`

### Available Official Tools

The official Atlassian MCP server provides 20+ tools including:

**Jira Tools:**
- `searchJiraIssuesUsingJql` - Search using JQL queries
- `getJiraIssue` - Get specific issue details  
- `createJiraIssue` - Create new issues
- `editJiraIssue` - Edit existing issues
- `addCommentToJiraIssue` - Add comments
- `transitionJiraIssue` - Change issue status
- `getVisibleJiraProjects` - List accessible projects

**Confluence Tools:**
- `getConfluenceSpaces` - List Confluence spaces
- `getConfluencePage` - Get page content
- `createConfluencePage` - Create new pages
- `searchConfluenceUsingCql` - Search Confluence

**General Tools:**
- `atlassianUserInfo` - Get user information
- `getAccessibleAtlassianResources` - List accessible resources

## 🧪 Testing

Test the agent to verify everything is working:

```bash
# Quick test
python -c "
import asyncio
from src.mcp_client.agent import ClaudeJiraAgent

async def test():
    agent = ClaudeJiraAgent(verbose=True)
    print('Testing official Atlassian MCP server...')
    result = await agent.run('show me my visible jira projects')
    print('✅ Test completed!')
    print(result)

asyncio.run(test())
"
```

## 🔐 Security

- **OAuth 2.0**: Secure authentication through official Atlassian APIs
- **No stored tokens**: MCP server handles authentication securely
- **Official server**: Uses `mcp.atlassian.com` - no custom server required
- **Environment isolation**: API keys stored in `.env` file (not committed to git)

## 📚 Architecture

- **Claude Sonnet 4**: Latest Anthropic model for natural language understanding
- **Official Atlassian MCP Server**: Hosted at `mcp.atlassian.com`
- **MCP Protocol**: Standardized AI-to-system integration protocol
- **OAuth 2.0**: Secure authentication flow
- **No Custom Infrastructure**: Leverages official Atlassian services

## 🚦 Getting Help

1. **Authentication Issues**: Ensure OAuth flow completes in browser
2. **Connection Problems**: Check internet connection to `mcp.atlassian.com`
3. **API Issues**: Verify Anthropic API key is valid
4. **Tool Errors**: Check that you have appropriate Jira/Confluence permissions

## � Migration from Custom MCP Server

This project has been fully migrated from a custom MCP server to the **official Atlassian MCP server**. Benefits include:

- ✅ **No maintenance** of custom server code
- ✅ **20+ official tools** instead of custom implementations  
- ✅ **OAuth security** instead of API token management
- ✅ **Automatic updates** when Atlassian adds new features
- ✅ **Production reliability** from Atlassian's infrastructure
