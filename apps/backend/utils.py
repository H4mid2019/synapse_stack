"""
Utility functions for file handling and validation
"""
import os
import re
import unicodedata
from typing import Optional, Tuple
from werkzeug.utils import secure_filename


# Windows reserved filenames
WINDOWS_RESERVED_NAMES = {
    'con', 'prn', 'aux', 'nul',
    'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
    'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
}

# Dangerous characters that should be removed/escaped
DANGEROUS_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
DANGEROUS_CHAR_MAP = {
    '<': '_lt_',
    '>': '_gt_',
    ':': '_colon_',
    '"': '_quote_',
    '/': '_slash_',
    '\\': '_backslash_',
    '|': '_pipe_',
    '?': '_question_',
    '*': '_asterisk_'
}


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to be safe for filesystem use across platforms.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length (default 255 for most filesystems)
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed_file"
    
    # Normalize Unicode to NFKD form
    normalized = unicodedata.normalize('NFKD', filename)
    
    # Remove control characters and dangerous characters
    sanitized = re.sub(DANGEROUS_CHARS, '', normalized)
    
    # Handle Windows reserved names
    name_without_ext, ext = os.path.splitext(sanitized)
    if name_without_ext.lower() in WINDOWS_RESERVED_NAMES:
        name_without_ext = f"_{name_without_ext}"
    
    # Use werkzeug's secure_filename as baseline
    secure_name = secure_filename(f"{name_without_ext}{ext}")
    
    # Additional sanitization for edge cases
    secure_name = secure_name.strip('. ')
    
    # Ensure we have a name
    if not secure_name or secure_name.startswith('.'):
        secure_name = f"file{ext}" if ext else "unnamed_file"
    
    # Truncate if too long
    if len(secure_name.encode('utf-8')) > max_length:
        secure_name = truncate_filename(secure_name, max_length)
    
    return secure_name


def truncate_filename(filename: str, max_length: int = 255) -> str:
    """
    Truncate filename while preserving extension and ensuring validity.
    
    Args:
        filename: Filename to truncate
        max_length: Maximum length in bytes
        
    Returns:
        Truncated filename
    """
    if len(filename.encode('utf-8')) <= max_length:
        return filename
    
    name_without_ext, ext = os.path.splitext(filename)
    
    # Calculate available space for base name
    ext_bytes = len(ext.encode('utf-8'))
    available_bytes = max_length - ext_bytes - 3  # Reserve 3 bytes for "..."
    
    if available_bytes <= 0:
        # Extension alone is too long, fallback
        return f"file{ext[:max_length-4]}" if ext else "file"
    
    # Truncate the base name
    truncated_name = name_without_ext
    while len(truncated_name.encode('utf-8')) > available_bytes and len(truncated_name) > 1:
        truncated_name = truncated_name[:-1]
    
    # Add ellipsis and extension
    if len(truncated_name) < len(name_without_ext):
        truncated_name += "..."
    
    result = truncated_name + ext
    
    # Final safety check
    if len(result.encode('utf-8')) > max_length:
        # Extreme case: truncate extension too
        result = result[:max_length].encode('utf-8').decode('utf-8', errors='ignore')
    
    return result


def validate_filename(filename: str, max_length: int = 255) -> Tuple[bool, Optional[str]]:
    """
    Validate filename for various edge cases.
    
    Args:
        filename: Filename to validate
        max_length: Maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "Filename cannot be empty"
    
    # Check for whitespace-only names
    if not filename.strip():
        return False, "Filename cannot be empty or whitespace only"
    
    # Check length
    if len(filename.encode('utf-8')) > max_length:
        return False, f"Filename too long (max {max_length} bytes)"
    
    # Check for directory traversal attempts
    if '..' in filename:
        return False, "Filename cannot contain directory traversal sequences"
    
    # Check for dangerous characters
    if re.search(DANGEROUS_CHARS, filename):
        return False, "Filename contains invalid characters"
    
    # Check for Windows reserved names
    name_without_ext, _ = os.path.splitext(filename)
    if name_without_ext.lower() in WINDOWS_RESERVED_NAMES:
        return False, "Filename uses a reserved system name"
    
    # Check for leading/trailing dots and spaces
    if filename.startswith('.') or filename.endswith('.') or filename.startswith(' '):
        return False, "Filename cannot start with '.' or ' '"
    
    return True, None


def is_safe_path(path: str) -> bool:
    """
    Check if a path is safe (no directory traversal).
    
    Args:
        path: Path to check
        
    Returns:
        True if path is safe
    """
    if not path:
        return True
    
    # Resolve the path and check if it's within expected boundaries
    try:
        normalized = os.path.normpath(path)
        if normalized.startswith('..') or '..' in normalized:
            return False
        return True
    except Exception:
        return False


def clean_pdf_filename(filename: str) -> str:
    """
    Clean PDF filename ensuring it has proper extension.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename with .pdf extension
    """
    if not filename:
        return "document.pdf"
    
    # Sanitize first
    cleaned = sanitize_filename(filename)
    
    # Ensure PDF extension
    if not cleaned.lower().endswith('.pdf'):
        name_without_ext, _ = os.path.splitext(cleaned)
        cleaned = f"{name_without_ext}.pdf"
    
    return cleaned


def has_meaningful_content(text: str, min_chars: int = 10) -> bool:
    """
    Check if text content is meaningful (not just whitespace or placeholders).
    
    Args:
        text: Text to check
        min_chars: Minimum number of non-whitespace characters required
        
    Returns:
        True if content is meaningful
    """
    if not text:
        return False
    
    # Remove whitespace and check length
    stripped = re.sub(r'\s+', '', text)
    if len(stripped) < min_chars:
        return False
    
    # Check for common placeholder patterns
    placeholder_patterns = [
        r'^\s*fill?\s*out?\s*this?\s*form?\s*$',
        r'^\s*placeholder\s*$',
        r'^\s*dummy\s*$',
        r'^\s*lorem ipsum\s*$',
        r'^\s*this is a test\s*$'
    ]
    
    text_lower = text.lower().strip()
    for pattern in placeholder_patterns:
        if re.match(pattern, text_lower):
            return False
    
    return True
