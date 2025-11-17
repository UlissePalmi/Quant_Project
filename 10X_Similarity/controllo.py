import pandas as pd

df_Dataset = pd.read_csv("Final Dataset.csv")
ticker_list = df_Dataset['ticker'].unique()

list_of_dict = []

for ticker in ticker_list:
    ticker_df = df_Dataset[df_Dataset['ticker']==ticker]['date_a']
    ticker_list = ticker_df.astype(str).str[-4:].tolist()
    list = []
    for i in range(int(min(ticker_list)), 2026):
        if not str(i) in ticker_list:
            list.append(i)
    if list:
        t_dict = {ticker: list}
        list_of_dict.append(t_dict)
print(list_of_dict)
