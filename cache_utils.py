# Quantum_simulator/cache_utils.py
import os
import time
import pickle
import logging
from datetime import datetime, timedelta

class FileCache:
    def __init__(self, cache_dir="cache", ttl=3600):
        self.cache_dir = cache_dir
        self.ttl = ttl  # Time-to-live in seconds (1 hour)
        os.makedirs(cache_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def get(self, key):
        """Retrieve a value from the cache by key."""
        file_path = os.path.join(self.cache_dir, f"{key}.pkl")
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                # Check if cache entry is expired
                if data['timestamp'] + timedelta(seconds=self.ttl) > datetime.now():
                    return data['value']
                else:
                    os.remove(file_path)  # Remove expired file
                    return None
            return None
        except Exception as e:
            self.logger.error(f"Failed to read cache for key {key}: {str(e)}")
            return None

    def set(self, key, value):
        """Store a value in the cache with a timestamp."""
        file_path = os.path.join(self.cache_dir, f"{key}.pkl")
        try:
            with open(file_path, 'wb') as f:
                pickle.dump({
                    'value': value,
                    'timestamp': datetime.now()
                }, f)
        except Exception as e:
            self.logger.error(f"Failed to write cache for key {key}: {str(e)}")

    def clear_expired(self):
        """Remove all expired cache files."""
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                if data['timestamp'] + timedelta(seconds=self.ttl) <= datetime.now():
                    os.remove(file_path)
        except Exception as e:
            self.logger.error(f"Failed to clear expired cache: {str(e)}")