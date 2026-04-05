import yfinance as yf
import time
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ipywidgets as widgets
from IPython.display import display, clear_output


class TradingBot:

    def __init__(self, tickers, short_window, long_window, sma_windows=None):
        self.tickers = tickers
        self.short_window = short_window
        self.long_window = long_window
        base = sma_windows or [short_window, long_window]
        self.sma_windows = sorted(set(base + [short_window, long_window]))
        self.positions = {ticker: 0 for ticker in self.tickers}
        self._cache = {}

    def get_data(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="12mo", interval="1d")
            if hist.empty:
                return None
            return info, hist
        except Exception as e:
            print(f"[ERROR] Error fetching data for {ticker}: {e}")
            return None

    def analyze_market(self, ticker, df):
        df['SMA_Short'] = df['Close'].rolling(window=self.short_window).mean()
        df['SMA_Long']  = df['Close'].rolling(window=self.long_window).mean()
        if len(df) < self.long_window:
            return 'HOLD'
        prev_short = df['SMA_Short'].iloc[-2]
        curr_short = df['SMA_Short'].iloc[-1]
        prev_long  = df['SMA_Long'].iloc[-2]
        curr_long  = df['SMA_Long'].iloc[-1]
        if prev_short <= prev_long and curr_short > curr_long:
            return 'BUY'
        elif prev_short >= prev_long and curr_short < curr_long:
            return 'SELL'
        return 'HOLD'

    def get_company_news(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            news_list = stock.news
            print(f"\n--- Latest News for {ticker} ---")
            if news_list:
                for item in news_list[:2]:
                    print(f"- {item.get('title', 'No Title')}")
                    print(f"  Link: {item.get('link', 'No Link')}")
            else:
                print("No recent news found.")
            print("----------------------------------\n")
        except Exception as e:
            print(f"Could not fetch news for {ticker}: {e}")

    def execute_trade(self, ticker, company_name, action, price):
        print(f"ticker       : {ticker}")
        print(f"company_name : {company_name}")
        print(f"action       : {action}")
        print(f"price        : €{price}")

    def run(self):
        try:
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
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {ticker} [{company_name}]: "
                          f"€{current_price:.2f} | Strategy: HOLD")
        except KeyboardInterrupt:
            print("\nBot stopped by user.")

    def _get_computed_df(self, ticker):
        if ticker in self._cache:
            return self._cache[ticker]
        data = self.get_data(ticker)
        if data is None:
            return None
        info, df = data
        if df.empty:
            return None
        df = df.copy()
        for w in self.sma_windows:
            df[f'SMA_{w}'] = df['Close'].rolling(window=w).mean()
        df['Signal'] = 0.0
        df.loc[df[f'SMA_{self.short_window}'] > df[f'SMA_{self.long_window}'], 'Signal'] = 1.0
        df['Position'] = df['Signal'].diff()
        company_name = info.get('longName', ticker)
        self._cache[ticker] = (company_name, df)
        return self._cache[ticker]

    def visualize_colab(self):

        # ── 颜色配置 ────────────────────────────────────────────────
        SMA_COLORS = [
            '#F4A261', '#2A9D8F', '#E76F51', '#9B5DE5',
            '#A8DADC', '#F72585', '#4CC9F0', '#06D6A0',
        ]
        win_colors = {w: SMA_COLORS[i % len(SMA_COLORS)]
                      for i, w in enumerate(self.sma_windows)}

        # ── 预加载第一个 ticker 的标签 ───────────────────────────────
        # 其余 ticker 标签在首次点击时加载（避免启动太慢）
        ticker_labels = {}
        for t in self.tickers:
            ticker_labels[t] = t  # 先用 ticker 本身作为临时标签

        # ── Widgets ─────────────────────────────────────────────────
        btn_prev = widgets.Button(
            description='◀  Prev',
            layout=widgets.Layout(width='100px', height='34px'),
        )
        btn_next = widgets.Button(
            description='Next  ▶',
            layout=widgets.Layout(width='100px', height='34px'),
        )
        dropdown = widgets.Dropdown(
            options=[(t, t) for t in self.tickers],
            value=self.tickers[0],
            layout=widgets.Layout(width='360px'),
        )
        sma_toggle = widgets.SelectMultiple(
            options=self.sma_windows,
            value=[self.short_window, self.long_window],
            description='SMA:',
            layout=widgets.Layout(width='200px', height=f'{28 * len(self.sma_windows) + 8}px'),
        )
        status_label = widgets.Label(value='⏳ 加载中...')
        out = widgets.Output()

        idx = {'i': 0}

        # ── 布局（先 display，再 draw）───────────────────────────────
        nav_row = widgets.HBox(
            [btn_prev, dropdown, btn_next, status_label],
            layout=widgets.Layout(align_items='center', gap='8px', margin='0 0 8px 0'),
        )
        sma_label = widgets.HTML('<b style="font-size:13px">显示 SMA 均线：</b>')
        sma_row = widgets.HBox(
            [sma_label, sma_toggle],
            layout=widgets.Layout(align_items='flex-start', margin='0 0 10px 0'),
        )

        # ✅ 先显示界面，再画图
        display(nav_row, sma_row, out)

        # ── 绘图函数 ────────────────────────────────────────────────
        def draw(ticker, visible_smas):
            status_label.value = f'⏳ 加载 {ticker} ...'

            # ✅ 用 self 而不是 bot
            res = self._get_computed_df(ticker)
            if res is None:
                with out:
                    clear_output(wait=True)
                    print(f"❌ 无法获取 {ticker} 的数据")
                status_label.value = '❌ 数据获取失败'
                return

            company_name, df = res

            # 更新 dropdown 标签
            ticker_labels[ticker] = f"{company_name} ({ticker})"
            dropdown.options = [(ticker_labels[t], t) for t in self.tickers]
            dropdown.value = ticker  # 保持选中

            fig = go.Figure()

            # 收盘价
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Close'],
                name='Close Price',
                line=dict(color='#5B8DB8', width=2),
                opacity=0.7,
            ))

            # ✅ 用 self 而不是 bot
            for w in self.sma_windows:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[f'SMA_{w}'],
                    name=f'SMA {w}',
                    line=dict(color=win_colors[w], width=1.5),
                    visible=True if w in visible_smas else 'legendonly',
                ))

            # Buy / Sell markers
            buy_mask  = df['Position'] == 1.0
            sell_mask = df['Position'] == -1.0

            # ✅ 用 self 而不是 bot
            fig.add_trace(go.Scatter(
                x=df[buy_mask].index,
                y=df[f'SMA_{self.short_window}'][buy_mask],
                mode='markers', name='Buy Signal',
                marker=dict(symbol='triangle-up', size=12, color='#2DC653',
                            line=dict(color='white', width=1)),
            ))
            fig.add_trace(go.Scatter(
                x=df[sell_mask].index,
                y=df[f'SMA_{self.short_window}'][sell_mask],
                mode='markers', name='Sell Signal',
                marker=dict(symbol='triangle-down', size=12, color='#E63946',
                            line=dict(color='white', width=1)),
            ))

            # ✅ 用 self 而不是 bot
            current_signal = self.analyze_market(ticker, df.copy())
            signal_emoji = {'BUY': '🟢 BUY', 'SELL': '🔴 SELL', 'HOLD': '🟡 HOLD'}[current_signal]
            current_price = df['Close'].iloc[-1]

            fig.update_layout(
                title=f"<b>{company_name}</b>  |  €{current_price:.2f}  |  {signal_emoji}",
                xaxis_title='Date',
                yaxis_title='Price (€)',
                hovermode='x unified',
                height=520,
                template='plotly_white',
                legend=dict(orientation='h', yanchor='bottom', y=1.01, xanchor='right', x=1),
                margin=dict(l=50, r=30, t=70, b=50),
            )

            # ✅ display(fig) 而不是 fig.show()
            with out:
                clear_output(wait=True)
                display(fig)

            status_label.value = f'✅ {company_name}'

        # ── 事件处理（只绑定一次）───────────────────────────────────
        def on_prev(_):
            idx['i'] = (idx['i'] - 1) % len(self.tickers)
            dropdown.value = self.tickers[idx['i']]

        def on_next(_):
            idx['i'] = (idx['i'] + 1) % len(self.tickers)
            dropdown.value = self.tickers[idx['i']]

        def on_dropdown_change(change):
            if change['type'] == 'change' and change['name'] == 'value':
                ticker = change['new']
                idx['i'] = self.tickers.index(ticker)
                draw(ticker, list(sma_toggle.value))

        def on_sma_change(change):
            if change['type'] == 'change' and change['name'] == 'value':
                draw(self.tickers[idx['i']], list(change['new']))

        btn_prev.on_click(on_prev)
        btn_next.on_click(on_next)
        dropdown.observe(on_dropdown_change)
        sma_toggle.observe(on_sma_change)

        # ✅ 最后才画图（界面已经显示了）
        draw(self.tickers[0], list(sma_toggle.value))


# ════════════════════════════════════════════════════════════════════
#  入口
# ════════════════════════════════════════════════════════════════════

WATCHLIST = [
    'FR0000133308',   # Orange
    'FR0000120644',   # Danone
    'FR0010908533',   # Edenred SE
    'FR0000121667',   # EssilorLuxottica
    'FR0000120321',   # L'Oréal
    'FR0000120578',   # Sanofi
    'NL0014559478',   # Technip Energies
    'FR0000120271',   # TotalEnergies
]

bot = TradingBot(
    tickers=WATCHLIST,
    short_window=10,
    long_window=50,
    sma_windows=[5, 10, 20, 25, 50, 100, 200],
)

# bot.get_company_news(WATCHLIST[0])
# bot.run()

bot.visualize_colab()