# predictions/views.py
import glob
import os
import joblib
import numpy as np
import tensorflow as tf
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
import os, joblib, tensorflow as tf, pandas as pd, numpy as np
from django.conf import settings
from analytics.models import HealthRecord


# === Paths ===
# === Paths ===
MODEL_H5 = os.path.join(settings.BASE_DIR, 'predictions', 'ml_model', 'disease_model.h5')
LABEL_PKL = os.path.join(settings.BASE_DIR, 'predictions', 'ml_model', 'label_encoder.pkl')
SCALER_PKL = os.path.join(settings.BASE_DIR, 'predictions', 'ml_model', 'scaler.pkl')
DATA_FOLDER = os.path.join(settings.BASE_DIR, 'predictions', 'data')

# === Load model and preprocessors ===
_model, _scaler, _label_encoder, SYMPTOMS = None, None, None, []

def load_artifacts():
    """Load model, scaler, encoder, and symptoms from CSV with auto feature alignment."""
    global _model, _scaler, _label_encoder, SYMPTOMS
    if _model and _scaler and _label_encoder and SYMPTOMS:
        return _model, _scaler, _label_encoder, SYMPTOMS

    # Load artifacts
    _model = tf.keras.models.load_model(MODEL_H5)
    _scaler = joblib.load(SCALER_PKL)
    _label_encoder = joblib.load(LABEL_PKL)

    # Load symptoms from first CSV
    files = sorted(glob.glob(os.path.join(DATA_FOLDER, "*.csv")))
    if not files:
        raise FileNotFoundError("No CSV found in predictions/data/")
    df = pd.read_csv(files[0])
    SYMPTOMS = [c for c in df.columns if c != "disease"]

    # Align features with model input
    expected_features = getattr(_scaler, "n_features_in_", len(SYMPTOMS))
    if len(SYMPTOMS) > expected_features:
        print(f"[WARN] Trimming {len(SYMPTOMS) - expected_features} extra symptoms.")
        SYMPTOMS = SYMPTOMS[:expected_features]
    elif len(SYMPTOMS) < expected_features:
        print(f"[WARN] Padding with {expected_features - len(SYMPTOMS)} placeholder features.")
        while len(SYMPTOMS) < expected_features:
            SYMPTOMS.append(f"feature_{len(SYMPTOMS)+1}")

    return _model, _scaler, _label_encoder, SYMPTOMS

