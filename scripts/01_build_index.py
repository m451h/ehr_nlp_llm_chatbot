"""
Build Vector Database Index
Loads all JSON files and creates ChromaDB index
"""
import sys
sys.path.insert(0, '.')

from src.loaders.json_loader import JSONLoader
from src.models.embeddings import get_embedding_model
from src.database.vector_db import VectorDatabase
from config.settings import BATCH_SIZE, EMBEDDING_BATCH_SIZE
import time

def flatten_metadata(metadata):
    """Convert any list values in metadata into comma-separated strings."""
    clean = {}
    for k, v in metadata.items():
        if isinstance(v, list):
            clean[k] = ", ".join(map(str, v))  # turn list into string
        else:
            clean[k] = v
    return clean
def build_index():
    """Main function to build the vector database index"""
    
    print("\n" + "="*60)
    print("VECTOR DATABASE INDEX BUILDER")
    print("="*60 + "\n")
    
    start_time = time.time()
    
    # =========================================================================
    # STEP 1: Load JSON Files
    # =========================================================================
    print("STEP 1: Loading JSON Files")
    print("-"*60)
    
    loader = JSONLoader()
    
    try:
        qa_items = loader.load_directory(pattern="*.json")
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"\n💡 Make sure your JSON files are in: data/raw/")
        print(f"   Current structure should be:")
        print(f"   ehr_chatbot/")
        print(f"   └── data/")
        print(f"       └── raw/")
        print(f"           ├── diabetes.json")
        print(f"           ├── hypertension.json")
        print(f"           └── ...")
        return False
    
    if not qa_items:
        print("\n❌ No Q&A items found!")
        return False
    
    # Show statistics
    stats = loader.get_stats(qa_items)
    print(f"\n📊 Data Statistics:")
    print(f"   Total Q&A items: {stats['total_items']}")
    print(f"   Conditions: {stats['num_conditions']}")
    print(f"   Topics: {stats['num_topics']}")
    
    # Show conditions
    print(f"\n📋 Conditions loaded:")
    for i, cond in enumerate(stats['conditions'][:10], 1):
        print(f"   {i}. {cond}")
    if len(stats['conditions']) > 10:
        print(f"   ... and {len(stats['conditions']) - 10} more")
    
    # =========================================================================
    # STEP 2: Initialize Components
    # =========================================================================
    print(f"\n{'='*60}")
    print("STEP 2: Initializing Components")
    print("-"*60)
    
    # Load embedding model
    embedding_model = get_embedding_model()
    
    # Initialize vector database
    vector_db = VectorDatabase()
    
    # Create fresh collection
    print("\n⚠️  Creating new collection (will delete existing data)")
    vector_db.create_collection()
    
    # =========================================================================
    # STEP 3: Compute Embeddings
    # =========================================================================
    print(f"\n{'='*60}")
    print("STEP 3: Computing Embeddings")
    print("-"*60)
    
    # Extract data
    ids = [item['id'] for item in qa_items]
    texts = [item['text'] for item in qa_items]
    metadatas = [item['metadata'] for item in qa_items]
    
    print(f"\n🔄 Computing embeddings for {len(texts)} items...")
    print(f"   This may take several minutes...")
    print(f"   Batch size: {EMBEDDING_BATCH_SIZE}")
    
    embeddings_start = time.time()
    
    embeddings = embedding_model.encode(
        texts,
        batch_size=EMBEDDING_BATCH_SIZE,
        show_progress=True
    )
    
    embeddings_time = time.time() - embeddings_start
    print(f"\n✅ Embeddings computed in {embeddings_time:.1f} seconds")
    print(f"   Average: {embeddings_time/len(texts):.3f} seconds per item")
    
    # =========================================================================
    # STEP 4: Add to Vector Database
    # =========================================================================
    print(f"\n{'='*60}")
    print("STEP 4: Adding to Vector Database")
    print("-"*60)
    metadatas = [flatten_metadata(item['metadata']) for item in qa_items]
    vector_db.add_items(
        ids=ids,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        documents=texts,
        batch_size=BATCH_SIZE
    )
    
    # =========================================================================
    # STEP 5: Verify and Show Results
    # =========================================================================
    print(f"\n{'='*60}")
    print("STEP 5: Verification")
    print("-"*60)
    
    # Get final stats
    db_stats = vector_db.get_stats()
    
    print(f"\n✅ Vector Database Built Successfully!")
    print(f"\n📊 Final Statistics:")
    print(f"   Items in database: {db_stats['total_items']}")
    print(f"   Collection name: {db_stats['collection_name']}")
    
    # Verify count matches
    if db_stats['total_items'] == len(qa_items):
        print(f"   ✅ Count verified: All items added correctly")
    else:
        print(f"   ⚠️  Warning: Count mismatch!")
        print(f"      Expected: {len(qa_items)}")
        print(f"      In DB: {db_stats['total_items']}")
    
    # =========================================================================
    # Summary
    # =========================================================================
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print("BUILD COMPLETE")
    print("="*60)
    print(f"\n⏱️  Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"\n📁 Index location: ./vector_db/")
    print(f"\n🎯 Next steps:")
    print(f"   1. Run tests: python scripts/02_test_search.py")
    print(f"   2. Or test search: python scripts/test_search_engine.py")

    
    return True


def quick_stats():
    """Show quick statistics of existing index"""
    print("\n" + "="*60)
    print("VECTOR DATABASE STATISTICS")
    print("="*60 + "\n")
    
    try:
        vector_db = VectorDatabase()
        vector_db.get_collection()
        
        stats = vector_db.get_stats()
        
        print(f"📊 Current Index:")
        print(f"   Total items: {stats['total_items']}")
        print(f"   Collection: {stats['collection_name']}")
        
        # Try a sample query
        from src.models.embeddings import get_embedding_model
        
        model = get_embedding_model()
        test_query = "علائم چیه؟"
        query_emb = model.encode_single(test_query)
        
        results = vector_db.query(
            query_embeddings=[query_emb.tolist()],
            n_results=1
        )
        
        if results['ids'][0]:
            print(f"\n✅ Index is working!")
            print(f"   Sample query: '{test_query}'")
            print(f"   Found result: {results['metadatas'][0][0]['question']}")
        
    except Exception as e:
        print(f"❌ No index found or error: {e}")
        print(f"\n💡 Run: python scripts/01_build_index.py build")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "build":
            success = build_index()
            sys.exit(0 if success else 1)
        
        elif command == "stats":
            quick_stats()
        
        elif command == "rebuild":
            print("\n⚠️  This will DELETE existing index and rebuild from scratch!")
            response = input("Continue? (yes/no): ")
            if response.lower() in ['yes', 'y']:
                success = build_index()
                sys.exit(0 if success else 1)
            else:
                print("Cancelled.")
        
        else:
            print(f"Unknown command: {command}")
            print(f"Usage: python scripts/01_build_index.py [build|stats|rebuild]")
    
    else:
        print("\n" + "="*60)
        print("Vector Database Index Builder")
        print("="*60)
        print("\nUsage:")
        print("  python scripts/01_build_index.py build      # Build new index")
        print("  python scripts/01_build_index.py stats      # Show current stats")
        print("  python scripts/01_build_index.py rebuild    # Rebuild from scratch")
        print("\n" + "="*60)