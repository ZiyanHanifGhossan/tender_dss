import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "pipeline.joblib")


def ensure_model_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)


def train_default_pipeline(random_state=42):
    """Train a default pipeline on synthetic data (used as fallback/demo)."""
    np.random.seed(random_state)
    N = 1000
    nilai = np.random.uniform(1, 50, N)        # Rp Miliar (1 - 50)
    durasi = np.random.randint(1, 25, N)      # bulan (1 - 24)
    kompleksitas = np.random.randint(1, 11, N) # 1 - 10
    risiko = np.random.randint(1, 11, N)      # 1 - 10

    X_train = np.column_stack([nilai, durasi, kompleksitas, risiko])

    # Tentukan bobot 'benar' untuk membuat label sintetis (untuk demo)
    true_w = np.array([0.09, -0.05, -0.2, -0.25])
    true_b = -2.0
    logits = X_train.dot(true_w) + true_b
    probs = 1 / (1 + np.exp(-logits))
    # Sampling label berdasarkan probabilitas (membuat distribusi realistik)
    y_train = (probs > np.random.rand(N)).astype(int)

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000))
    ])

    pipeline.fit(X_train, y_train)
    return pipeline


def save_model(path=MODEL_PATH):
    """Save current pipeline to disk."""
    ensure_model_dir()
    global pipeline
    joblib.dump(pipeline, path)


def load_model(path=MODEL_PATH):
    """Load pipeline from disk and set global pipeline."""
    global pipeline
    pipeline = joblib.load(path)
    return pipeline


def is_model_available(path=MODEL_PATH):
    return os.path.exists(path)


# Initialize pipeline: try load from disk, otherwise train default and save
try:
    if is_model_available():
        pipeline = joblib.load(MODEL_PATH)
    else:
        pipeline = train_default_pipeline()
        # save default model so subsequent runs reuse it
        save_model()
except Exception:
    # If anything goes wrong, ensure we still have a trained pipeline in memory
    pipeline = train_default_pipeline()

# alias for backward compatibility
model = pipeline


def predict_win_probability(features, return_details=False):
    """
    features = [nilai_proyek, durasi, kompleksitas, risiko]
    Jika return_details=True, mengembalikan (prob, details_dict) dengan z, sigmoid, dan koefisien (skala asli).
    """
    prob = pipeline.predict_proba([features])[0][1]
    if not return_details:
        return prob

    clf = pipeline.named_steps['clf']
    scaler = pipeline.named_steps['scaler']

    Xs = scaler.transform([features])
    z = clf.decision_function(Xs)[0]
    sigmoid = 1 / (1 + np.exp(-z))

    scaled_coef = clf.coef_[0]
    scaled_intercept = clf.intercept_[0]

    # Konversi koefisien kembali ke skala fitur asli
    # untuk interpretasi: coef_orig = scaled_coef / scaler.scale_
    coef_orig = scaled_coef / scaler.scale_
    intercept_orig = scaled_intercept - np.sum(scaled_coef * scaler.mean_ / scaler.scale_)

    details = {
        'z': float(z),
        'sigmoid': float(sigmoid),
        'probability': float(prob),
        'scaled_coef': scaled_coef.tolist(),
        'scaled_intercept': float(scaled_intercept),
        'coef_orig': coef_orig.tolist(),
        'intercept_orig': float(intercept_orig),
        'scaler_mean': scaler.mean_.tolist(),
        'scaler_scale': scaler.scale_.tolist(),
    }
    return prob, details


def get_model_info():
    clf = pipeline.named_steps['clf']
    scaler = pipeline.named_steps['scaler']
    scaled_coef = clf.coef_[0]
    scaled_intercept = clf.intercept_[0]
    coef_orig = scaled_coef / scaler.scale_
    intercept_orig = scaled_intercept - np.sum(scaled_coef * scaler.mean_ / scaler.scale_)
    return {
        'coef_orig': coef_orig.tolist(),
        'intercept_orig': float(intercept_orig),
        'scaled_coef': scaled_coef.tolist(),
        'scaled_intercept': float(scaled_intercept),
        'scaler_mean': scaler.mean_.tolist(),
        'scaler_scale': scaler.scale_.tolist()
    }


def retrain_from_db(get_labeled_tenders_func, test_size=0.2, random_state=42):
    """Retrain pipeline using labeled data from DB.

    get_labeled_tenders_func should be a callable that returns rows with
    (id, project_name, nilai_proyek, durasi, kompleksitas, risiko, outcome)
    outcome values expected as 'Menang' or 'Kalah'.

    Returns a dict with metrics and saves the trained model to disk.
    """
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix

    rows = get_labeled_tenders_func()
    X = []
    y = []
    for r in rows:
        outcome = r[6]
        if outcome is None:
            continue
        if outcome not in ('Menang', 'Kalah'):
            continue
        X.append([r[2], r[3], r[4], r[5]])
        y.append(1 if outcome == 'Menang' else 0)

    if len(X) == 0:
        return {'error': 'Tidak ada data berlabel untuk retrain.'}

    X = np.array(X)
    y = np.array(y)

    if len(np.unique(y)) < 2:
        return {'error': 'Hanya terdapat satu kelas pada data berlabel. Butuh setidaknya satu contoh dari kedua kelas (Menang dan Kalah).'}

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)

    new_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000))
    ])

    new_pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = new_pipeline.predict(X_test)
    y_prob = new_pipeline.predict_proba(X_test)[:, 1]
    acc = float(accuracy_score(y_test, y_pred))
    try:
        auc = float(roc_auc_score(y_test, y_prob))
    except Exception:
        auc = None
    cm = confusion_matrix(y_test, y_pred).tolist()

    # Save model
    global pipeline
    pipeline = new_pipeline
    save_model()

    metrics = {
        'n_samples': int(len(y)),
        'n_train': int(len(y_train)),
        'n_test': int(len(y_test)),
        'accuracy': acc,
        'auc': auc,
        'confusion_matrix': cm
    }
    return metrics
