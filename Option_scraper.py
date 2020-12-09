#!/usr/bin/env python
# coding: utf-8

# In[83]:


# Necessary Libraries
import yfinance as yf
import pandas as pd
import shutil, os, time, glob
import numpy as np
import requests
from get_all_tickers import get_tickers as gt
from statistics import mean
import math
import Stats_scraper
from openpyxl import load_workbook

# In[84]:


#Locations
os.chdir(r"C:\Users\igorq\Documents\Phynance\Data")
pathopt = "Options/"
ext = ".xlsx"


# In[85]:


from datetime import date
from datetime import timedelta
#Parameters
tickers = ["AAPL", "AMZN", "TSLA", "MSFT", "GOOGL", "SPY", "UDOW", "SDOW", "SPXL", "SPXS"]
date = date.today() - timedelta(days=1)
date= date.strftime("%d%m%Y")

# In[87]:


Amount_of_API_Calls = 0

for i in range(0, len(tickers)):
    stock = tickers[i]  # Gets the current stock ticker
    temp = yf.Ticker(str(stock))
    data = temp.history()
    last_quote = (data.tail(1)['Close'].iloc[0])
    center_strike = (math.ceil(last_quote))
        
    cdf=pd.DataFrame()
    for j in range(0, min(5,len(temp.options))):
        try:
            df = temp.option_chain(str(temp.options[j])).calls
            center_strike_pos = (df[df['strike']==center_strike].index.values)[0]
            df_puts = temp.option_chain(str(temp.options[j])).puts
            df = df.append(df_puts)
            cdf = cdf.append(df)
            Amount_of_API_Calls += 2
        except:
            pass                

    # Write each dataframe to a different worksheet.
    with pd.ExcelWriter(pathopt+stock+ext, engine='openpyxl', mode='a') as writer:
        cdf.to_excel(writer, sheet_name=date, index=False)

print(str(len(tickers))+" Excel tabs saved succesfully")
print("Amount of API Calls: "+str(Amount_of_API_Calls))

# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