# === Disease Information ===
# Covers all 32 diseases from your dataset
DISEASE_INFO = {
    "Allergy": {
        "causes": ["Exposure to allergens (dust, pollen, pet dander, etc.)"],
        "prevention": ["Avoid known allergens", "Keep windows closed during pollen season"],
        "dos": ["Use prescribed antihistamines", "Stay hydrated", "Shower after exposure"],
        "donts": ["Do not ignore breathing difficulty", "Avoid strong perfumes or smoke"],
        "home_remedies": ["Saline nasal rinse", "Steam inhalation", "Cool compress for itchy eyes"]
    },
    "Anemia": {
        "causes": ["Iron deficiency", "Vitamin B12 or folate deficiency"],
        "prevention": ["Eat iron-rich foods", "Take supplements if prescribed"],
        "dos": ["Include leafy greens, meat, beans, and vitamin C"],
        "donts": ["Avoid skipping meals", "Do not self-medicate iron"],
        "home_remedies": ["Spinach, dates, pomegranate, and jaggery help boost hemoglobin"]
    },
    "Anxiety Disorder": {
        "causes": ["Stress, trauma, chemical imbalance, genetics"],
        "prevention": ["Stress management", "Sleep hygiene", "Therapy"],
        "dos": ["Practice meditation, exercise regularly"],
        "donts": ["Avoid caffeine and alcohol", "Don't isolate yourself"],
        "home_remedies": ["Deep breathing, herbal teas like chamomile, journaling"]
    },
    "Appendicitis": {
        "causes": ["Infection or obstruction of appendix"],
        "prevention": ["No known prevention — prompt diagnosis is key"],
        "dos": ["Seek immediate medical help if pain worsens"],
        "donts": ["Do not self-treat or ignore severe abdominal pain"],
        "home_remedies": ["None — medical attention is essential"]
    },
    "Arthritis": {
        "causes": ["Joint inflammation due to wear, infection, or autoimmune causes"],
        "prevention": ["Maintain healthy weight", "Stay active"],
        "dos": ["Gentle exercises, warm compresses"],
        "donts": ["Avoid overexertion", "Do not skip medications"],
        "home_remedies": ["Turmeric milk, hot baths, omega-3 rich diet"]
    },
    "Asthma": {
        "causes": ["Inflammation of airways triggered by allergens or pollution"],
        "prevention": ["Avoid dust, smoke, and strong odors"],
        "dos": ["Use inhalers regularly as prescribed"],
        "donts": ["Do not stop medication abruptly"],
        "home_remedies": ["Steam inhalation, ginger tea, avoid cold air"]
    },
    "Bronchitis": {
        "causes": ["Viral or bacterial infection of airways"],
        "prevention": ["Avoid smoking, cold air, and pollution"],
        "dos": ["Drink fluids, use humidifier, rest"],
        "donts": ["Avoid smoking or irritants"],
        "home_remedies": ["Honey, turmeric milk, steam therapy"]
    },
    "COVID-19": {
        "causes": ["SARS-CoV-2 virus infection"],
        "prevention": ["Masking, hand hygiene, vaccination"],
        "dos": ["Isolate, monitor oxygen, consult doctor if severe"],
        "donts": ["Avoid public contact if symptomatic"],
        "home_remedies": ["Steam inhalation, warm fluids, zinc and vitamin C-rich diet"]
    },
    "Chickenpox": {
        "causes": ["Varicella-zoster virus"],
        "prevention": ["Vaccination"],
        "dos": ["Rest, keep hydrated, cool baths"],
        "donts": ["Avoid scratching lesions"],
        "home_remedies": ["Oatmeal baths, calamine lotion, neem leaves"]
    },
    "Chronic Fatigue Syndrome": {
        "causes": ["Unknown; linked to viral infections and immune issues"],
        "prevention": ["Healthy lifestyle, stress management"],
        "dos": ["Rest, gradual physical activity"],
        "donts": ["Avoid overexertion"],
        "home_remedies": ["Balanced nutrition, meditation"]
    },
    "Common Cold": {
        "causes": ["Rhinovirus infection"],
        "prevention": ["Wash hands often", "Avoid crowds"],
        "dos": ["Hydrate, rest, vitamin C intake"],
        "donts": ["Avoid antibiotics"],
        "home_remedies": ["Honey, ginger tea, salt-water gargle"]
    },
    "Dengue": {
        "causes": ["Dengue virus via Aedes mosquitoes"],
        "prevention": ["Avoid mosquito bites", "Remove stagnant water"],
        "dos": ["Hydration, rest, monitor for warning signs"],
        "donts": ["Avoid painkillers like aspirin or ibuprofen"],
        "home_remedies": ["Papaya leaf juice, coconut water, fluids"]
    },
    "Depression": {
        "causes": ["Chemical imbalance, trauma, chronic stress"],
        "prevention": ["Therapy, social interaction, sleep hygiene"],
        "dos": ["Stay connected, exercise, seek help"],
        "donts": ["Avoid alcohol and isolation"],
        "home_remedies": ["Sunlight, journaling, omega-3 foods"]
    },
    "Diabetes": {
        "causes": ["Insulin resistance or deficiency"],
        "prevention": ["Healthy diet, weight control"],
        "dos": ["Monitor blood sugar regularly"],
        "donts": ["Avoid sugary and processed foods"],
        "home_remedies": ["Bitter gourd juice, fenugreek water"]
    },
    "Flu": {
        "causes": ["Influenza virus"],
        "prevention": ["Flu shot, hygiene"],
        "dos": ["Rest, hydration, fever control"],
        "donts": ["Avoid going out while sick"],
        "home_remedies": ["Warm soups, steam inhalation"]
    },
    "Gastroenteritis": {
        "causes": ["Viral/bacterial infection from contaminated food or water"],
        "prevention": ["Hand hygiene, clean water"],
        "dos": ["ORS, hydration, bland diet"],
        "donts": ["Avoid dairy or oily foods"],
        "home_remedies": ["Coconut water, ginger tea, banana"]
    },
    "Hypertension": {
        "causes": ["Genetic, lifestyle, stress"],
        "prevention": ["Exercise, reduce salt"],
        "dos": ["Monitor BP, take medications regularly"],
        "donts": ["Avoid salty food and alcohol"],
        "home_remedies": ["Garlic, hibiscus tea, meditation"]
    },
    "Migraine": {
        "causes": ["Neurological triggers like stress, dehydration, hormones"],
        "prevention": ["Identify and avoid triggers"],
        "dos": ["Rest, hydration, pain management"],
        "donts": ["Avoid caffeine excess and bright lights"],
        "home_remedies": ["Cold compress, peppermint oil, quiet room"]
    },
    "Pneumonia": {
        "causes": ["Bacterial or viral infection of lungs"],
        "prevention": ["Vaccination, hygiene"],
        "dos": ["Rest, antibiotics if prescribed"],
        "donts": ["Avoid smoking and cold exposure"],
        "home_remedies": ["Steam, ginger tea, fluids"]
    },
    "Tuberculosis": {
        "causes": ["Mycobacterium tuberculosis infection"],
        "prevention": ["BCG vaccine, early detection"],
        "dos": ["Complete TB treatment course"],
        "donts": ["Avoid stopping meds early"],
        "home_remedies": ["Nutrient-rich foods, sunlight exposure"]
    },
    "Unknown": {
        "causes": ["Unclear symptom combination"],
        "prevention": ["General hygiene, healthy habits"],
        "dos": ["Consult a doctor"],
        "donts": ["Avoid self-diagnosis"],
        "home_remedies": ["Rest, fluids, balanced diet"]
    }
}


