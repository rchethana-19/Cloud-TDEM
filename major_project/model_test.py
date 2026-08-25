import joblib

model = joblib.load("model.pkl")

print("Model Loaded Successfully!")

print(type(model))