"""
Configuration settings for EHR Chatbot
"""
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTOR_DB_DIR = PROJECT_ROOT / "vector_db"

# Ensure directories exist
VECTOR_DB_DIR.mkdir(exist_ok=True)
PROCESSED_DATA_DIR.mkdir(exist_ok=True)

# Model settings
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
EMBEDDING_DIMENSION = 384

# ChromaDB settings
CHROMA_COLLECTION_NAME = "ehr_qa"
CHROMA_DISTANCE_METRIC = "cosine"

# Search settings
HIGH_CONFIDENCE_THRESHOLD = 0.83
MEDIUM_CONFIDENCE_THRESHOLD = 0.75
DEFAULT_TOP_K = 3

# Batch processing
BATCH_SIZE = 1000
EMBEDDING_BATCH_SIZE = 32

print(f"✅ Configuration loaded")
print(f"   Project root: {PROJECT_ROOT}")
print(f"   Raw data: {RAW_DATA_DIR}")
print(f"   Vector DB: {VECTOR_DB_DIR}")