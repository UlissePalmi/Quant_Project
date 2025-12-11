import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeRegressor, export_text
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

from xgboost import XGBRegressor

df = pd.read_csv("merged_dataset.csv")

for col in ["date_a", "date_b", "start_anchor", "end_anchor"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

# ===== 2) Feature engineering =====
# similarity threshold: auto-detect units (0-1 vs 0-100)
sim_max = df["similarity"].replace([np.inf, -np.inf], np.nan).dropna().max()
sim_threshold = 0.70 if sim_max <= 1.5 else 70.0
df["sim_below_70"] = (df["similarity"] < sim_threshold).astype(int)

# sentiment sign: 1 if >= 0 else 0 (you can flip to {-1,1} if you prefer)
df["sentiment_pos"] = (df["sentiment"] >= 0).astype(int)
df["len_growth_pct"] = df['len_a'] / df['len_b'] - 1
df["inc_len"] = df["len_a"] > df["len_b"]
df['sim_sum'] = df['sentiment'] + df['old_similarity']

df_clf = df.copy()

# 2) Create 5 classes from ret_18 (very_negative ... very_positive)
labels = [
    "very_negative",
    "negative",
    "flat",
    "positive",
    "very_positive"
]

# Drop rows with missing ret_18 first
df_clf = df_clf.dropna(subset=["ret_18"])

df_clf["ret_18_bucket"] = pd.qcut(
    df_clf["ret_18"],
    q=5,
    labels=labels
)

# Integer class labels 0..4
df_clf["ret_18_class"] = df_clf["ret_18_bucket"].cat.codes

# 3) Features X and classification target y
feature_cols = [
    "similarity",
    "sim_below_70",
    "sentiment",
    "sentiment_pos",
    "inc_len",
    "len_growth_pct",
    "old_similarity",
    "ret_prev_12m",
]

X = df_clf[feature_cols].copy()
y = df_clf["ret_18_class"].copy()

# 4) Drop rows with missing values in features/target
mask = X.notna().all(axis=1) & y.notna()
X = X[mask]
y = y[mask]

# Keep aligned dates / df for later use
dates = pd.to_datetime(df_clf.loc[mask, "date_a"])
df_clf = df_clf[mask]

import matplotlib.pyplot as plt

# Use the continuous target, not the class
ret = df['ret_18'].dropna()

plt.figure(figsize=(8, 5))
plt.hist(ret, bins=1000)  # adjust bins as needed
plt.xlabel("18-month return (ret_18)")
plt.ylabel("Frequency")
plt.title("Distribution of 18-month returns")
plt.tight_layout()
plt.show()



X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    shuffle=True,
    random_state=42,
    stratify=y  # important: preserve class proportions
)

# Random Forest classifier
rf_clf = RandomForestClassifier(
    n_estimators=300,
    max_depth=6,
    min_samples_leaf=200,
    n_jobs=-1,
    random_state=42
)

rf_clf.fit(X_train, y_train)

# Predictions on test set
y_pred = rf_clf.predict(X_test)
y_proba = rf_clf.predict_proba(X_test)  # class probabilities if you need them

# Basic evaluation
print("Random Forest Classifier performance:")
print(classification_report(y_test, y_pred, target_names=labels))

print("Confusion matrix (rows=true, cols=pred):")
print(confusion_matrix(y_test, y_pred))

# Optional: feature importance
import pandas as pd

feat_imp = pd.Series(
    rf_clf.feature_importances_,
    index=X.columns
).sort_values(ascending=False)

print("\nFeature importances:")
print(feat_imp)
