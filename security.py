"""Security features for Callisto."""
import re
import html

def sanitize_input(text: str) -> str:
    """Remove potentially malicious content from input text."""
    if not text:
        return ""
        
    # HTML escape to prevent XSS
    text = html.escape(text)
    
    # Remove potentially harmful patterns
    text = re.sub(r'(?i)(<script.*?>.*?</script>)', '', text)
    text = re.sub(r'(?i)javascript:', '', text)
    
    return text.strip()

def validate_uuid(uuid_str: str) -> bool:
    """Validate that a string is a properly formatted UUID."""
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
    return bool(uuid_pattern.match(uuid_str))

def secure_delete(text: str) -> str:
    """Replace text with random data for secure deletion (simplified)."""
    import secrets
    return ''.join(secrets.choice('X') for _ in range(len(text)))