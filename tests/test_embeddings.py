"""Test embedding model"""
import sys
sys.path.insert(0, '.')

from src.models.embeddings import get_embedding_model

# Test
model = get_embedding_model()

text = "چه غذاهایی خوبه؟"
embedding = model.encode_single(text)

print(f"✅ Embedding test passed")
print(f"   Text: {text}")
print(f"   Embedding shape: {embedding.shape}")
print(f"   First 5 values: {embedding[:5]}")