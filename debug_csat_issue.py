#!/usr/bin/env python3
"""
Debug script to diagnose CSAT product matching issue.
Run this to see what evidence is being collected and used.
"""

from api.services.chat_service import answer_question

question = "Which products have the lowest CSAT and what are customers actually saying?"

print("\n" + "="*80)
print("RUNNING DEBUG TEST")
print("="*80)
print(f"Question: {question}\n")

result = answer_question(question, debug=True)

# Print what tools were called and what evidence was collected
print("\n" + "="*80)
print("TOOL USAGE")
print("="*80)
print(f"Route: {result['route']}")
print(f"Total evidence items: {len(result['debug']['raw_evidence'])}")

print("\n" + "="*80)
print("SQL RESULTS (should be products 473, 246, 102 - lowest CSAT)")
print("="*80)
for idx, item in enumerate(result['debug']['raw_evidence']):
    if item['tool'] == 'run_sql_query':
        print(f"SQL Query #{idx+1}: Got {len(item['result'])} rows")
        for i, row in enumerate(item['result'][:5], start=1):
            product_name = row.get('product_name', 'N/A')
            product_id = row.get('product_id', 'N/A')
            csat = row.get('avg_csat_score', 'N/A')
            print(f"  Row {i}: {product_name} (ID: {product_id}) - CSAT: {csat}")

print("\n" + "="*80)
print("VECTOR SEARCH RESULTS (should ONLY have 473, 246, 102)")
print("="*80)
for idx, item in enumerate(result['debug']['raw_evidence']):
    if item['tool'] == 'run_vector_search':
        print(f"Vector Search #{idx+1}: Got {len(item['result'])} matches")
        for i, match in enumerate(item['result'][:5], start=1):
            product_name = match.get('product_name', 'N/A')
            product_id = match.get('product_id', 'N/A')
            text = match.get('text', '')[:60]
            print(f"  Match {i}: {product_name} (ID: {product_id})")
            print(f"    Text: {text}...")

print("\n" + "="*80)
print("FINAL ANSWER (FIRST 800 CHARS)")
print("="*80)
print(result['answer'][:800])

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

# Analyze the issue
sql_product_ids = set()
vector_product_ids = set()

for item in result['debug']['raw_evidence']:
    if item['tool'] == 'run_sql_query':
        for row in item['result']:
            pid = row.get('product_id')
            if pid:
                sql_product_ids.add(str(pid))
    elif item['tool'] == 'run_vector_search':
        for match in item['result']:
            pid = match.get('product_id')
            if pid:
                vector_product_ids.add(str(pid))

print(f"\nSQL product IDs found: {sorted(sql_product_ids)}")
print(f"Vector product IDs found: {sorted(vector_product_ids)}")

if sql_product_ids & vector_product_ids:
    print(f"\n✅ OVERLAP: {sql_product_ids & vector_product_ids}")
else:
    print(f"\n🔴 NO OVERLAP - This is the problem!")
    print(f"   SQL has: {sql_product_ids}")
    print(f"   Vector has: {vector_product_ids}")
    print(f"   These don't match at all!")

print("\n" + "="*80)
