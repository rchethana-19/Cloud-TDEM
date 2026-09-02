from datetime import datetime

from major_project.feature_extractor import extract_features
from major_project.risk_engine import calculate_risk
from major_project.explain import generate_explanation


def evaluate_request(request_data):

    features = extract_features(request_data)

    risk = calculate_risk(features)

    explanation = generate_explanation(
        features,
        risk["decision"]
    )

    return {

        "status": "success",

        "timestamp": datetime.utcnow().isoformat(),

        "risk_score": risk["risk_score"],

        "decision": risk["decision"],

        "model": "Isolation Forest",

        "reasons": explanation["reasons"]

    }