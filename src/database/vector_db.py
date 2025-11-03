"""
Vector Database using ChromaDB
Handles storage and retrieval of embeddings
"""
import chromadb
from chromadb.config import Settings
from chromadb import PersistentClient
from typing import List, Dict, Optional
from config.settings import (
    VECTOR_DB_DIR, 
    CHROMA_COLLECTION_NAME, 
    CHROMA_DISTANCE_METRIC
)


class VectorDatabase:
    """ChromaDB wrapper for vector storage"""
    
    def __init__(self):
        print(f"🔄 Initializing Vector Database")
        print(f"   Location: {VECTOR_DB_DIR}")
        
        self.client = PersistentClient(path=str(VECTOR_DB_DIR))
        
        self.collection = None
        print(f"✅ Vector DB initialized")
    
    def create_collection(self, name: str = CHROMA_COLLECTION_NAME):
        """Create a new collection (deletes existing)"""
        print(f"🗑️  Deleting existing collection if exists...")
        try:
            self.client.delete_collection(name)
        except:
            pass
        
        print(f"🔨 Creating collection: {name}")
        self.collection = self.client.create_collection(
            name=name,
            metadata={"hnsw:space": CHROMA_DISTANCE_METRIC}
        )
        print(f"✅ Collection created")
    
    def get_collection(self, name: str = CHROMA_COLLECTION_NAME):
        """Get existing collection"""
        print(f"📂 Loading collection: {name}")
        self.collection = self.client.get_collection(name)
        print(f"✅ Collection loaded ({self.collection.count()} items)")
    
    def get_or_create_collection(self, name: str = CHROMA_COLLECTION_NAME):
        """Get collection or create if doesn't exist"""
        try:
            self.get_collection(name)
        except:
            self.create_collection(name)
    
    def add_items(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        documents: List[str],
        batch_size: int = 1000
    ):
        """
        Add items to collection in batches
        
        Args:
            ids: List of unique IDs
            embeddings: List of embedding vectors
            metadatas: List of metadata dicts
            documents: List of text documents
            batch_size: Batch size for adding
        """
        if self.collection is None:
            raise RuntimeError("No collection loaded. Call get_or_create_collection() first")
        
        total = len(ids)
        print(f"\n📦 Adding {total} items to vector DB...")
        
        for i in range(0, total, batch_size):
            batch_end = min(i + batch_size, total)
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"   Batch {batch_num}/{total_batches}: items {i+1}-{batch_end}")
            
            self.collection.add(
                ids=ids[i:batch_end],
                embeddings=embeddings[i:batch_end],
                metadatas=metadatas[i:batch_end],
                documents=documents[i:batch_end]
            )
        
        print(f"✅ All items added to vector DB")
    
    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 3,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query the collection
        
        Args:
            query_embeddings: Query vectors
            n_results: Number of results to return
            where: Filter conditions (e.g., {"condition_id": "cond_diabetes"})
            
        Returns:
            Query results
        """
        if self.collection is None:
            raise RuntimeError("No collection loaded")
        
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
            include=["metadatas", "documents", "distances"]
        )
    
    def count(self) -> int:
        """Get number of items in collection"""
        if self.collection is None:
            return 0
        return self.collection.count()
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        return {
            'total_items': self.count(),
            'collection_name': self.collection.name if self.collection else None
        }