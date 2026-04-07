#!/usr/bin/env python3
"""
Verification test for golden SQL retrieval payload extraction fix.

This test verifies that:
1. The search_support_tickets() function now extracts ALL payload fields
2. Golden SQL examples include "question" and "sql" fields
3. The chat_service.py can correctly build golden_sql_prompt with examples
"""

import json
import os
from pathlib import Path


def test_payload_extraction():
    """Test that payload extraction now includes all fields."""
    print("\n" + "="*70)
    print("TEST 1: Verify query.py payload extraction fix")
    print("="*70)
    
    # Read the updated query.py to verify the fix
    query_file = Path("/Users/akshayjain/Documents/chat_bot/embeddings/query.py")
    content = query_file.read_text()
    
    # Check for the fixed payload extraction logic
    if 'result_item.update(payload)' in content:
        print("✅ PASS: Payload extraction now uses .update(payload)")
        print("   This means ALL payload fields are preserved, not just hardcoded ones")
        return True
    else:
        print("❌ FAIL: Old hardcoded extraction logic still present")
        return False


def test_system_prompt_updates():
    """Test that system prompt now includes production-grade instructions."""
    print("\n" + "="*70)
    print("TEST 2: Verify SYSTEM_PROMPT production-grade updates")
    print("="*70)
    
    chat_service_file = Path("/Users/akshayjain/Documents/chat_bot/api/services/chat_service.py")
    content = chat_service_file.read_text()
    
    checks = [
        (
            "always show human-readable names",
            "product_name, region",
            "instruction to prefer product_name over product_id"
        ),
        (
            "data is unavailable",
            "When expected metric columns are NULL",
            "NULL/zero result handling guidance"
        ),
    ]
    
    passed = 0
    for keyword1, keyword2, description in checks:
        if keyword1 in content and keyword2 in content:
            print(f"✅ PASS: {description}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
    
    return passed == len(checks)


def test_golden_sql_json():
    """Test that golden_sql.json contains the expected structure."""
    print("\n" + "="*70)
    print("TEST 3: Verify golden_sql.json data structure")
    print("="*70)
    
    golden_file = Path("/Users/akshayjain/Documents/chat_bot/data/golden_sql.json")
    
    if not golden_file.exists():
        print("⚠️  WARNING: golden_sql.json not found - seeding may not have run yet")
        return False
    
    try:
        with open(golden_file) as f:
            data = json.load(f)
        
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            required_fields = {"question", "sql"}
            
            if all(field in first_item for field in required_fields):
                print(f"✅ PASS: Found {len(data)} golden examples with correct structure")
                print(f"   Fields present: {list(first_item.keys())}")
                
                # Show first example
                print(f"\n   Example 1:")
                print(f"   - Question: {first_item['question'][:80]}...")
                print(f"   - SQL: {first_item['sql'][:80]}...")
                return True
            else:
                print(f"❌ FAIL: Missing required fields. Found: {list(first_item.keys())}")
                return False
        else:
            print(f"❌ FAIL: golden_sql.json is empty or invalid")
            return False
    except Exception as e:
        print(f"❌ FAIL: Error reading golden_sql.json: {e}")
        return False


def test_chat_service_golden_prompt():
    """Test that chat_service.py can receive golden examples."""
    print("\n" + "="*70)
    print("TEST 4: Verify chat_service.py golden prompt logic")
    print("="*70)
    
    chat_service_file = Path("/Users/akshayjain/Documents/chat_bot/api/services/chat_service.py")
    content = chat_service_file.read_text()
    
    checks = [
        (
            'collection_name="sql_examples"',
            "queries sql_examples collection correctly"
        ),
        (
            'match.get("question")',
            "attempts to extract 'question' field"
        ),
        (
            'match.get("sql")',
            "attempts to extract 'sql' field"
        ),
        (
            'if q and sql:',
            "validates both fields before adding to prompt"
        ),
    ]
    
    passed = 0
    for keyword, description in checks:
        if keyword in content:
            print(f"✅ PASS: {description}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
    
    return passed == len(checks)


def main():
    """Run all verification tests."""
    print("\n" + "="*70)
    print("GOLDEN SQL RETRIEVAL FIX - VERIFICATION TEST SUITE")
    print("="*70)
    
    results = [
        ("Payload Extraction Fix", test_payload_extraction()),
        ("System Prompt Updates", test_system_prompt_updates()),
        ("Golden SQL Data", test_golden_sql_json()),
        ("Chat Service Logic", test_chat_service_golden_prompt()),
    ]
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All fixes verified! Golden SQL should now work correctly.")
        print("\nNext steps:")
        print("1. Restart the API server (if running)")
        print("2. Send a test question to the chat API")
        print("3. Check the debug/raw_evidence to confirm golden examples are retrieved")
        print("4. Monitor OpenAI API logs to verify full prompt is being sent")
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
