"""
Test Search Engine
Run after building the index
"""
import sys
sys.path.insert(0, '.')

from src.search.search_engine import SearchEngine, ChatbotSearchHandler


def test_basic_search():
    """Test basic search functionality"""
    print("="*60)
    print("TEST 1: Basic Search")
    print("="*60)
    
    engine = SearchEngine()
    
    # Test query
    query = "چه غذاهایی خوبه؟"
    print(f"\n🔍 Query: {query}")
    
    results = engine.search(query, top_k=3)
    
    print(f"\n📊 Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. Confidence: {result['confidence_level'].upper()} ({result['similarity']:.3f})")
        print(f"   Condition: {result['metadata'].get('condition_name', 'N/A')}")
        print(f"   Topic: {result['metadata'].get('topic', 'N/A')}")
        print(f"   Q: {result['metadata'].get('question', 'N/A')[:50]}...")
        print()


def test_filtered_search():
    """Test search with condition filter"""
    print("="*60)
    print("TEST 2: Filtered Search (Within Condition)")
    print("="*60)
    
    engine = SearchEngine()
    
    query = "علائم چیه؟"
    condition_id = "cond_type_2_diabetes"
    
    print(f"\n🔍 Query: {query}")
    print(f"   Filter: {condition_id}")
    
    results = engine.search_within_condition(
        query=query,
        condition_id=condition_id,
        top_k=3
    )
    
    print(f"\n📊 Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. Confidence: {result['confidence_level'].upper()} ({result['similarity']:.3f})")
        print(f"   Condition ID: {result['metadata']['condition_id']}")
        print(f"   Q: {result['metadata']['question']}")
        print()
    
    # Verify all results are from correct condition
    all_match = all(r['metadata']['condition_id'] == condition_id for r in results)
    print(f"✅ All results from correct condition: {all_match}")


def test_condition_mismatch():
    """Test condition mismatch detection"""
    print("="*60)
    print("TEST 3: Condition Mismatch Detection")
    print("="*60)
    
    engine = SearchEngine()
    
    # Simulate: User clicked diabetes, but asks about hypertension
    query = "فشار خون چطور کنترل کنم؟"
    current_condition = "cond_type_2_diabetes"
    
    print(f"\n🔍 Query: {query}")
    print(f"   Current condition: {current_condition}")
    
    mismatch = engine.detect_condition_mismatch(
        query=query,
        current_condition_id=current_condition
    )
    
    print(f"\n📊 Mismatch Detection Result:")
    if mismatch and mismatch.get('is_mismatch'):
        print(f"   ⚠️  MISMATCH DETECTED!")
        print(f"   Detected condition: {mismatch['detected_condition_name']}")
        print(f"   Similarity: {mismatch['similarity']:.3f}")
        print(f"   Difference: {mismatch['similarity_diff']:.3f}")
    else:
        print(f"   ✅ No mismatch (question is about current condition)")


def test_chatbot_handler():
    """Test high-level chatbot handler"""
    print("="*60)
    print("TEST 4: Chatbot Handler")
    print("="*60)
    
    handler = ChatbotSearchHandler()
    
    test_cases = [
        ("چه غذاهایی برای دیابت خوبه؟", "cond_type_2_diabetes"),
        ("فشار خون چطور کنترل کنم؟", "cond_type_2_diabetes"),  # Mismatch
        ("خیلی سوال عجیب غریبی", "cond_type_2_diabetes"),  # Low confidence
    ]
    
    for query, condition_id in test_cases:
        print(f"\n{'─'*60}")
        print(f"🔍 Query: {query}")
        print(f"   Condition: {condition_id}")
        
        response = handler.handle_user_query(
            query=query,
            condition_id=condition_id
        )
        
        print(f"\n📊 Response Type: {response['response_type'].upper()}")
        
        if response['response_type'] == 'direct_answer':
            print(f"   Answer: {response['answer'][:100]}...")
            print(f"   Confidence: {response['confidence']:.3f}")
        
        elif response['response_type'] == 'condition_mismatch':
            print(f"   ⚠️  {response['message']}")
            print(f"   Detected: {response['detected_condition_name']}")
        
        elif response['response_type'] == 'clarification':
            print(f"   Message: {response['message']}")
        
        elif response['response_type'] == 'llm_fallback':
            print(f"   → Need LLM fallback")
            print(f"   Message: {response['message']}")


def test_stats():
    """Show search engine statistics"""
    print("="*60)
    print("TEST 5: Engine Statistics")
    print("="*60)
    
    engine = SearchEngine()
    stats = engine.get_stats()
    
    print(f"\n📊 Search Engine Stats:")
    print(f"   Total items: {stats['total_items']}")
    print(f"   Embedding dimension: {stats['embedding_dimension']}")
    print(f"   High confidence: ≥ {stats['high_confidence_threshold']}")
    print(f"   Medium confidence: ≥ {stats['medium_confidence_threshold']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SEARCH ENGINE TEST SUITE")
    print("="*60 + "\n")
    
    try:
        test_basic_search()
        print("\n")
        
        test_filtered_search()
        print("\n")
        
        test_condition_mismatch()
        print("\n")
        
        test_chatbot_handler()
        print("\n")
        
        test_stats()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()