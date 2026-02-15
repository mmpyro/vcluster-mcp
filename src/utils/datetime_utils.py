from datetime import datetime, timezone

def calculate_age(creation_timestamp) -> str:
    """Calculate the age of a resource"""
    if not creation_timestamp:
        return 'Unknown'
    
    now = datetime.now(timezone.utc)
    age = now - creation_timestamp
    
    days = age.days
    hours = age.seconds // 3600
    minutes = (age.seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d{hours}h"
    elif hours > 0:
        return f"{hours}h{minutes}m"
    else:
        return f"{minutes}m"
