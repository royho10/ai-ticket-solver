# Jira Agent - AI-Powered Jira Ticket Management

A LangChain-based AI agent that can interact with Jira using natural language queries.

## 🚀 Features

- **Natural Language Processing**: Ask questions in plain English about your Jira tickets
- **Real-time Jira Integration**: Direct API connection to your Jira instance  
- **Smart Query Understanding**: Automatically chooses the right tools for your requests
- **Multiple Query Types**: Get ticket details, search your issues, and more

## 📁 Project Structure

```
ticket_solver/
├── src/jira/                 # Main Jira agent package
│   ├── __init__.py          # Package initialization
│   ├── agent.py             # Main LangChain agent implementation
│   ├── service.py           # Jira API service layer
│   ├── tools.py             # LangChain tools for Jira operations
│   └── models.py            # Pydantic data models
├── tests/                   # Test suite
│   └── jira/               # Jira-specific tests
├── configs/                 # Configuration files
├── scripts/                 # Utility scripts
├── .env                    # Environment variables (create from .env.example)
├── .env.example            # Template for environment variables
├── requirements.txt        # Python dependencies
├── test_agent.py           # Comprehensive test suite
└── example.py              # Usage examples
```

## 🛠️ Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your details:
```env
# Jira Configuration
JIRA_API_BASE=https://yourcompany.atlassian.net/rest/api/3
JIRA_API_TOKEN=your_jira_api_token
JIRA_EMAIL=your.email@company.com

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
```

### 3. Test Installation

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
