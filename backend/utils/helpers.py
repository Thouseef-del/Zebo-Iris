"""General helper utilities used by the backend."""
import os

def save_bytes_to_file(data: bytes, dest_path: str) -> None:
    """Save raw bytes to disk, creating directories as needed."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, 'wb') as f:
        f.write(data)
