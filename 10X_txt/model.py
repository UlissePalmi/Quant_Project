import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

data = pd.read_csv("Final Data.csv")
filtered = data.loc[data["similarity"] < 0.73]

print(filtered)