def predict_disease(request):
    model, scaler, label_encoder, SYMPTOMS = load_artifacts()

    if request.method == "POST":
        # Read 5 dropdowns (user may leave some blank)
        raw = [
            request.POST.get("symptom1"),
            request.POST.get("symptom2"),
            request.POST.get("symptom3"),
            request.POST.get("symptom4"),
            request.POST.get("symptom5"),
        ]
        selected = [s for s in raw if s and s.strip() != ""]
        selected = list(dict.fromkeys(selected))  # dedupe, preserve order

        if len(selected) < 2:
            messages.error(request, "Please select at least 2 different symptoms.")
            return render(request, "predictions/predict.html", {"symptoms": SYMPTOMS})

        # Build binary feature vector
        x = np.zeros((1, len(SYMPTOMS)))
        for s in selected:
            if s in SYMPTOMS:
                x[0, SYMPTOMS.index(s)] = 1

        # Align features if necessary
        if x.shape[1] > scaler.n_features_in_:
            x = x[:, :scaler.n_features_in_]
        elif x.shape[1] < scaler.n_features_in_:
            pad = np.zeros((1, scaler.n_features_in_ - x.shape[1]))
            x = np.concatenate([x, pad], axis=1)

        # Predict
        x_scaled = scaler.transform(x)
        probs = model.predict(x_scaled)
        idx = int(np.argmax(probs))
        label = label_encoder.inverse_transform([idx])[0]
        confidence = float(np.max(probs))

        info = DISEASE_INFO.get(label, DISEASE_INFO["Unknown"])

        context = {
            "predicted": label,
            "confidence": round(confidence * 100, 2),
            "selected_symptoms": selected,
            "info": info,
            "symptoms": SYMPTOMS,
        }
        return render(request, "predictions/result.html", context)

    return render(request, "predictions/predict.html", {"symptoms": SYMPTOMS})



# ==== Manage Health ====
from analytics.models import HealthRecord
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages

@login_required
def manage_health(request):
    """Allows patient to input health data, calculate BMI, and save to analytics."""
    if request.method == 'POST':
        weight = request.POST.get('weight')
        height = request.POST.get('height')
        bp = request.POST.get('bp')
        sugar = request.POST.get('sugar')
        heartrate = request.POST.get('heartrate')
        oxygen = request.POST.get('oxygen')

        bmi = None
        try:
            if weight and height:
                bmi = round(float(weight) / ((float(height) / 100) ** 2), 2)
        except Exception:
            messages.error(request, "Invalid height or weight values.")
            bmi = None

        # Save the record to database
        try:
            HealthRecord.objects.create(
                user=request.user,
                weight_kg=float(weight) if weight else None,
                height_cm=float(height) if height else None,
                bmi=bmi,
                bp=bp or None,
                sugar=float(sugar) if sugar else None,
                heartrate=float(heartrate) if heartrate else None,
                oxygen=float(oxygen) if oxygen else None
            )
            messages.success(request, "✅ Health data saved successfully!")
        except Exception as e:
            messages.error(request, f"⚠️ Could not save data: {e}")

        return render(request, 'predictions/manage_health.html', {
            'bmi': bmi,
            'weight': weight,
            'height': height,
            'bp': bp,
            'sugar': sugar,
            'heartrate': heartrate,
            'oxygen': oxygen,
            'success': True
        })

    return render(request, 'predictions/manage_health.html')
