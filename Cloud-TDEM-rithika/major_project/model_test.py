from pathlib import Path

import joblib

MODEL_PATH = Path(__file__).resolve().with_name("model.pkl")
model = joblib.load(MODEL_PATH)

print("Model Loaded Successfully!")

print(type(model))