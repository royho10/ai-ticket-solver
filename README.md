# 🤖 Claude Sonnet 4 + MCP Jira Agent

A modern AI-powered Jira ticket management system using **Claude Sonnet 4** and **Model Context Protocol (MCP)** for secure, standardized AI-to-system integration.

## ⚡ **NEW**: Modern MCP Architecture

This project has been **fully modernized** from LangChain to use:
- **🧠 Claude Sonnet 4** (Anthropic's latest model) instead of OpenAI GPT-4
- **🔌 Model Context Protocol (MCP)** for standardized AI-system integration
- **🏗️ Modern Architecture** with separated client/server components
- **🔒 Enhanced Security** through controlled MCP tool access

## 🚀 Features

- **🗣️ Natural Language Processing**: Ask questions in plain English about your Jira tickets
- **⚡ Real-time Jira Integration**: Direct API connection via MCP tools
- **🧠 Claude Sonnet 4**: Latest AI model for superior understanding and responses  
- **🔌 MCP Integration**: Standardized protocol for secure tool access
- **🎯 Smart Query Understanding**: Automatically chooses the right tools for your requests
- **📊 Multiple Query Types**: Get ticket details, search your issues, analyze status, and more

## 📁 Modern Project Structure

```
ticket_solver/
├── src/
│   ├── mcp_client/           # 🧠 Claude Sonnet 4 MCP Client
│   │   ├── __init__.py      
│   │   └── agent.py         # Main Claude + MCP agent
│   ├── mcp_server/          # 🔧 Custom Jira MCP Server  
│   │   └── jira_server.py   # MCP server with Jira tools
│   └── jira/                # 📦 Legacy components (for reference)
│       ├── agent.py         # [LEGACY] LangChain agent
│       ├── service.py       # Jira API service (reused by MCP)
│       ├── tools.py         # [LEGACY] LangChain tools
│       └── models.py        # Pydantic data models
├── configs/
│   ├── config.yaml          # [LEGACY] LangChain config
│   └── mcp_config.yaml      # 🆕 MCP configuration
├── claude_chat.py           # 🆕 Modern chat interface
├── chat.py                  # [LEGACY] Old chat interface  
├── test_agent.py           # Test suite
├── .env                    # Environment variables
└── requirements.txt        # Dependencies (updated for MCP)
```

## 🛠️ Setup

### 1. Environment Setup

```bash
# Create virtual environment (if not already created)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install modern dependencies for Claude + MCP
pip install anthropic "mcp[cli]" python-dotenv requests pydantic
```

### 2. Get API Keys

#### Anthropic API Key (Required for Claude Sonnet 4)
1. Go to [Anthropic Console](https://console.anthropic.com/account/keys)
2. Create a new API key
3. Copy the key (starts with `sk-ant-`)

#### Jira API Token (Required for Jira access)
1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create API token
3. Copy the token

### 3. Configuration

Update your `.env` file with the required credentials:

```env
# Jira Configuration  
JIRA_API_BASE=https://royho10.atlassian.net/rest/api/3
JIRA_API_TOKEN=your_jira_api_token_here
JIRA_EMAIL=royho10@gmail.com

# Claude Sonnet 4 Configuration (Anthropic)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Legacy OpenAI (can be removed after migration)
# OPENAI_API_KEY=your_openai_key
```

### 4. Quick Start

#### 🆕 Modern Claude + MCP Interface

```bash
# Start the modern chat interface
python claude_chat.py
```

#### 📦 Legacy LangChain Interface (for comparison)

```bash
# Start the legacy interface  
python chat.py
```

### 5. Test Installation

```bash
python test_agent.py
```

## 📝 Usage

### Basic Usage

```python
from src.jira.agent import JiraAgent

# Create agent
agent = JiraAgent()

# Ask natural language questions
response = agent.run("show me my jira tickets")
print(response)

response = agent.run("what is the status of ticket PROJ-123?")
print(response)
```

### Run Examples

```bash
python example.py
```

## 🔧 Available Queries

The agent can handle various types of natural language queries:

- **"show me my jira tickets"** - Lists all your assigned/reported tickets
- **"what tickets do I have?"** - Same as above  
- **"get details for ticket KAN-4"** - Full details for a specific ticket
- **"what is the summary of KAN-1?"** - Just the summary of a ticket
- **"tell me about ticket KAN-2"** - Comprehensive information

## 🧪 Testing

Run the test suite to verify everything is working:

```bash
python test_agent.py
```

The test suite checks:
- ✅ Environment configuration
- ✅ Jira API connection  
- ✅ Tool functionality
- ✅ Agent responses

## 🔐 Security

- API tokens are stored in `.env` file (not committed to git)
- `.gitignore` configured to exclude sensitive files
- Use Jira API tokens instead of passwords

## 📚 Architecture

- **LangChain Framework**: For AI agent orchestration
- **OpenAI GPT**: For natural language understanding
- **Jira REST API**: For ticket data retrieval
- **Pydantic**: For data validation and models
- **Domain-Driven Design**: Clean separation of concerns

## 🚦 Getting Help

1. Run `python test_agent.py` to diagnose issues
2. Check your `.env` file configuration
3. Verify Jira API token permissions
4. Ensure OpenAI API key is valid
