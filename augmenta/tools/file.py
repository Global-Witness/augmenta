"""
File handling utilities for loading binary content.
"""
import mimetypes
from pathlib import Path
from typing import Optional, Union, Any

from pydantic_ai import BinaryContent


def load_file(file_path: Union[str, Path, Any]) -> Optional[BinaryContent]:
    """
    Load a file as binary content with appropriate MIME type detection.
    
    Args:
        file_path: Path to the file to load
        
    Returns:
        BinaryContent object with binary data and media type if file exists,
        None otherwise
    """
    # Skip if file path is None, empty, or 'NA' or not a string-like object
    if file_path is None:
        return None
    
    # Handle non-string types by converting to string first
    try:
        file_path_str = str(file_path).strip()
        if not file_path_str or file_path_str.upper() == 'NA':
            return None
    except:
        # If we can't convert to string, it's not a valid path
        return None
    
    try:
        path = Path(file_path_str)
        
        # Check if file exists
        if not path.exists():
            return None
        
        # Read binary content
        file_binary = path.read_bytes()
        
        # Determine MIME type
        media_type = mimetypes.guess_type(str(path))[0]
        
        # Default to application/octet-stream if type cannot be determined
        if not media_type:
            media_type = "application/octet-stream"
        
        # Create and return binary content
        return BinaryContent(data=file_binary, media_type=media_type)
    
    except Exception as e:
        print(f"Error loading file {file_path}: {str(e)}")
        return None
