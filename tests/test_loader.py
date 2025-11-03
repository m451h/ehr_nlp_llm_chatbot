"""Test JSON loader"""
import sys
sys.path.insert(0, '.')

from src.loaders.json_loader import JSONLoader

# Initialize
loader = JSONLoader()

# Load all files
items = loader.load_directory()

# Show stats
stats = loader.get_stats(items)
print(f"\n📊 Statistics:")
print(f"   Total items: {stats['total_items']}")
print(f"   Conditions: {stats['num_conditions']}")
print(f"   Topics: {stats['num_topics']}")

# Show sample
if items:
    print(f"\n📝 Sample item:")
    sample = items[0]
    print(f"   ID: {sample['id']}")
    print(f"   Condition: {sample['metadata']['condition_name']}")
    print(f"   Topic: {sample['metadata']['topic']}")
    print(f"   Question: {sample['metadata']['question']}")