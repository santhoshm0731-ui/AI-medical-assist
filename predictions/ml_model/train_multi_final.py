# predictions/ml_model/train_multi_final.py
import os
import glob
import random
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight

# ----------------- CONFIG -----------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(BASE_DIR, 'predictions', 'data')   # CSVs should be here
OUT_DIR = os.path.join(BASE_DIR, 'predictions', 'ml_model')
os.makedirs(OUT_DIR, exist_ok=True)

MODEL_PATH = os.path.join(OUT_DIR, 'disease_model.h5')
SCALER_PATH = os.path.join(OUT_DIR, 'scaler.pkl')
LABEL_ENCODER_PATH = os.path.join(OUT_DIR, 'label_encoder.pkl')

# Adjust these hyperparameters if you want
HIDDEN_UNITS = [1024, 512, 256, 128]
DROPOUT = 0.4
LR = 1e-3
BATCH_SIZE = 64
EPOCHS = 120
PATIENCE = 12
VAL_FRACTION = 0.1111   # results in ~10% test, ~10% val (see splitting below)

# Symptom columns MUST match the CSV generator
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
# ------------------------------------------

def load_all_csvs(folder):
    files = sorted(glob.glob(os.path.join(folder, '*.csv')))
    if not files:
        raise RuntimeError(f"No CSV files found in {folder}. Put your CSVs there (e.g. disease_data_2500_part1.csv).")
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        dfs.append(df)
        print("Loaded:", f, "rows:", len(df))
    data = pd.concat(dfs, ignore_index=True)
    print("Total rows after concat:", len(data))
    return data

def build_model(input_dim, n_classes):
    inputs = keras.Input(shape=(input_dim,), name='symptoms')
    x = layers.BatchNormalization()(inputs)
    for units in HIDDEN_UNITS:
        x = layers.Dense(units, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(DROPOUT)(x)
    outputs = layers.Dense(n_classes, activation='softmax', name='disease_out')(x)
    model = keras.Model(inputs, outputs, name='disease_mlp')
    opt = keras.optimizers.Adam(learning_rate=LR)
    model.compile(optimizer=opt, loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

def main():
    print("Reading CSVs from:", DATA_DIR)
    df = load_all_csvs(DATA_DIR)

    # Validate symptom columns exist
    missing = [c for c in SYMPTOMS if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing symptom columns in CSVs: {missing}")

    if 'disease' not in df.columns:
        raise RuntimeError("CSV files must contain a 'disease' column as the target label.")

    X = df[SYMPTOMS].astype(float).values
    y = df['disease'].astype(str).values

    print("X shape:", X.shape, "n_samples:", X.shape[0])
    # encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    classes = le.classes_
    print("Detected classes (n):", len(classes))
    print(classes)

    # Split: first test, then train/val
    X_trainval, X_test, y_trainval, y_test = train_test_split(X, y_enc, test_size=0.10, random_state=SEED, stratify=y_enc)
    val_frac_of_trainval = VAL_FRACTION / (1.0 - 0.10)
    X_train, X_val, y_train, y_val = train_test_split(X_trainval, y_trainval, test_size=val_frac_of_trainval, random_state=SEED, stratify=y_trainval)

    print("Train/Val/Test shapes:", X_train.shape, X_val.shape, X_test.shape)

    # Scale features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)

    # class weights to mitigate imbalance
    classes_unique = np.unique(y_train)
    class_weights = compute_class_weight(class_weight='balanced', classes=classes_unique, y=y_train)
    class_weight_dict = {int(c): float(w) for c, w in zip(classes_unique, class_weights)}
    print("Using class weights:", class_weight_dict)

    # build & train model
    model = build_model(input_dim=X_train.shape[1], n_classes=len(classes))
    model.summary()

    callbacks = [
        keras.callbacks.EarlyStopping(monitor='val_loss', patience=PATIENCE, restore_best_weights=True, verbose=1),
        keras.callbacks.ModelCheckpoint(MODEL_PATH, monitor='val_loss', save_best_only=True, verbose=1),
        keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=6, verbose=1)
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        class_weight=class_weight_dict,
        verbose=2
    )

    # evaluate
    print("Evaluating on test set...")
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"Test accuracy: {test_acc:.4f}  Test loss: {test_loss:.4f}")

    # predictions and metrics
    y_pred_probs = model.predict(X_test)
    y_pred = np.argmax(y_pred_probs, axis=1)

    print("Classification report:")
    print(classification_report(y_test, y_pred, target_names=classes))
    print("Confusion matrix (rows=true, cols=pred):")
    print(confusion_matrix(y_test, y_pred))

    # Save artifacts
    print("Saving model and artifacts...")
    model.save(MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(le, LABEL_ENCODER_PATH)
    print("Saved model ->", MODEL_PATH)
    print("Saved scaler ->", SCALER_PATH)
    print("Saved label encoder ->", LABEL_ENCODER_PATH)

if __name__ == "__main__":
    main()
