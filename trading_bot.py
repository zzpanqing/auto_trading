import yfinance as yf
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button


class TradingBot:

  def __init__(self, tickers, short_window, long_window, sma_windows=None):
    self.tickers = tickers # ticker : stock'slabel
    self.short_window = short_window
    self.long_window = long_window
    self.sma_windows = sma_windows if sma_windows else [short_window, long_window]
    self.positions = {ticker: 0 for ticker in self.tickers}

  def get_data(self, ticker):
    #Fetches historical data to calculate moving averages.
    try:
      stock = yf.Ticker(ticker)
      info = stock.info
      hist = stock.history(period="12mo", interval="1d")
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

  def visualize_tickers_navigator(self):
    data_cache = {}
    idx = {'i': 0}
    fig, ax = plt.subplots(figsize=(12, 6))
    plt.subplots_adjust(bottom=0.2)

    # Track which SMA windows are visible
    sma_visible = {window: True for window in self.sma_windows}

    def compute_df(ticker):
      if ticker in data_cache:
        return data_cache[ticker]
      data = self.get_data(ticker)
      if data is None:
        return None
      (info, df) = data
      df = df.copy()
      for window in self.sma_windows:
        df[f'SMA_{window}'] = df['Close'].rolling(window=window).mean()
      df['Signal'] = 0.0
      df.loc[df[f'SMA_{self.short_window}'] > df[f'SMA_{self.long_window}'], 'Signal'] = 1.0
      df['Position'] = df['Signal'].diff()
      company_name = info.get('longName', ticker)
      data_cache[ticker] = (company_name, df)
      return data_cache[ticker]

    def update():
      ax.clear()
      if not self.tickers:
        ax.set_title('No tickers provided')
        fig.canvas.draw_idle()
        return
      ticker = self.tickers[idx['i']]
      res = compute_df(ticker)
      if res is None:
        ax.set_title(f"{ticker} - data unavailable")
        fig.canvas.draw_idle()
        return
      (company_name, df) = res
      ax.plot(df['Close'], label='Close Price', alpha=0.5)
      for window in self.sma_windows:
        if sma_visible[window]:
          ax.plot(df[f'SMA_{window}'], label=f'SMA {window}', alpha=0.9)
      ax.plot(df[df['Position'] == 1.0].index,
              df[f'SMA_{self.short_window}'][df['Position'] == 1.0],
              '^', markersize=8, color='g', label='Buy')
      ax.plot(df[df['Position'] == -1.0].index,
              df[f'SMA_{self.short_window}'][df['Position'] == -1.0],
              'v', markersize=8, color='r', label='Sell')
      ax.set_title(f"{company_name} ({ticker})")
      ax.legend(loc='upper left', fontsize='small')
      ax.grid(True, alpha=0.3)
      ax.tick_params(axis='x', rotation=45)
      fig.canvas.draw_idle()

    # Buttons
    axprev = plt.axes([0.70, 0.02, 0.10, 0.05])
    axnext = plt.axes([0.82, 0.02, 0.10, 0.05])
    bprev = Button(axprev, 'Prev')
    bnext = Button(axnext, 'Next')

    # Create toggle buttons for each SMA window
    button_axes = []
    toggle_buttons = []
    for i, window in enumerate(self.sma_windows):
      ax_button = plt.axes([0.10 + i*0.12, 0.02, 0.10, 0.05])
      button_axes.append(ax_button)
      btn = Button(ax_button, f'SMA {window}')
      toggle_buttons.append(btn)
      def make_toggle(window):
        def toggle(event):
          sma_visible[window] = not sma_visible[window]
          btn.label.set_text(f"SMA {window} {'(off)' if not sma_visible[window] else ''}")
          fig.canvas.draw_idle()
          update()
        return toggle
      btn.on_clicked(make_toggle(window))

    def on_prev(event):
      idx['i'] = (idx['i'] - 1) % len(self.tickers)
      update()

    def on_next(event):
      idx['i'] = (idx['i'] + 1) % len(self.tickers)
      update()

    bprev.on_clicked(on_prev)
    bnext.on_clicked(on_next)

    # Keyboard shortcuts
    def on_key(event):
      if event.key in ('left', 'pageup'):
        on_prev(event)
      elif event.key in ('right', 'pagedown'):
        on_next(event)
    fig.canvas.mpl_connect('key_press_event', on_key)

    update()
    plt.show()


  def run(self):
    try:
      while True:
        for ticker in self.tickers:
          data = self.get_data(ticker)
          if data is None:
            continue
          (info, df) = data
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
  WATCHLIST = ['FR0000133308', #Orange, ORA
               'FR0000120644', #Danone, XPAR BN
               'FR0010908533', #Edenred SE, XPAR
               'FR0000121667', #EssilorLuxottica, XPAR
               'FR0000120321', #L'Oréal, XPAR EL
               'FR0000120578', #Sanofi, XPAR OR
               'NL0014559478', #Technip Energies N.V. XPAR TE
               'FR0000120271' # TotalEnergies SE, XPAR TTE
              ]
  bot = TradingBot(tickers=WATCHLIST, short_window=20, long_window=100, sma_windows=[10, 20, 50, 100, 200])

  # Uncomment to run the bot
  # bot.run()
  
  # Test collecting data for the first stock
  # data = bot.get_data(WATCHLIST[0])
  # print(data)

  bot.get_company_news(WATCHLIST[0])

  # Visualize all strategies in one figure
  # bot.visualize_all_strategies()

  # Optionally, you can still visualize individual stocks if needed
  #for ticker in WATCHLIST:
  #  bot.visualize_strategy(ticker)

  # Visualize interactively: use Prev/Next buttons or Left/Right keys to switch tickers
  bot.visualize_tickers_navigator()

