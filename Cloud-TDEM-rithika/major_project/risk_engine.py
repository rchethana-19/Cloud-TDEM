
from pathlib import Path

import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# ----------------------------
# Load trained model once
# ----------------------------

MODEL_PATH = Path(__file__).resolve().with_name("model.pkl")
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"AI model not found at {MODEL_PATH}. Train the model first.")

model = joblib.load(MODEL_PATH)

print("AI Risk Model Loaded Successfully!")
# -----------------------------
# Label Encoders
# -----------------------------

country_encoder = LabelEncoder()
country_encoder.fit(["India", "USA", "Germany", "UK", "Canada", "Unknown", "Russia", "China"])

browser_encoder = LabelEncoder()
browser_encoder.fit(["Chrome", "Firefox", "Edge", "Safari"])

sensitivity_encoder = LabelEncoder()
sensitivity_encoder.fit(["Low", "Medium", "High"])


# -----------------------------
# Risk Evaluation Function
# -----------------------------

def calculate_risk(features):

    df = pd.DataFrame([features])

    df["country"] = country_encoder.transform(df["country"])
    df["browser"] = browser_encoder.transform(df["browser"])
    df["file_sensitivity"] = sensitivity_encoder.transform(df["file_sensitivity"])

    prediction = model.predict(df)[0]

    score = model.decision_function(df)[0]

    # Convert score into a simple 0–1 risk score
    risk_score = max(0, min(1, 0.5 - score))

    if risk_score < 0.30:
        decision = "ALLOW"

    elif risk_score < 0.70:
        decision = "REQUIRE_MFA"

    else:
        decision = "DENY"

    return {
    "risk_score": float(round(risk_score, 2)),
    "decision": decision
    }