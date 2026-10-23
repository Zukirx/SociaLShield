import numpy as np
from datetime import datetime
from .user_store import get_user, update_user_history
from .roberta_classifier import get_roberta_scorer

def calculate_credibility(post) -> float:
    # 1. RoBERTa Text-Based Credibility Score (Multi-Class weights proxy)
    roberta = get_roberta_scorer(use_mock=True) # use mock by default for fast local testing
    text_score = roberta.predict_score(post.text_content)
    
    # 2. Historical Ground Truth
    user_record = get_user(post.author_id)
    baseline = user_record['credibility_score'] if user_record else 0.5
    
    # 3. Account Integrity
    age_days = post.author_meta.get('account_age_days', 1)
    followers = post.author_meta.get('followers', 1)
    verified = post.author_meta.get('verified', False)
    
    integrity_score = 0.5
    if verified:
        integrity_score += 0.2
    if age_days > 365:
        integrity_score += 0.1
    elif age_days < 30:
        integrity_score -= 0.2
        
    if followers > 1000:
        integrity_score += 0.1
        
    integrity_score = max(0.0, min(1.0, integrity_score))
    
    # 4. Final blended score (RoBERTa + User Integrity)
    # Give high weight to the RoBERTa score to emphasize the NLP framework 
    final_score = (text_score * 0.6) + (integrity_score * 0.2) + (baseline * 0.2)
    final_score = max(0.0, min(1.0, final_score))
    
    # Update store
    history = post.author_history if post.author_history else []
    update_user_history(post.author_id, post.author_username, history, final_score)
    
    return final_score
