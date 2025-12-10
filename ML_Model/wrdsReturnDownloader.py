import wrds
import pandas as pd

# 1. Connect
db = wrds.Connection(wrds_username='upalmier')

df_input = pd.read_excel("master_all.xlsx")
ciks = df_input['CIK'].astype(str).str.zfill(10).tolist()

def querymaker(cik):
    query = f"""
    SELECT 
        c.cik, 
        c.conm as company_name, 
        m.date, 
        m.ret
    FROM 
        crsp.msf as m
    JOIN 
        crsp.ccmxpf_linktable as link
        ON m.permno = link.lpermno
    JOIN
        comp.company as c
        ON link.gvkey = c.gvkey
    WHERE 
        c.cik = '{cik}'            
        AND m.date >= '2006-01-01'      
        AND m.date <= '2025-10-31'
        AND link.linktype IN ('LU', 'LC')
        AND link.linkprim IN ('P', 'C')
        AND m.date >= link.linkdt
        AND (m.date <= link.linkenddt OR link.linkenddt IS NULL)
    """
    return query

df1 = db.raw_sql(querymaker(ciks[0]))
print(df1)
for cik in ciks[1:]:
    query = querymaker(cik)
    print(cik)
    try:
        df = db.raw_sql(query)
        print("Success! Here is the data:")
        print(df)
        # exact syntax:
        df1 = pd.concat([df1, df], ignore_index=True)

    except Exception as e:
        print("Error:", e)

df1.to_csv('returns.csv')