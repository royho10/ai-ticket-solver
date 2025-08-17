# Multi-MCP Server Architecture Documentation

## 🏗️ **Architecture Overview**

The restructured codebase now supports multiple MCP servers with a clean, scalable architecture:

```
User Query → MultiMCPAgent → GenericMCPClient → Server-Specific Adapters → MCP Servers
```

### **Key Components**

1. **`GenericMCPClient`** - Core MCP client that manages multiple server connections
2. **`BaseMCPServerAdapter`** - Abstract base class for server-specific functionality  
3. **`AtlassianMCPAdapter`** - Atlassian-specific implementation (Jira & Confluence)
4. **`MultiMCPAgent`** - Main agent that orchestrates everything
5. **`ClaudeJiraAgent`** - Backward compatibility wrapper

## 🎯 **Generic vs Server-Specific Methods**

### **Generic Methods (work with any MCP server)**

#### In `GenericMCPClient`:
- `register_mcp_server()` - Register any MCP server adapter
- `initialize_all_connections()` - Connect to all registered servers
- `execute_multi_server_query()` - Execute query across relevant servers
- `_format_all_capabilities()` - Format capabilities from all servers
- `_determine_relevant_servers()` - Find servers that can handle query

#### In `BaseMCPServerAdapter`:
- `initialize_connection()` - Generic connection initialization
- `discover_capabilities()` - Generic capability discovery (tools, resources)
- `format_capabilities_summary()` - Generic capability formatting

### **Server-Specific Methods (Atlassian-specific)**

#### In `AtlassianMCPAdapter`:
- `_is_create_issue_intent()` - Recognize Jira issue creation
- `_is_my_issues_intent()` - Recognize "my issues" queries
- `_extract_jira_issue_keys()` - Extract Jira issue keys (e.g., KAN-7)
- `_execute_jira_search()` - Execute JQL searches
- `_get_atlassian_cloud_id()` - Get Atlassian cloud ID for API routing
- `_parse_atlassian_create_issue_request()` - Parse create issue parameters

## 🔧 **Adding New MCP Servers**

### **Step 1: Create Server Adapter**

```python
from src.mcp_client.base_client import BaseMCPServerAdapter, MCPServerConfig, MCPTransportType

class MyCustomMCPAdapter(BaseMCPServerAdapter):
    def __init__(self, verbose: bool = True):
        config = MCPServerConfig(
            name="MyService",
            transport_type=MCPTransportType.HTTP_SSE,  # or STDIO
            url="https://my-mcp-server.com/v1/sse"
        )
        super().__init__(config, verbose)
    
    async def initialize_connection(self) -> bool:
        # Custom initialization logic
        self._server_params = self.config.to_server_params()
        return True
    
    def parse_query_intent(self, query: str) -> List[tuple]:
        # Parse user queries for your service
        if "my custom action" in query.lower():
            return [("myCustomTool", query)]
        return []
    
    async def execute_server_specific_tool(self, session, tool_name, parameters, **kwargs):
        # Execute your service-specific tools
        if tool_name == "myCustomTool":
            result = await session.call_tool(tool_name, {"input": parameters})
            return self._extract_tool_result_content(result)
```

### **Step 2: Register with Agent**

```python
from src.mcp_client import MultiMCPAgent
from my_custom_adapter import MyCustomMCPAdapter

# Create agent
agent = MultiMCPAgent(enable_atlassian=True)

# Add your custom server
custom_adapter = MyCustomMCPAdapter()
agent.add_mcp_server_adapter(custom_adapter)

# Use normally
response = await agent.chat("perform my custom action")
```

## 📋 **Method Naming Convention**

### **Generic Methods** (work with any MCP server):
- `initialize_connection()` - Generic connection setup
- `discover_capabilities()` - Generic capability discovery
- `execute_multi_server_query()` - Cross-server query execution
- `parse_query_intent()` - Generic query parsing interface

### **Server-Specific Methods** (contain server name):
- `_execute_jira_search()` - Jira-specific search
- `_get_atlassian_cloud_id()` - Atlassian-specific cloud ID
- `_parse_atlassian_create_issue_request()` - Atlassian issue creation
- `_execute_github_repository()` - GitHub-specific repository access

### **Private Helper Methods** (start with underscore):
- `_extract_tool_result_content()` - Extract MCP tool results
- `_is_create_issue_intent()` - Check for issue creation intent
- `_determine_relevant_servers()` - Find servers for query

## 🚀 **Usage Examples**

### **Basic Usage (Backward Compatible)**
```python
from src.mcp_client import create_claude_jira_agent

# Works exactly like before
agent = create_claude_jira_agent()
response = agent.run_sync("what jira issues i have?")
```

### **Multi-Server Usage**
```python
from src.mcp_client import create_multi_mcp_agent

# Enable multiple servers
agent = create_multi_mcp_agent(
    enable_atlassian=True,
    # Future: enable_github=True, enable_slack=True
)

# Queries route to appropriate servers automatically
jira_response = await agent.chat("what jira issues i have?")
tools_response = await agent.chat("what tools do you have?")
```

### **Custom Server Integration**
```python
from src.mcp_client import MultiMCPAgent
from my_adapters import GitHubAdapter, SlackAdapter

agent = MultiMCPAgent()

# Add multiple custom servers
agent.add_mcp_server_adapter(GitHubAdapter())
agent.add_mcp_server_adapter(SlackAdapter())

# Query spans multiple services
response = await agent.chat("create github issue and notify slack channel")
```

## 🎯 **Benefits of New Architecture**

### **1. Scalability**
- ✅ Easy to add new MCP servers
- ✅ Clean separation of concerns
- ✅ No coupling between server implementations

### **2. Maintainability**
- ✅ Generic methods are reusable
- ✅ Server-specific logic is isolated
- ✅ Clear naming conventions

### **3. Extensibility**
- ✅ Plugin-style architecture for adapters
- ✅ Standardized adapter interface
- ✅ Cross-server query capabilities

### **4. Backward Compatibility**
- ✅ Existing code continues to work
- ✅ Gradual migration path
- ✅ No breaking changes

## 🔧 **Future MCP Servers to Add**

With this architecture, you can easily add:

1. **GitHub MCP Server**
   - Repository management
   - Issue tracking
   - Pull request workflows

2. **Slack MCP Server**
   - Channel management
   - Message sending
   - Team coordination

3. **Database MCP Servers**
   - PostgreSQL, MySQL queries
   - Schema introspection
   - Data analysis

4. **File System MCP Server**
   - Local file operations
   - Directory navigation
   - File content analysis

5. **API Integration Servers**
   - REST API interactions
   - OAuth authentication
   - Custom service integrations

## 📊 **Architecture Comparison**

| Aspect | Old Architecture | New Architecture |
|--------|-----------------|------------------|
| **Server Support** | Atlassian only | Multiple MCP servers |
| **Extensibility** | Hard-coded logic | Plugin-based adapters |
| **Method Naming** | Mixed concerns | Clear generic vs specific |
| **Code Reuse** | Limited | High reusability |
| **Testing** | Monolithic | Modular testing |
| **Maintenance** | Complex | Clean separation |

The new architecture positions your codebase to scale with the growing MCP ecosystem! 🚀
