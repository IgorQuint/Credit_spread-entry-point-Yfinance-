#!/usr/bin/env python
# coding: utf-8

# Necessary Libraries
import yfinance as yf
import pandas as pd
import shutil, os, time, glob
import numpy as np
import requests
from get_all_tickers import get_tickers as gt
from statistics import mean
import math


# If you have a list of your own you would like to use just create a new list instead of using this, for example: tickers = ["FB", "AMZN", ...] 
tickers = ["AMZN", "NVDA", "GOOGL", "TSLA", "MSFT", "FB", "AAPL", "SPY", "UDOW", "SDOW", "SPXL", "SPXS"]
# Check that the amount of tickers isn't more than 2000
print("The amount of stocks chosen to observe: " + str(len(tickers)))
# These two lines remove the Stocks folder and then recreate it in order to remove old stocks. Make sure you have created a Stocks Folder the first time you run this.
os.chdir(r"C:\Users\igorq\Documents\Phynance\Data")
shutil.rmtree("Stocks/")
os.mkdir("Stocks/")
#  These will do the same thing but for the folder jolding the Stats for each stock.



# Do not make more than 2,000 calls per hour or 48,000 calls per day or Yahoo Finance may block your IP. The clause "(Amount_of_API_Calls < 1800)" below will stop the loop from making
# too many calls to the Yahoo finance API.
Stock_Failure = 0
Stocks_Not_Imported = 0
Amount_of_API_Calls = 0
# Used to iterate through our list of tickers
i=0
while (i < len(tickers)) and (Amount_of_API_Calls < 1800):
    try:
        print("Dowloading = " + str(tickers[i]))
        stock = tickers[i]  # Gets the current stock ticker
        temp = yf.Ticker(str(stock))
        pathstocks = "Stocks/"
        ext = ".csv"
        Hist_data = temp.history(period="max")  # Tells yfinance what kind of data we want about this stock (In this example, all of the historical data)
        Hist_data.to_csv(pathstocks+stock+ext)  # Saves the historical data in csv format for further processing later
        time.sleep(2)  # Pauses the loop for two seconds so we don't cause issues with Yahoo Finance's backend operations
        Amount_of_API_Calls += 1 
        Stock_Failure = 0
        i += 1  # Iteration to the next ticker
    except ValueError:
        print("Yahoo Finance Backend Error, Attempting to Fix")  # An error occured on Yahoo Finance's backend. We will attempt to retreive the data again
        if Stock_Failure > 5:  # Move on to the next ticker if the current ticker fails more than 5 times
            i+=1
            Stocks_Not_Imported += 1
        Amount_of_API_Calls += 1
        Stock_Failure += 1
    # Handle SSL error
    except requests.exceptions.SSLError as e:
        print("Yahoo Finance Backend Error, Attempting to Fix SSL")  # An error occured on Yahoo Finance's backend. We will attempt to retreive the data again
        if Stock_Failure > 5:  # Move on to the next ticker if the current ticker fails more than 5 times
            i+=1
            Stocks_Not_Imported += 1
        Amount_of_API_Calls += 1
        Stock_Failure += 1
print("The amount of stocks we successfully imported: " + str(i - Stocks_Not_Imported))
print("The number of API calls done: " + str(Amount_of_API_Calls))


# In[54]:


from datetime import date
from datetime import timedelta

# Get the path for each stock file in a list
list_files=[]

for root, dirs, files in os.walk("Stocks/"):
    for file in files:
        if file.endswith('.csv'):
            list_files.append(file)

date = date.today() - timedelta(days=1)
date= date.strftime("%d%m%Y")

# From http://stackoverflow.com/a/14314054/3293881 by @Jaime
def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

