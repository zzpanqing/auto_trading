import yfinance as yf

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
      hist = stock.history(period="3mo", interval="1d")
    except Exception as e:
      print(f"Error fetching data for {ticker}: {e}")
      return None
    return hist







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
  #bot.run()
  
  # Test collecting data for the first stock
  data = bot.get_data(WATCHLIST[0])
  print(data)