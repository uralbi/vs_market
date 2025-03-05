from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import datetime, timedelta
from json import dumps


def get_ids(objects):
    ids = []
    for obj in objects:
        ids.append(obj.id)
    return ids


def tojson(value):
    """Convert Python objects to a JSON string"""
    return dumps(value)


def time_ago(timestamp):
    if not timestamp:
        return "Unknown"

    now = datetime.utcnow()
    
    if timestamp.tzinfo is not None and timestamp.tzinfo.utcoffset(timestamp) is not None:
        timestamp = timestamp.replace(tzinfo=None)
        
    diff = now - timestamp

    if diff < timedelta(minutes=1):
        return "Только что"
    elif diff < timedelta(hours=1):
        return f"{diff.seconds // 60} мин назад"
    elif diff < timedelta(days=1):
        return f"{diff.seconds // 3600}ч. назад"
    elif diff < timedelta(days=2):
        return f"{diff.days} день назад"
    elif diff < timedelta(days=5):
        return f"{diff.days} дня назад"
    elif diff < timedelta(days=30):
        return f"{diff.days} дней назад"
    elif diff < timedelta(days=365):
        return f"{diff.days // 30} мес. назад"
    else:
        years = diff.days // 365
        if years < 2:
            return "Год назад"
        if years < 5:
            return f"{diff.days // 365} года назад"
        else:
            return f"{diff.days // 365} лет назад"
        
