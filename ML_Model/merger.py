import pandas as pd

sim_df = pd.read_csv('cleanSimData.csv')
return_df = pd.read_csv('returns.csv')


      
sim_df["date_a"] = pd.to_datetime(sim_df["date_a"],format="mixed",dayfirst=True)
sim_df["date_b"] = pd.to_datetime(sim_df["date_b"],format="mixed",dayfirst=True)
return_df["date"] = pd.to_datetime(return_df["date"])


sim_df["start_anchor"] = (sim_df["date_a"] + pd.offsets.MonthBegin(1)).dt.normalize()
sim_df["end_anchor"]   = sim_df["start_anchor"] + pd.offsets.DateOffset(months=18)

return_df['retPlusOne'] = return_df['ret'] + 1

#print(sim_df)
#print(return_df)


sim_df['ret_18'] = sim_df['ticker'].map(
    return_df
    .groupby('cik')['retPlusOne']
    .mean()
)


sim_tmp = sim_df.reset_index().rename(columns={'index': 'sim_idx'})

merged = sim_tmp.merge(
    return_df[['cik', 'date', 'retPlusOne']],
    left_on='ticker',    # ticker in sim_df
    right_on='cik',      # cik in return_df
    how='left'
)
merged = merged[
    (merged['date'] >= merged['start_anchor']) &
    (merged['date'] <= merged['end_anchor'])     # use < if you want end exclusive
]

mean_window = merged.groupby('sim_idx')['retPlusOne'].mean()
sim_df['ret_18'] = sim_df.index.to_series().map(mean_window)

sim_df = sim_df.dropna(subset=['ret_18'])

print(merged.head(50))
print(sim_df.head(50))


sim_df.to_csv('merged_dataset.csv')


#find a way to account for bankrupcy/merger