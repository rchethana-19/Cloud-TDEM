import pandas as pd
import joblib

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

# -----------------------------
# Load Dataset
# -----------------------------

df = pd.read_csv("dataset.csv")

print("Dataset Loaded Successfully!")
print(df.head())

# -----------------------------
# Encode Categorical Features
# -----------------------------

label_encoders = {}

categorical_columns = [
    "country",
    "browser",
    "file_sensitivity"
]

for col in categorical_columns:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    label_encoders[col] = le

# Remove label column before training
X = df.drop(columns=["label"])

# -----------------------------
# Train Isolation Forest
# -----------------------------

model = IsolationForest(
    n_estimators=100,
    contamination=0.10,
    random_state=42
)

model.fit(X)

print("\nModel Trained Successfully!")

# -----------------------------
# Predict Anomalies
# -----------------------------

predictions = model.predict(X)

df["prediction"] = predictions

normal = (predictions == 1).sum()
anomaly = (predictions == -1).sum()

print("\nPrediction Summary")
print("---------------------")
print("Normal Records :", normal)
print("Anomalies      :", anomaly)

# -----------------------------
# Save Model
# -----------------------------

joblib.dump(model, "model.pkl")

print("\nModel saved as model.pkl")