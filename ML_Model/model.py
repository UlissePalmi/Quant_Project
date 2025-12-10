import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeRegressor, export_text
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor

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




X = df[["similarity", "sim_below_70", "sentiment", "sentiment_pos", "inc_len", "len_growth_pct", "old_similarity", "sim_sum", "ret_prev_12m"]].copy()
y = df["ret_18"].copy()

# Drop rows with missing values in features/target
mask = X.notna().all(axis=1) & y.notna()
X = X[mask]; y = y[mask]
dates = pd.to_datetime(df.loc[mask, "date_a"])


df = df[mask]


'''
# ===== 3) Time-aware cross-validation =====
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, shuffle=True, random_state=42)

# Tree that's intentionally simple & robust for returns
tree = DecisionTreeRegressor(
    criterion="squared_error",
    max_depth=4,          # keep shallow for interpretability
    min_samples_leaf=200)

tree.fit(X_train, y_train)
pred = tree.predict(X_test)
mae  = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2   = r2_score(y_test, pred)
print(f"Test MAE={mae:.4f} | RMSE={rmse:.4f} | R²={r2:.3f}")

# Optional: see the rules
print(export_text(tree, feature_names=list(X.columns)))
''''''
'''
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, shuffle=True, random_state=42
)

# Random Forest model for returns
rf = RandomForestRegressor(
    n_estimators=300,       # number of trees
    criterion="squared_error",
    max_depth=5,            # limit depth to reduce overfitting
    min_samples_leaf=200,   # similar robustness to your tree
    n_jobs=-1,              # use all cores
    random_state=42,
    oob_score=True          # out-of-bag score as extra validation
)

rf.fit(X_train, y_train)
pred = rf.predict(X_test)

mae  = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2   = r2_score(y_test, pred)

print(f"Random Forest | Test MAE={mae:.4f} | RMSE={rmse:.4f} | R²={r2:.3f}")
print(f"OOB R² (if applicable) = {rf.oob_score_:.3f}")

y_pred = rf.predict(X)

df['y_pred'] = y_pred
df.to_csv('pred_check.csv')
'''
''''''
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, shuffle=True, random_state=42
)

# XGBoost model
xgb = XGBRegressor(
    n_estimators=500,        # number of boosting stages
    learning_rate=0.05,     # smaller LR + more trees = smoother model
    max_depth=3,            # shallow trees to reduce overfitting
    subsample=0.8,          # row subsampling
    colsample_bytree=0.8,   # feature subsampling
    reg_lambda=1.0,         # L2 regularization
    reg_alpha=0.0,          # L1 regularization (set >0 if you want sparsity)
    objective="reg:squarederror",
    random_state=42,
    n_jobs=-1
)

xgb.fit(X_train, y_train)

pred = xgb.predict(X_test)

mae  = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2   = r2_score(y_test, pred)

print(f"XGBoost | Test MAE={mae:.4f} | RMSE={rmse:.4f} | R²={r2:.3f}")
'''