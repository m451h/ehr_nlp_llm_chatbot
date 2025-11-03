"""
JSON file loader
Loads Q&A data from JSON files
"""
import json
from pathlib import Path
from typing import List, Dict, Union
from config.settings import RAW_DATA_DIR


class JSONLoader:
    """Load Q&A data from JSON files"""
    
    def __init__(self, data_dir: Union[str, Path] = None):
        self.data_dir = Path(data_dir) if data_dir else RAW_DATA_DIR
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        
        print(f"📁 JSON Loader initialized")
        print(f"   Data directory: {self.data_dir}")
    
    def load_file(self, filepath: Union[str, Path]) -> List[Dict]:
        """
        Load a single JSON file
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            List of Q&A items
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        print(f"📄 Loading: {filepath.name}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON formats
        items = self._normalize_format(data)
        
        print(f"   ✓ Loaded {len(items)} items")
        return items
    
    def load_directory(self, pattern: str = "*.json") -> List[Dict]:
        """
        Load all JSON files from directory
        
        Args:
            pattern: File pattern (e.g., "*.json", "diabetes_*.json")
            
        Returns:
            List of all Q&A items from all files
        """
        print(f"\n📁 Scanning directory: {self.data_dir}")
        print(f"   Pattern: {pattern}")
        
        json_files = list(self.data_dir.glob(pattern))
        
        if not json_files:
            raise FileNotFoundError(f"No JSON files found matching: {pattern}")
        
        print(f"   Found {len(json_files)} files")
        
        all_items = []
        for json_file in sorted(json_files):
            items = self.load_file(json_file)
            all_items.extend(items)
        
        print(f"\n📊 Total items loaded: {len(all_items)}")
        return all_items
    
    def load_specific_conditions(self, condition_ids: List[str]) -> List[Dict]:
        """
        Load specific conditions by ID
        
        Args:
            condition_ids: List of condition IDs (e.g., ["cond_diabetes", "cond_hypertension"])
            
        Returns:
            List of Q&A items for specified conditions
        """
        all_items = self.load_directory()
        
        filtered_items = [
            item for item in all_items
            if item['metadata']['condition_id'] in condition_ids
        ]
        
        print(f"📊 Filtered to {len(filtered_items)} items for {len(condition_ids)} conditions")
        return filtered_items
    
    def _normalize_format(self, data: Union[Dict, List]) -> List[Dict]:
        """
        Normalize different JSON formats to standard list
        
        Handles:
        - Direct list: [{"id": ..., "text": ..., "metadata": ...}, ...]
        - Wrapped: {"conditions": [...]}
        - Single item: {"id": ..., "text": ..., "metadata": ...}
        """
        if isinstance(data, list):
            return data
        
        if isinstance(data, dict):
            # Check for wrapped format
            if 'conditions' in data:
                return data['conditions']
            
            # Check if it's a single item
            if 'id' in data and 'text' in data and 'metadata' in data:
                return [data]
        
        raise ValueError(f"Unrecognized JSON format: {type(data)}")
    
    def get_stats(self, items: List[Dict]) -> Dict:
        """Get statistics about loaded data"""
        conditions = set()
        topics = set()
        
        for item in items:
            conditions.add(item['metadata']['condition_id'])
            topics.add(item['metadata']['topic'])
        
        return {
            'total_items': len(items),
            'num_conditions': len(conditions),
            'num_topics': len(topics),
            'conditions': sorted(conditions),
            'topics': sorted(topics)
        }