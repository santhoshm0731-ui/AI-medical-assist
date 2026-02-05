import os, joblib, tensorflow as tf, pandas as pd, numpy as np
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medassist.settings")



import django
django.setup()

# === Paths ===
MODEL_H5 = os.path.join(settings.BASE_DIR, 'predictions', 'ml_model', 'disease_model.h5')
LABEL_PKL = os.path.join(settings.BASE_DIR, 'predictions', 'ml_model', 'label_encoder.pkl')
SCALER_PKL = os.path.join(settings.BASE_DIR, 'predictions', 'ml_model', 'scaler.pkl')
DATA_PATH = os.path.join(settings.BASE_DIR, 'predictions', 'data', 'disease_data_2500_part1.csv')

# === Helper to load artifacts ===
def load_artifacts():
    model = tf.keras.models.load_model(MODEL_H5)
    scaler = joblib.load(SCALER_PKL)
    label_encoder = joblib.load(LABEL_PKL)

    df = pd.read_csv(DATA_PATH)
    symptoms = [c for c in df.columns if c != 'disease']

    expected_features = getattr(scaler, 'n_features_in_', len(symptoms))
    if len(symptoms) > expected_features:
        print(f"[WARN] Trimming {len(symptoms) - expected_features} extra symptoms to match model input ({expected_features}).")
        symptoms = symptoms[:expected_features]
    elif len(symptoms) < expected_features:
        print(f"[WARN] Padding with {expected_features - len(symptoms)} zeros.")
        while len(symptoms) < expected_features:
            symptoms.append(f"feature_{len(symptoms)+1}")

    return model, scaler, label_encoder, symptoms


# === Load ===
model, scaler, le, SYMPTOMS = load_artifacts()
print("✅ Model, Scaler, and Label Encoder loaded.")
print("✅ Symptom count:", len(SYMPTOMS))

# === Predict manually ===
selected = ["fever", "cough", "fatigue", "sore_throat"]

x = np.zeros((1, len(SYMPTOMS)))
for s in selected:
    if s in SYMPTOMS:
        x[0, SYMPTOMS.index(s)] = 1

# Fix mismatch
if x.shape[1] > scaler.n_features_in_:
    x = x[:, :scaler.n_features_in_]
elif x.shape[1] < scaler.n_features_in_:
    pad = np.zeros((1, scaler.n_features_in_ - x.shape[1]))
    x = np.concatenate([x, pad], axis=1)

x_scaled = scaler.transform(x)
pred = model.predict(x_scaled)
label = le.inverse_transform([np.argmax(pred)])[0]

print("🩺 Predicted:", label)
print("📊 Confidence:", round(float(np.max(pred)) * 100, 2), "%")