# From http://stackoverflow.com/a/40085052/3293881
def strided_app(a, L, S=1 ):  # Window len = L, Stride len/stepsize = S
    size=len(a)
    nrows = ((size-L)//S)+1
    n = a.strides[0]
    return np.lib.stride_tricks.as_strided(a, shape=(nrows,L), strides=(S*n,n))

def rolling_meansqdiff_numpy(a, w):
    A = strided_app(a, w)
    B = moving_average(a,w)
    subs = A-B[:,None]
    sums = np.einsum('ij,ij->i',subs,subs)
    return (sums/w)**0.5

# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter("Stats/"+"stockstats"+".xlsx", engine='xlsxwriter')

# Create the dataframe that we will be adding the final analysis of each stock to
Compare_Stocks = pd.DataFrame(columns=["Company", "Days_Observed", "Crosses", "True_Positive", "False_Positive", "True_Negative", "False_Negative", "Sensitivity", 
"Specificity", "Accuracy", "TPR", "FPR"])

# While loop to cycle through the stock paths
for stock in list_files:
    # Dataframe to hold the historical data of the stock we are interested in.
    Hist_data = pd.read_csv("Stocks/"+stock)
    Company = ((os.path.basename(stock)).split(".csv")[0])  # Name of the company
    # This list holds the closing prices of a stock
    prices = []
    dates = []
    c = 0
    # Add the closing prices to the prices list and make sure we start at greater than 1.5 dollars to reduce outlier calculations.
    while c < len(Hist_data):
        if Hist_data.iloc[c,4] > float(1.50):  # Check that the closing price for this day is greater than $1.50
            prices.append(Hist_data.iloc[c,4])
            dates.append(Hist_data.iloc[c,0])
        c += 1
    
    prices_df = pd.DataFrame(prices)  # Make a dataframe from the prices list
    # Calculate exponentiall weighted moving averages:
    day12 = prices_df.ewm(span=12, adjust=False).mean()  #
    day26 = prices_df.ewm(span=26, adjust=False).mean()
    macd = []  # List to hold the MACD line values
    counter=0  # Loop to substantiate the MACD line
    while counter < (len(day12)):
        macd.append(day12.iloc[counter,0] - day26.iloc[counter,0])  # Subtract the 26 day EW moving average from the 12 day.
        counter += 1
        
    macd_df = pd.DataFrame(macd)
    signal_df = macd_df.ewm(span=9, adjust=False).mean() # Create the signal line, which is a 9 day EW moving average
    signal = signal_df.values.tolist()  # Add the signal line values to a list.  
    i = 0
    upPrices=[]
    downPrices=[]
    #  Loop to hold up and down price movements
    while i < len(prices):
        if i == 0:
            upPrices.append(0)
            downPrices.append(0)
        else:
            if (prices[i]-prices[i-1])>0:
                upPrices.append(prices[i]-prices[i-1])
                downPrices.append(0)
            else:
                downPrices.append(prices[i]-prices[i-1])
                upPrices.append(0)
        i += 1
    x = 0
    avg_gain = []
    avg_loss = []
    #  Loop to calculate the average gain and loss
    while x < len(upPrices):
        if x <15:
            avg_gain.append(0)
            avg_loss.append(0)
        else:
            sumGain = 0
            sumLoss = 0
            y = x-13
            while y<=x:
                sumGain += upPrices[y]
                sumLoss += downPrices[y]
                y += 1
            avg_gain.append(sumGain/14)
            avg_loss.append(abs(sumLoss/14))
        x += 1
    p = 0
    RS = []
    RSI = []
    #  Loop to calculate RSI and RS
    while p < len(prices):
        if p <15:
            RS.append(0)
            RSI.append(0)
        else:
            RSvalue = (avg_gain[p]/avg_loss[p])
            RS.append(RSvalue)
            RSI.append(100 - (100/(1+RSvalue)))
        p+=1
        
    pricearr = np.array(prices)
    MA30 = moving_average(pricearr, 20)
    
    # set .std(ddof=0) for population std instead of sample

    STD30 = rolling_meansqdiff_numpy(pricearr, 20)

  
    #prices.rolling(window=20).std(ddof=0)
    UB = MA30 + (STD30 * 2)
    LB = MA30 - (STD30 * 2)
    
    MA30 = MA30.tolist()
    STD30 = STD30.tolist()
    UB = UB.tolist()
    LB = LB.tolist()
    
    for i in range(0,19):
        MA30.insert(0,0)
        STD30.insert(0,0)
        UB.insert(0,0)
        LB.insert(0,0)

    
    #  Creates the csv for each stock's stats and price movements
    df_dict = {
        'Date' : dates,
        'Prices' : prices,
        'upPrices' : upPrices,
        'downPrices' : downPrices,
        'AvgGain' : avg_gain,
        'AvgLoss' : avg_loss,
        'RS' : RS,
        'RSI' : RSI,
        'MACD' : macd,
        'Signal' : signal,
        '30 day MA' : MA30,
        '30-day std deviation' : STD30,
        'Upper band' : UB,
        'Lower band' : LB
    }
    df = pd.DataFrame(df_dict, columns = ['Date', 'Prices', 'upPrices', 'downPrices', 'AvgGain','AvgLoss', 'RS', "RSI", "MACD", "Signal", "30 day MA", "30-day std deviation", "Upper band", "Lower band"])
    
    # Write each dataframe to a different tab.
    df.to_excel(writer, sheet_name=Company)

writer.save()




