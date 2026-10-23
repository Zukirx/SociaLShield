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
            s_fact, cred, diff, senti = features
            if s_fact <= 0.20:
                # Refuted / Fake claim: High to Critical risk regardless of diffusion
                risk = 0.82 + (0.20 - s_fact) * 0.5 + diff * 0.12 + (1.0 - cred) * 0.05
                return min(float(risk), 0.98)
            elif s_fact <= 0.40:
                # Unverified / Disputed claim
                risk = 0.60 + (0.40 - s_fact) * 0.4 + diff * 0.20 + (1.0 - cred) * 0.10
                return min(float(risk), 0.88)
            elif s_fact >= 0.70:
                # Verified factual claim: Low risk
                risk = (1.0 - s_fact) * 0.3 + (1.0 - cred) * 0.15 + diff * 0.15
                return max(float(risk), 0.05)
            else:
                risk = (1.0 - s_fact) * 0.45 + (1.0 - cred) * 0.25 + diff * 0.30
                return float(risk)
            
        return float(self.model.predict_proba(np.array([features]))[0][1])
        
    def assess_risk(self, s_fact: float, user_credibility: float, diffusion_risk: float, sentiment_subj: float = 0.5, verdict: str = ""):
        features = [s_fact, user_credibility, diffusion_risk, sentiment_subj]
        risk_score = self.predict_proba(features)
        
        tier = "Low"
        if verdict == "FAKE" or risk_score >= 0.80 or s_fact <= 0.15:
            tier = "Critical"
            risk_score = max(risk_score, 0.88)
        elif verdict == "MISLEADING" or risk_score >= 0.60 or s_fact <= 0.35:
            tier = "High"
            risk_score = max(risk_score, 0.65)
        elif risk_score >= 0.40 or s_fact < 0.65:
            tier = "Medium"
            
        return {
            "risk_score": round(risk_score, 4),
            "tier": tier
        }

# Singleton
ensemble_model = RiskEnsemble()

def get_ensemble():
    return ensemble_model
