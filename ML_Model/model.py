import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.tree import DecisionTreeRegressor, export_text
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

df = pd.read_csv("Final Dataset.csv")

#df = df[df["similarity"] < 0.70]

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

# Keep just the three inputs you requested
X = df[["similarity", "sim_below_70", "sentiment", "sentiment_pos", "len_growth_pct", "ret_12m_prior_to_10k"]].copy()
y = df["ret_18m_next_month"].copy()

# Drop rows with missing values in features/target
mask = X.notna().all(axis=1) & y.notna()
X = X[mask]; y = y[mask]
dates = pd.to_datetime(df.loc[mask, "date_a"])

# ===== 3) Time-aware cross-validation =====
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, shuffle=True, random_state=42)

# Tree that's intentionally simple & robust for returns
tree = DecisionTreeRegressor(
    criterion="squared_error",
    max_depth=3,          # keep shallow for interpretability
    min_samples_leaf=200)

tree.fit(X_train, y_train)
pred = tree.predict(X_test)
mae  = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2   = r2_score(y_test, pred)
print(f"Test MAE={mae:.4f} | RMSE={rmse:.4f} | R²={r2:.3f}")

# Optional: see the rules
print(export_text(tree, feature_names=list(X.columns)))
