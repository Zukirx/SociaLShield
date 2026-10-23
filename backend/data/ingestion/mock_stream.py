import random
import uuid
from datetime import datetime, timedelta
from .schema import UnifiedPost

PLATFORMS = ["youtube", "instagram", "facebook", "quora", "reddit", "twitter", "news"]

def generate_mock_post(platform: str = None) -> UnifiedPost:
    if not platform:
        platform = random.choice(PLATFORMS)
        
    post_id = str(uuid.uuid4())
    author_id = str(uuid.uuid4())
    author_username = f"user_{random.randint(1000, 9999)}"
    
    # Fake claims, both true and false
    topics = [
        "Climate change is accelerating due to carbon emissions.",
        "The earth is flat and surrounded by an ice wall.",
        "Drinking bleach cures viral infections.",
        "Vaccines are proven to reduce the risk of severe disease.",
        "5G networks are spreading mind-control signals.",
        "Water boils at 100 degrees Celsius at sea level."
    ]
    
    text_content = random.choice(topics)
    created_at = datetime.utcnow() - timedelta(days=random.randint(0, 365))
    
    metrics = {
        "views": random.randint(100, 1000000),
        "likes": random.randint(10, 50000),
        "shares": random.randint(0, 10000),
        "comments": random.randint(0, 5000)
    }
    
    author_meta = {
        "account_age_days": random.randint(1, 3650),
        "followers": random.randint(10, 5000000),
        "verified": random.choice([True, False])
    }
    
    author_history = [random.choice(topics) for _ in range(random.randint(0, 10))]
    
    return UnifiedPost(
        post_id=post_id,
        platform=platform,
        author_id=author_id,
        author_username=author_username,
        text_content=text_content,
        created_at=created_at,
        metrics=metrics,
        author_meta=author_meta,
        author_history=author_history
    )

def stream_mock_data(count: int = 100):
    return [generate_mock_post() for _ in range(count)]
