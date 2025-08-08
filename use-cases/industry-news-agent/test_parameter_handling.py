#!/usr/bin/env python3
"""
Simple test to verify tool input parameter handling without dependencies.
"""
import sys
from pathlib import Path


def mock_tool_run_method(*args, **kwargs):
    """Mock version of the fixed _run method to test parameter handling."""
    try:
        # This is the exact logic from our fixed AIContentAnalysisTool._run
        articles = None
        analysis_config = None
        
        # Case 1: Arguments passed as positional args
        if len(args) == 1 and isinstance(args[0], list):
            articles = args[0]
            analysis_config = kwargs.get('analysis_config')
        elif len(args) == 1 and not isinstance(args[0], list):
            # Single article passed
            articles = [args[0]]
            analysis_config = kwargs.get('analysis_config')
        elif len(args) == 2:
            articles = args[0]
            analysis_config = args[1]
        elif 'articles' in kwargs:
            # Arguments passed as keyword args
            articles = kwargs['articles']
            analysis_config = kwargs.get('analysis_config')
        else:
            # No valid arguments found
            raise ValueError(f"Invalid arguments: args={args}, kwargs={kwargs}")
        
        # Ensure articles is a list
        if not isinstance(articles, list):
            articles = [articles]
        
        return {
            "success": True,
            "articles_count": len(articles),
            "articles_type": type(articles),
            "analysis_config": analysis_config,
            "args_received": args,
            "kwargs_received": kwargs
        }
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error in mock _run: {e}")
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")
        raise e


def test_parameter_handling():
    """Test various parameter passing scenarios."""
    print("🧪 Testing parameter handling logic...")
    
    # Create mock article objects
    class MockArticle:
        def __init__(self, title):
            self.title = title
    
    test_articles = [
        MockArticle("Article 1"),
        MockArticle("Article 2")
    ]
    
    # Test scenarios that mirror the real LangChain usage
    test_cases = [
        {
            "name": "List as first positional arg",
            "args": [test_articles],
            "kwargs": {},
            "expected_articles_count": 2
        },
        {
            "name": "Single article as first positional arg", 
            "args": [test_articles[0]],
            "kwargs": {},
            "expected_articles_count": 1
        },
        {
            "name": "List and config as positional args",
            "args": [test_articles, {"max_tokens": 1000}],
            "kwargs": {},
            "expected_articles_count": 2
        },
        {
            "name": "Articles as keyword arg",
            "args": [],
            "kwargs": {"articles": test_articles},
            "expected_articles_count": 2
        },
        {
            "name": "Articles and config as keyword args",
            "args": [],
            "kwargs": {"articles": test_articles, "analysis_config": {"max_tokens": 500}},
            "expected_articles_count": 2
        },
        {
            "name": "Mixed positional and keyword",
            "args": [test_articles],
            "kwargs": {"analysis_config": {"temperature": 0.5}},
            "expected_articles_count": 2
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        try:
            result = mock_tool_run_method(
                *test_case['args'], 
                **test_case['kwargs']
            )
            
            if result['success'] and result['articles_count'] == test_case['expected_articles_count']:
                print(f"  ✅ Success: {result['articles_count']} articles processed")
                print(f"     Articles type: {result['articles_type']}")
                print(f"     Config: {result['analysis_config']}")
                passed += 1
            else:
                print(f"  ❌ Failed: Expected {test_case['expected_articles_count']} articles, got {result['articles_count']}")
                failed += 1
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  🎯 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    return failed == 0


if __name__ == "__main__":
    success = test_parameter_handling()
    if success:
        print("\n🎉 All parameter handling tests passed!")
        print("The tool input type issue should be resolved.")
    else:
        print("\n⚠️  Some tests failed. Further investigation needed.")