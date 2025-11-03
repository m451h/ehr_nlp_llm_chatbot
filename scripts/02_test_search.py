"""
Simple Search Test
Quick test to verify search is working
"""
import sys
sys.path.insert(0, '.')

from src.search.search_engine import SearchEngine, ChatbotSearchHandler


def main():
    print("\n" + "="*60)
    print("SEARCH ENGINE QUICK TEST")
    print("="*60 + "\n")
    
    # Initialize
    print("🔄 Initializing search engine...")
    engine = SearchEngine()
    handler = ChatbotSearchHandler()
    
    # Show stats
    stats = engine.get_stats()
    print(f"\n📊 Engine Stats:")
    print(f"   Items loaded: {stats['total_items']}")
    print(f"   Confidence thresholds: High ≥{stats['high_confidence_threshold']}, Medium ≥{stats['medium_confidence_threshold']}")
    
    if stats['total_items'] == 0:
        print("\n❌ No data in vector database!")
        print("   Run: python scripts/01_build_index.py build")
        return
    
    # Test queries
    test_queries = [
        "چه غذاهایی برای دیابت خوبه؟",
        "علائم دیابت چیه؟",
        "دارو باید بخورم؟"
    ]
    
    print(f"\n{'='*60}")
    print("Running Test Queries")
    print("="*60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'-'*60}")
        print(f"Test {i}/3")
        print(f"{'-'*60}")
        print(f"🔍 Query: {query}")
        
        # Search
        results = engine.search(query, top_k=3)
        
        if results:
            best = results[0]
            print(f"\n✅ Found {len(results)} results")
            print(f"\n📊 Best Match:")
            print(f"   Confidence: {best['confidence_level'].upper()} ({best['similarity']:.3f})")
            print(f"   Condition: {best['metadata'].get('condition_name', 'N/A')}")
            print(f"   Topic: {best['metadata'].get('topic', 'N/A')}")
            print(f"   Question: {best['metadata'].get('question', 'N/A')}")
            print(f"   Answer: {best['metadata'].get('answer', 'N/A')[:100]}...")
        else:
            print(f"\n❌ No results found")
    
    # Test chatbot handler
    print(f"\n{'='*60}")
    print("Testing Chatbot Handler")
    print("="*60)
    
    query = "چه غذاهایی خوبه؟"
    condition_id = "cond_type_2_diabetes"
    
    print(f"\n🔍 Query: {query}")
    print(f"   Condition: {condition_id}")
    
    response = handler.handle_user_query(query, condition_id)
    
    print(f"\n📊 Response Type: {response['response_type'].upper()}")
    
    if response['response_type'] == 'direct_answer':
        print(f"   ✅ Direct answer (high confidence)")
        print(f"   Answer: {response['answer'][:150]}...")
    elif response['response_type'] == 'clarification':
        print(f"   ⚠️  Needs clarification (medium confidence)")
        print(f"   Message: {response['message']}")
    elif response['response_type'] == 'llm_fallback':
        print(f"   🤖 Needs LLM fallback (low confidence)")
    elif response['response_type'] == 'condition_mismatch':
        print(f"   ⚠️  Condition mismatch detected")
        print(f"   {response['message']}")
    
    print(f"\n{'='*60}")
    print("✅ ALL TESTS COMPLETED")
    print("="*60)



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()