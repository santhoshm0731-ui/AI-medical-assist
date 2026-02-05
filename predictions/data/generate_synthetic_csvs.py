import os, random, pandas as pd, numpy as np

random.seed(123)
np.random.seed(123)

BASE = os.path.join(os.path.dirname(__file__))
OUT_DIR = BASE
os.makedirs(OUT_DIR, exist_ok=True)

# Full symptom list (broader coverage)
SYMPTOMS = [
    "fever","chills","sweating","cough","sore_throat","runny_nose","nasal_congestion",
    "shortness_of_breath","wheezing","chest_pain","fatigue","weakness","headache",
    "migraine_like_pain","dizziness","nausea","vomiting","diarrhea","abdominal_pain",
    "loss_of_appetite","body_pain","joint_pain","muscle_ache","rash","itching",
    "eye_redness","loss_of_taste_or_smell","urinary_frequency","burning_urination",
    "bleeding","sweeling_limbs","back_pain","constipation","anxiety","depression",
    "memory_loss","sleep_disturbance","blurred_vision","ear_pain","skin_peeling",
    "sensitivity_to_light","dehydration","palpitations","chest_tightness"
]

# Expanded disease list
DISEASES = [
    "Flu","Common Cold","COVID-19","Gastroenteritis","Dengue","Malaria",
    "Pneumonia","Strep Throat","Migraine","Urinary Tract Infection","Allergy",
    "Asthma","Bronchitis","Hypertension","Diabetes","Anemia","Arthritis",
    "Chickenpox","Measles","Sinusitis","Tuberculosis","Tonsillitis","Anxiety Disorder",
    "Depression","Skin Infection","Eye Infection","Ear Infection","Heart Disease",
    "Kidney Infection","Food Poisoning","Appendicitis","Chronic Fatigue Syndrome"
]

# Symptom probability map per disease
disease_common = {
    "Flu": {"high":["fever","cough","fatigue","headache","body_pain"], "mid":["sore_throat","chills","sweating"]},
    "Common Cold": {"high":["cough","sore_throat","runny_nose","nasal_congestion"], "mid":["headache","fatigue"]},
    "COVID-19": {"high":["fever","cough","fatigue","loss_of_taste_or_smell","shortness_of_breath"], "mid":["headache","sore_throat"]},
    "Gastroenteritis": {"high":["nausea","vomiting","diarrhea","abdominal_pain"], "mid":["loss_of_appetite","weakness"]},
    "Dengue": {"high":["fever","body_pain","headache","rash"], "mid":["nausea","weakness"]},
    "Malaria": {"high":["fever","chills","sweating","weakness"], "mid":["headache","nausea"]},
    "Pneumonia": {"high":["fever","cough","shortness_of_breath","chest_pain"], "mid":["fatigue"]},
    "Strep Throat": {"high":["sore_throat","fever","headache"], "mid":["loss_of_appetite"]},
    "Migraine": {"high":["headache","migraine_like_pain","nausea","dizziness"], "mid":[]},
    "Urinary Tract Infection": {"high":["urinary_frequency","burning_urination","loss_of_appetite"], "mid":["fever"]},
    "Allergy": {"high":["runny_nose","nasal_congestion","itching","eye_redness"], "mid":["sore_throat"]},
    "Asthma": {"high":["wheezing","shortness_of_breath","chest_tightness"], "mid":["cough","fatigue"]},
    "Bronchitis": {"high":["cough","wheezing","chest_pain"], "mid":["fatigue","shortness_of_breath"]},
    "Hypertension": {"high":["headache","dizziness","fatigue"], "mid":["chest_pain","palpitations"]},
    "Diabetes": {"high":["fatigue","weakness","frequent_urination"], "mid":["blurred_vision","dehydration"]},
    "Anemia": {"high":["fatigue","weakness","dizziness"], "mid":["pale_skin","shortness_of_breath"]},
    "Arthritis": {"high":["joint_pain","swelling","stiffness"], "mid":["fatigue","body_pain"]},
    "Chickenpox": {"high":["fever","rash","itching"], "mid":["fatigue"]},
    "Measles": {"high":["rash","fever","runny_nose","eye_redness"], "mid":["cough","sore_throat"]},
    "Sinusitis": {"high":["headache","nasal_congestion","facial_pain"], "mid":["fever","fatigue"]},
    "Tuberculosis": {"high":["cough","fever","weight_loss"], "mid":["fatigue","night_sweats"]},
    "Tonsillitis": {"high":["sore_throat","fever","difficulty_swallowing"], "mid":["fatigue"]},
    "Anxiety Disorder": {"high":["anxiety","palpitations","sleep_disturbance"], "mid":["fatigue"]},
    "Depression": {"high":["depression","fatigue","sleep_disturbance"], "mid":["loss_of_appetite"]},
    "Skin Infection": {"high":["rash","itching","skin_peeling"], "mid":["fever"]},
    "Eye Infection": {"high":["eye_redness","itching","blurred_vision"], "mid":["pain"]},
    "Ear Infection": {"high":["ear_pain","fever","hearing_loss"], "mid":["headache"]},
    "Heart Disease": {"high":["chest_pain","palpitations","shortness_of_breath"], "mid":["fatigue","weakness"]},
    "Kidney Infection": {"high":["fever","back_pain","burning_urination"], "mid":["nausea","fatigue"]},
    "Food Poisoning": {"high":["vomiting","diarrhea","abdominal_pain"], "mid":["fever","weakness"]},
    "Appendicitis": {"high":["abdominal_pain","nausea","fever"], "mid":["loss_of_appetite"]},
    "Chronic Fatigue Syndrome": {"high":["fatigue","muscle_ache","sleep_disturbance"], "mid":["memory_loss","weakness"]},
}

def make_probs(common_symptoms, base=0.01, high=0.8, mid=0.4):
    probs = {s: base for s in SYMPTOMS}
    for s in common_symptoms.get('high', []):
        probs[s] = high
    for s in common_symptoms.get('mid', []):
        probs[s] = mid
    return probs

disease_symptom_probs = {d: make_probs(disease_common.get(d, {})) for d in DISEASES}

def generate_rows(n_rows=2500):
    rows = []
    proportions = np.random.dirichlet(np.ones(len(DISEASES)), size=1)[0]
    counts = {d: max(1, int(n_rows * p)) for d,p in zip(DISEASES, proportions)}
    diff = n_rows - sum(counts.values())
    counts[DISEASES[0]] += diff
    for dis in DISEASES:
        prob_map = disease_symptom_probs.get(dis, {})
        for _ in range(counts[dis]):
            sample = {"disease": dis}
            for s in SYMPTOMS:
                p = prob_map.get(s, 0.01)
                sample[s] = 1 if random.random() < p else 0
            if sum(sample[s] for s in SYMPTOMS) < 2:
                common = disease_common.get(dis, {"high":[]})["high"][:2]
                for s in common:
                    sample[s] = 1
            rows.append(sample)
    random.shuffle(rows)
    df = pd.DataFrame(rows)
    return df

if __name__ == "__main__":
    for idx in range(1,4):
        df = generate_rows(2500)
        out = os.path.join(OUT_DIR, f"disease_data_2500_part{idx}.csv")
        df.to_csv(out, index=False)
        print(f"Wrote {out} → {df.shape[0]} rows, {len(SYMPTOMS)} features, {len(DISEASES)} diseases")
