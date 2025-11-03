"""
Search Engine
Combines embedding model, vector DB, and search logic
"""
from typing import List, Dict, Optional
from src.models.embeddings import get_embedding_model
from src.database.vector_db import VectorDatabase
from config.settings import (
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
    DEFAULT_TOP_K
)


class SearchEngine:
    """
    Main search engine for Q&A retrieval
    Handles query -> embedding -> search -> results
    """
    
    def __init__(self):
        print("🔄 Initializing Search Engine...")
        
        # Load embedding model
        self.embedding_model = get_embedding_model()
        
        # Load vector database
        self.vector_db = VectorDatabase()
        self.vector_db.get_or_create_collection()
        
        print(f"✅ Search Engine ready")
        print(f"   Items in DB: {self.vector_db.count()}")
    
    def search(
        self,
        query: str,
        condition_id: Optional[str] = None,
        topic: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K
    ) -> List[Dict]:
        """
        Search for similar Q&As
        
        Args:
            query: User's question in Persian
            condition_id: Filter by condition (e.g., "cond_type_2_diabetes")
            topic: Filter by topic (e.g., "رژیم غذایی")
            top_k: Number of results to return
            
        Returns:
            List of results with similarity scores and metadata
            
        Example:
            results = engine.search(
                query="چه غذاهایی خوبه؟",
                condition_id="cond_type_2_diabetes",
                top_k=3
            )
        """
        # Step 1: Convert query to embedding
        query_embedding = self.embedding_model.encode_single(query)
        
        # Step 2: Build filter
        where_filter = self._build_filter(condition_id, topic)
        
        # Step 3: Query vector database
        results = self.vector_db.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where_filter
        )
        
        # Step 4: Format results
        formatted_results = self._format_results(results)
        
        return formatted_results
    
    def search_within_condition(
        self,
        query: str,
        condition_id: str,
        top_k: int = DEFAULT_TOP_K
    ) -> List[Dict]:
        """
        Search within a specific condition
        This is the main method for button-clicked chatbot flow
        
        Args:
            query: User's question
            condition_id: The condition user clicked on
            top_k: Number of results
            
        Returns:
            List of results filtered to this condition only
        """
        return self.search(
            query=query,
            condition_id=condition_id,
            top_k=top_k
        )
    
    def search_all_conditions(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K
    ) -> List[Dict]:
        """
        Search across ALL conditions (no filter)
        Used for detecting if question is about a different condition
        
        Args:
            query: User's question
            top_k: Number of results
            
        Returns:
            List of results from all conditions
        """
        return self.search(
            query=query,
            condition_id=None,
            top_k=top_k
        )
    
    def detect_condition_mismatch(
        self,
        query: str,
        current_condition_id: str,
        threshold: float = 0.2
    ) -> Optional[Dict]:
        """
        Detect if user is asking about a different condition
        
        Args:
            query: User's question
            current_condition_id: The condition chat is currently about
            threshold: Similarity difference threshold to trigger detection
            
        Returns:
            Dict with other condition info if mismatch detected, None otherwise
            
        Example:
            User clicked: "دیابت نوع ۲"
            User asks: "فشار خون چطور کنترل کنم؟"
            
            Result: {
                'is_mismatch': True,
                'detected_condition_id': 'cond_hypertension',
                'detected_condition_name': 'فشار خون بالا',
                'similarity': 0.85
            }
        """
        # Search in current condition
        current_results = self.search_within_condition(
            query=query,
            condition_id=current_condition_id,
            top_k=1
        )
        
        # Search in all conditions
        all_results = self.search_all_conditions(
            query=query,
            top_k=1
        )
        
        if not current_results or not all_results:
            return None
        
        current_best = current_results[0]
        all_best = all_results[0]
        
        # Check if best match is from different condition
        if all_best['metadata']['condition_id'] != current_condition_id:
            # And if it's significantly better
            similarity_diff = all_best['similarity'] - current_best['similarity']
            
            if similarity_diff >= threshold:
                return {
                    'is_mismatch': True,
                    'current_condition_id': current_condition_id,
                    'detected_condition_id': all_best['metadata']['condition_id'],
                    'detected_condition_name': all_best['metadata']['condition_name'],
                    'similarity': all_best['similarity'],
                    'similarity_diff': similarity_diff
                }
        
        return {
            'is_mismatch': False
        }
    
    def _build_filter(
        self,
        condition_id: Optional[str] = None,
        topic: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Build ChromaDB filter from parameters
        
        Args:
            condition_id: Filter by condition
            topic: Filter by topic
            
        Returns:
            Filter dict for ChromaDB or None
        """
        filters = {}
        
        if condition_id:
            filters["condition_id"] = condition_id
        
        if topic:
            filters["topic"] = topic
        
        return filters if filters else None
    
    def _format_results(self, raw_results: Dict) -> List[Dict]:
        """
        Format ChromaDB results into clean structure
        
        Args:
            raw_results: Raw results from ChromaDB
            
        Returns:
            List of formatted result dicts
        """
        formatted = []
        
        # ChromaDB returns nested structure
        ids = raw_results['ids'][0] if raw_results['ids'] else []
        documents = raw_results['documents'][0] if raw_results['documents'] else []
        metadatas = raw_results['metadatas'][0] if raw_results['metadatas'] else []
        distances = raw_results['distances'][0] if raw_results['distances'] else []
        
        for i in range(len(ids)):
            # Convert distance to similarity
            # ChromaDB returns L2 distance, convert to similarity (0-1)
            distance = distances[i]
            similarity = max(0, 1 - (distance / 2))
            
            formatted.append({
                'id': ids[i],
                'text': documents[i],
                'metadata': metadatas[i],
                'similarity': float(similarity),
                'distance': float(distance),
                'confidence_level': self._get_confidence_level(similarity)
            })
        
        return formatted
    
    def _get_confidence_level(self, similarity: float) -> str:
        """
        Determine confidence level based on similarity score
        
        Args:
            similarity: Similarity score (0-1)
            
        Returns:
            'high', 'medium', or 'low'
        """
        if similarity >= HIGH_CONFIDENCE_THRESHOLD:
            return 'high'
        elif similarity >= MEDIUM_CONFIDENCE_THRESHOLD:
            return 'medium'
        else:
            return 'low'
    
    def get_stats(self) -> Dict:
        """Get search engine statistics"""
        return {
            'total_items': self.vector_db.count(),
            'embedding_dimension': self.embedding_model.dimension,
            'high_confidence_threshold': HIGH_CONFIDENCE_THRESHOLD,
            'medium_confidence_threshold': MEDIUM_CONFIDENCE_THRESHOLD
        }


class ChatbotSearchHandler:
    """
    High-level handler for chatbot search logic
    Implements the button-click -> search flow
    """
    
    def __init__(self):
        self.search_engine = SearchEngine()
    
    def handle_user_query(
        self,
        query: str,
        condition_id: str,
        detect_mismatch: bool = True
    ) -> Dict:
        """
        Handle a user query in the chatbot
        
        Args:
            query: User's question
            condition_id: The condition user clicked on
            detect_mismatch: Whether to detect if question is about different condition
            
        Returns:
            Dict with response and metadata
        """
        # Search within current condition
        results = self.search_engine.search_within_condition(
            query=query,
            condition_id=condition_id,
            top_k=3
        )
        
        if not results:
            return {
                'response_type': 'no_results',
                'message': 'متأسفم، چیزی پیدا نکردم. می‌تونید سوالتون رو واضح‌تر بپرسید؟'
            }
        
        best_match = results[0]
        confidence = best_match['confidence_level']
        
        # Check for condition mismatch
        mismatch = None
        if detect_mismatch and confidence == 'low':
            mismatch = self.search_engine.detect_condition_mismatch(
                query=query,
                current_condition_id=condition_id
            )
        
        # Build response based on confidence and mismatch
        if mismatch and mismatch.get('is_mismatch'):
            return {
                'response_type': 'condition_mismatch',
                'message': f"به نظر می‌رسه سوال شما درباره {mismatch['detected_condition_name']} باشه، نه {best_match['metadata']['condition_name']}.",
                'detected_condition_id': mismatch['detected_condition_id'],
                'detected_condition_name': mismatch['detected_condition_name'],
                'current_condition_id': condition_id,
                'suggestion': 'می‌خواید به چت آن بیماری برید؟'
            }
        
        elif confidence == 'high':
            return {
                'response_type': 'direct_answer',
                'answer': best_match['metadata']['answer'],
                'follow_up': best_match['metadata'].get('follow_up'),
                'related_topics': best_match['metadata'].get('related_topics', []),
                'confidence': best_match['similarity'],
                'source': 'knowledge_base'
            }
        
        elif confidence == 'medium':
            return {
                'response_type': 'clarification',
                'message': f"منظورتون این است؟\n\n{best_match['metadata']['question']}",
                'matched_question': best_match['metadata']['question'],
                'matched_answer': best_match['metadata']['answer'],
                'confidence': best_match['similarity'],
                'alternatives': [r['metadata']['question'] for r in results[1:3]]
            }
        
        else:  # low confidence
            return {
                'response_type': 'llm_fallback',
                'message': 'سوال شما رو کاملا متوجه نشدم. بهتره از هوش مصنوعی کمک بگیرم...',
                'query': query,
                'condition_id': condition_id,
                'best_match': best_match,
                'use_llm': True
            }