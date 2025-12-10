import pandas as pd
import csv

df = pd.read_excel("complete_similarity_data.xlsx")
df = df[(df["len_a"] >= 65) & (df["len_b"] >= 65)]

print(df)

df.to_csv("cleanSimData.csv")