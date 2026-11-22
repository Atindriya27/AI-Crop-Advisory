import json
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from .config import DATASET_PATH, FEATURES, MODEL_PATH, METADATA_PATH
from .preprocessing import load_dataset

def train(dataset_path=DATASET_PATH):
    df = load_dataset(dataset_path)
    X, y = df[FEATURES], df.label
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_accuracy = cross_val_score(
        RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced", n_jobs=-1),
        X, y, cv=cv, scoring="accuracy",
    )
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced", n_jobs=-1)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, pred, average="weighted", zero_division=0)
    metadata = {"dataset": Path(dataset_path).name, "samples": int(len(df)), "features": FEATURES,
                "classes": sorted(y.unique().tolist()), "split": "80/20 stratified", "random_state": 42,
                "feature_ranges": {feature: {"min": float(X[feature].min()), "max": float(X[feature].max())} for feature in FEATURES},
                "cross_validation": {"method": "5-fold stratified", "accuracy_mean": float(cv_accuracy.mean()),
                                     "accuracy_std": float(cv_accuracy.std()), "fold_scores": cv_accuracy.tolist()},
                "accuracy": accuracy_score(y_test, pred), "precision_weighted": precision,
                "recall_weighted": recall, "f1_weighted": f1,
                "confusion_matrix": confusion_matrix(y_test, pred, labels=sorted(y.unique())).tolist(),
                "class_labels": sorted(y.unique().tolist()), "classification_report": classification_report(y_test, pred, output_dict=True, zero_division=0),
                "feature_importance": dict(zip(FEATURES, model.feature_importances_.tolist()))}
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata

if __name__ == "__main__":
    print(json.dumps(train(), indent=2))
