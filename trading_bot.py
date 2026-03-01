import yfinance as yf
import time
from datetime import datetime

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

  def execute_trade(self, ticker, company_name, action, price):
    print("ticker " + ticker)
    print("company_name " + company_name)
    print("action " + action)
    print("price €" + str(price))



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
  bot = TradingBot(tickers=WATCHLIST, short_window=5, long_window=10)
  bot.run()
  
  # Test collecting data for the first stock
  # data = bot.get_data(WATCHLIST[0])
  # print(data)