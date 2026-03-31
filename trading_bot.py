import yfinance as yf
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


class TradingBot:
  def __init__(self, tickers, short_window, long_window):
    self.tickers = tickers # ticker : stock'slabel 
    self.short_window = short_window
    self.long_window = long_window
    self.positions = {ticker: 0 for ticker in self.tickers}

  def get_data(self, ticker):
    #Fetches historical data to calculate moving averages.
    try:
      stock = yf.Ticker(ticker)
      info = stock.info
      hist = stock.history(period="3mo", interval="1d")
    except Exception as e:
      print(f"Error fetching data for {ticker}: {e}")
      return None
    return info, hist
  
  def analyze_market(self, ticker, df):
    #Applies the SMA Crossover strategy.
    #Returns: 'BUY', 'SELL', or 'HOLD'
    df['SMA_Short'] = df['Close'].rolling(window=self.short_window).mean()
    df['SMA_Long'] = df['Close'].rolling(window=self.long_window).mean()
    if len(df) < self.long_window:
      return 'HOLD' # Not enough data yet
    current_price = df['Close'].iloc[-1]
    prev_short = df['SMA_Short'].iloc[-2]
    curr_short = df['SMA_Short'].iloc[-1]
    prev_long = df['SMA_Long'].iloc[-2]
    curr_long = df['SMA_Long'].iloc[-1]
            
    # Logic: Short SMA crosses ABOVE Long SMA -> BUY
    if prev_short <= prev_long and curr_short > curr_long:
      return 'BUY'
    # Logic: Short SMA crosses BELOW Long SMA -> SELL
    elif prev_short >= prev_long and curr_short < curr_long:
      return 'SELL'
    return 'HOLD'

  def get_company_news(self, ticker):
    """
    Fetches the latest news for a specific company.
    """
    try:
        stock = yf.Ticker(ticker)
        news_list = stock.news
        
        print(f"\n--- Latest News for {ticker} ---")
        if news_list:
            # Print the top 2 headlines
            for item in news_list[:2]:
                title = item.get('title', 'No Title')
                link = item.get('link', 'No Link')
                print(f"- {title}")
                print(f"  Link: {link}")
        else:
            print("No recent news found.")
        print("----------------------------------\n")
    except Exception as e:
        print(f"Could not fetch news for {ticker}: {e}")

  def execute_trade(self, ticker, company_name, action, price):
    print("ticker " + ticker)
    print("company_name " + company_name)
    print("action " + action)
    print("price €" + str(price))

  def visualize_strategy(self, ticker):
    data = self.get_data(ticker)
    if data is None:
      return
    (info, df) = data

    df['SMA_Short'] = df['Close'].rolling(window=self.short_window).mean()
    df['SMA_Long'] = df['Close'].rolling(window=self.long_window).mean()

    df['Signal'] = 0.0
    df.loc[df['SMA_Short'] > df['SMA_Long'], 'Signal'] = 1.0
    df['Position'] = df['Signal'].diff()

    plt.figure(figsize=(12, 6))
    plt.plot(df['Close'], label='Close Price', alpha=0.5)
    plt.plot(df['SMA_Short'], label=f'SMA {self.short_window}', alpha=0.9)
    plt.plot(df['SMA_Long'], label=f'SMA {self.long_window}', alpha=0.9)

    # Plot Buy/Sell Signals
    plt.plot(df[df['Position'] == 1.0].index, df['SMA_Short'][df['Position'] == 1.0], '^', markersize=10, color='g', label='Buy Signal')
    plt.plot(df[df['Position'] == -1.0].index, df['SMA_Short'][df['Position'] == -1.0], 'v', markersize=10, color='r', label='Sell Signal')

    company_name = info.get('longName', ticker)
    plt.title(f"{company_name} - SMA Crossover")
    plt.legend()
    plt.show()

  def visualize_all_strategies(self):
    """
    Visualize all tickers' strategies in a grid layout
    """
    num_tickers = len(self.tickers)

    # Calculate grid dimensions
    cols = 2  # 2 columns
    rows = (num_tickers + cols - 1) // cols  # Ceiling division

    fig, axes = plt.subplots(rows, cols, figsize=(16, 4 * rows))
    fig.suptitle('SMA Crossover Strategy - All Tickers', fontsize=16, y=0.98)

    # Flatten axes array for easier indexing
    if rows == 1 and cols == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for idx, ticker in enumerate(self.tickers):
        data = self.get_data(ticker)
        if data is None:
            continue

        (info, df) = data
        company_name = info.get('longName', ticker)

        # Calculate SMAs
        df['SMA_Short'] = df['Close'].rolling(window=self.short_window).mean()
        df['SMA_Long'] = df['Close'].rolling(window=self.long_window).mean()

        df['Signal'] = 0.0
        df.loc[df['SMA_Short'] > df['SMA_Long'], 'Signal'] = 1.0
        df['Position'] = df['Signal'].diff()

        # Plot on subplot
        ax = axes[idx]
        ax.plot(df['Close'], label='Close Price', alpha=0.5)
        ax.plot(df['SMA_Short'], label=f'SMA {self.short_window}', alpha=0.9)
        ax.plot(df['SMA_Long'], label=f'SMA {self.long_window}', alpha=0.9)

        # Plot Buy/Sell Signals
        ax.plot(df[df['Position'] == 1.0].index,
                df['SMA_Short'][df['Position'] == 1.0],
                '^', markersize=8, color='g', label='Buy')
        ax.plot(df[df['Position'] == -1.0].index,
                df['SMA_Short'][df['Position'] == -1.0],
                'v', markersize=8, color='r', label='Sell')

        ax.set_title(f"{company_name} ({ticker})")
        ax.legend(loc='upper left', fontsize='small')
        ax.grid(True, alpha=0.3)

        # Format x-axis dates
        ax.tick_params(axis='x', rotation=45)

    # Hide any unused subplots
    for idx in range(num_tickers, len(axes)):
        axes[idx].axis('off')

    plt.tight_layout()
    plt.show()


  def run(self):
    try:
      while True:
        for ticker in self.tickers:
          (info, df) = self.get_data(ticker)
          if df is not None:
            current_price = df['Close'].iloc[-1]
            signal = self.analyze_market(ticker, df)
            company_name = info.get('longName', ticker)
            if signal in ['BUY', 'SELL']:
              self.execute_trade(ticker, company_name, signal, current_price)
            else:
              print(f"[{datetime.now().strftime('%H:%M:%S')}] {ticker} [{company_name}]: €{current_price:.2f} | Strategy: HOLD")
        time.sleep(60)
    except KeyboardInterrupt:
      print("\nBot stopped by user.")




if __name__ == "__main__":
  WATCHLIST = ['FR0000120644', #Danone, XPAR BN
               'FR0010908533', #Edenred SE, XPAR
               'FR0000121667', #EssilorLuxottica, XPAR
               'FR0000120321', #L'Oréal, XPAR EL
               'FR0000120578', #, Sanofi, XPAR OR
               'NL0014559478', #Technip Energies N.V. XPAR TE
               'FR0000120271' # TotalEnergies SE, XPAR TTE
              ]
  bot = TradingBot(tickers=WATCHLIST, short_window=20, long_window=100)
  bot.run()
  
  # Test collecting data for the first stock
  # data = bot.get_data(WATCHLIST[0])
  # print(data)

  bot.get_company_news(WATCHLIST[0])
  for ticker in WATCHLIST:
    bot.visualize_strategy(ticker)
