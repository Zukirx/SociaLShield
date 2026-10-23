import xgboost as xgb
import numpy as np

class RiskEnsemble:
    def __init__(self):
        self.model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
        self.is_trained = False
        
    def train(self, X, y):
        self.model.fit(X, y)
        self.is_trained = True
        
    def predict_proba(self, features):
        if not self.is_trained:
            # Fallback heuristic if not yet trained
            s_fact, cred, diff, senti = features
            risk = (1.0 - s_fact) * 0.4 + (1.0 - cred) * 0.3 + diff * 0.3
            return float(risk)
            
        return float(self.model.predict_proba(np.array([features]))[0][1])
        
    def assess_risk(self, s_fact: float, user_credibility: float, diffusion_risk: float, sentiment_subj: float = 0.5):
        features = [s_fact, user_credibility, diffusion_risk, sentiment_subj]
        risk_score = self.predict_proba(features)
        
        tier = "Low"
        if risk_score > 0.8:
            tier = "Critical"
        elif risk_score > 0.6:
            tier = "High"
        elif risk_score > 0.4:
            tier = "Medium"
            
        return {
            "risk_score": risk_score,
            "tier": tier
        }

# Singleton
ensemble_model = RiskEnsemble()

def get_ensemble():
    return ensemble_model
