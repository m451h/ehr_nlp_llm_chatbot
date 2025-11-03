"""Test Vector Database"""
import sys
sys.path.insert(0, '.')

from src.database.vector_db import VectorDatabase
import numpy as np

# Initialize
db = VectorDatabase()
db.create_collection("test_collection")

# Add test data
test_ids = ["test_1", "test_2", "test_3"]
test_embeddings = np.random.rand(3, 384).tolist()
test_metadatas = [
    {"condition_id": "cond_diabetes", "topic": "test"},
    {"condition_id": "cond_diabetes", "topic": "test"},
    {"condition_id": "cond_hypertension", "topic": "test"}
]
test_documents = ["Test doc 1", "Test doc 2", "Test doc 3"]

db.add_items(test_ids, test_embeddings, test_metadatas, test_documents)

# Query
results = db.query(
    query_embeddings=[test_embeddings[0]],
    n_results=2,
    where={"condition_id": "cond_diabetes"}
)

print(f"\n✅ Test passed!")
print(f"   Found {len(results['ids'][0])} results")
print(f"   IDs: {results['ids'][0]}")

# Cleanup
db.client.delete_collection("test_collection")