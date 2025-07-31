#!/usr/bin/env python3
"""
Test script to verify the complete Jira agent functionality.
Run this to test that everything is working correctly.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def test_environment():
    """Test that environment variables are properly configured."""
    print("🔧 Testing Environment Configuration")
    print("=" * 50)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    jira_base = os.getenv("JIRA_API_BASE")
    jira_token = os.getenv("JIRA_API_TOKEN")
    jira_email = os.getenv("JIRA_EMAIL")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not all([jira_base, jira_token, jira_email, openai_key]):
        print("❌ Missing environment variables!")
        print("Please check your .env file contains:")
        print("- JIRA_API_BASE")
        print("- JIRA_API_TOKEN") 
        print("- JIRA_EMAIL")
        print("- OPENAI_API_KEY")
        return False
    
    print("✅ Environment variables configured")
    return True

def test_jira_connection():
    """Test basic Jira API connection."""
    print("\n🌐 Testing Jira Connection")
    print("=" * 50)
    
    try:
        from jira.service import JiraService
        service = JiraService()
        
        # Test with a simple API call
        import requests
        response = requests.get(f"{service.base_url}/myself", headers=service.headers)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Connected to Jira as: {user_info.get('displayName')}")
            return True
        else:
            print(f"❌ Jira connection failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Jira connection error: {e}")
        return False

def test_jira_tools():
    """Test Jira tools functionality."""
    print("\n🔧 Testing Jira Tools")
    print("=" * 50)
    
    try:
        from jira.tools import get_my_jira_issues
        
        # Test getting user's issues
        result = get_my_jira_issues()
        
        if "Error" in result:
            print(f"❌ Tool error: {result}")
            return False
        else:
            print("✅ Jira tools working")
            print(f"Found issues: {len(result.splitlines()) - 1}")
            return True
            
    except Exception as e:
        print(f"❌ Tools error: {e}")
        return False

def test_agent():
    """Test the complete agent functionality."""
    print("\n🤖 Testing Jira Agent")
    print("=" * 50)
    
    try:
        from jira.agent import JiraAgent
        
        agent = JiraAgent(verbose=False)  # Less verbose for testing
        
        # Test with a simple query
        response = agent.run("How many tickets do I have?")
        
        if "Error" in response:
            print(f"❌ Agent error: {response}")
            return False
        else:
            print("✅ Agent working correctly")
            print(f"Response: {response[:100]}...")
            return True
            
    except Exception as e:
        print(f"❌ Agent error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Jira Agent Test Suite")
    print("=" * 60)
    
    tests = [
        test_environment,
        test_jira_connection, 
        test_jira_tools,
        test_agent
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Test Results")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed}/{len(tests)} ({passed/len(tests)*100:.1f}%)")
    
    if failed == 0:
        print("\n🎉 All tests passed! Your Jira agent is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    main()
