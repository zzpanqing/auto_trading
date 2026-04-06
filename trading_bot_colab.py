from google.colab import output
output.enable_custom_widget_manager()

import yfinance as yf
import time
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from IPython.display import display


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
            print(f"[ERROR] {ticker}: {e}")
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

        SMA_COLORS = [
            '#F4A261', '#2A9D8F', '#E76F51', '#9B5DE5',
            '#A8DADC', '#F72585', '#4CC9F0', '#06D6A0',
        ]
        win_colors = {w: SMA_COLORS[i % len(SMA_COLORS)]
                      for i, w in enumerate(self.sma_windows)}

        # ── 预加载所有数据 ───────────────────────────────────────────
        print("⏳ 预加载数据...")
        res_list = []
        for t in self.tickers:
            res = self._get_computed_df(t)
            if res:
                res_list.append((t, res[0], res[1]))
                print(f"  ✅ {res[0]} ({t})")
            else:
                print(f"  ❌ {t} 数据获取失败")
        print("✅ 完成，正在绘图...\n")

        # ── 每个 ticker 有多少条 trace ───────────────────────────────
        # 结构：Close(1) + SMA×N + Buy(1) + Sell(1)
        N_SMA    = len(self.sma_windows)
        N_TRACES = 1 + N_SMA + 2  # Close + SMAs + Buy + Sell

        # ── 构建图表 ─────────────────────────────────────────────────
        fig = go.Figure()
        traces_info = []  # (start_idx, company_name, ticker, signal_emoji, price)

        for ticker_idx, (ticker, company_name, df) in enumerate(res_list):
            is_first = (ticker_idx == 0)
            start = len(fig.data)

            current_signal = self.analyze_market(ticker, df.copy())
            signal_emoji = {'BUY': '🟢 BUY', 'SELL': '🔴 SELL', 'HOLD': '🟡 HOLD'}[current_signal]
            current_price = df['Close'].iloc[-1]

            # Close Price
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Close'],
                name='Close Price',
                visible=is_first,
                line=dict(color='#5B8DB8', width=2),
                opacity=0.7,
                legendgroup=str(ticker_idx),
                showlegend=is_first,
            ))

            # SMA 曲线
            for w in self.sma_windows:
                is_default = w in [self.short_window, self.long_window]
                if is_first:
                    vis = True if is_default else 'legendonly'
                else:
                    vis = False
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[f'SMA_{w}'],
                    name=f'SMA {w}',
                    visible=vis,
                    line=dict(color=win_colors[w], width=1.5),
                    legendgroup=str(ticker_idx),
                    showlegend=is_first,
                ))

            # Buy Signal
            buy_mask = df['Position'] == 1.0
            fig.add_trace(go.Scatter(
                x=df[buy_mask].index,
                y=df[f'SMA_{self.short_window}'][buy_mask],
                mode='markers', name='Buy Signal',
                visible=is_first,
                marker=dict(symbol='triangle-up', size=12, color='#2DC653',
                            line=dict(color='white', width=1)),
                legendgroup=str(ticker_idx),
                showlegend=is_first,
            ))

            # Sell Signal
            sell_mask = df['Position'] == -1.0
            fig.add_trace(go.Scatter(
                x=df[sell_mask].index,
                y=df[f'SMA_{self.short_window}'][sell_mask],
                mode='markers', name='Sell Signal',
                visible=is_first,
                marker=dict(symbol='triangle-down', size=12, color='#E63946',
                            line=dict(color='white', width=1)),
                legendgroup=str(ticker_idx),
                showlegend=is_first,
            ))

            traces_info.append((start, company_name, ticker, signal_emoji, current_price))

        total_traces = len(fig.data)

        # ── 辅助：构建某个 ticker 的 visibility 数组 ─────────────────
        def make_visibility(active_idx, sma_defaults=None):
            """
            active_idx  : 显示哪个 ticker
            sma_defaults: 哪些 SMA 默认显示（None = 用 short/long）
            """
            if sma_defaults is None:
                sma_defaults = [self.short_window, self.long_window]
            vis = []
            for i, (start, _, _, _, _) in enumerate(traces_info):
                if i == active_idx:
                    # Close
                    vis.append(True)
                    # SMAs
                    for w in self.sma_windows:
                        vis.append(w in sma_defaults)
                    # Buy / Sell
                    vis.append(True)
                    vis.append(True)
                else:
                    vis.extend([False] * N_TRACES)
            return vis

        # ── Ticker 切换按钮 ──────────────────────────────────────────
        ticker_buttons = []
        for i, (start, company_name, ticker, signal_emoji, price) in enumerate(traces_info):
            ticker_buttons.append(dict(
                label=company_name,
                method='update',
                args=[
                    {
                        'visible': make_visibility(i),
                        'showlegend': [j // N_TRACES == i for j in range(total_traces)],
                    },
                    {
                        'title': f'<b>{company_name}</b>  |  €{price:.2f}  |  {signal_emoji}',
                    },
                ],
            ))

        # ── SMA 개별 toggle 按钮 ─────────────────────────────────────
        # 注：Plotly 原生按钮切换 SMA 只对当前显示的 ticker 生效
        # 这里用 restyle 切换单条 trace 的 visible
        sma_buttons = []
        for sma_idx, w in enumerate(self.sma_windows):
            sma_buttons.append(dict(
                label=f'SMA {w}',
                method='restyle',
                # trace index 在当前 ticker 里是 1+sma_idx（Close 是第0条）
                # 但因为所有 ticker 都堆在一起，需要对所有 ticker 同时操作
                args=[
                    {'visible': 'toggle'},
                    # 所有 ticker 里这条 SMA 的 trace 下标
                    [i * N_TRACES + 1 + sma_idx for i in range(len(traces_info))],
                ],
            ))

        # 初始标题
        first = traces_info[0]
        init_title = f'<b>{first[1]}</b>  |  €{first[4]:.2f}  |  {first[3]}'

        fig.update_layout(
            title=init_title,
            height=600,
            template='plotly_white',
            hovermode='x unified',
            xaxis_title='Date',
            yaxis_title='Price (€)',
            legend=dict(
                orientation='h',
                yanchor='bottom', y=1.18,
                xanchor='right', x=1,
            ),
            margin=dict(l=50, r=30, t=160, b=50),

            updatemenus=[
                # ── 菜单 1：Ticker 选择（下拉）────────────────────────
                dict(
                    type='dropdown',
                    direction='down',
                    buttons=ticker_buttons,
                    x=0, xanchor='left',
                    y=1.18, yanchor='top',
                    showactive=True,
                    bgcolor='white',
                    bordercolor='#cccccc',
                ),
                # ── 菜单 2：SMA 开关（横排按钮）──────────────────────
                dict(
                    type='buttons',
                    direction='left',
                    buttons=sma_buttons,
                    x=0, xanchor='left',
                    y=1.08, yanchor='top',
                    showactive=True,
                    bgcolor='#f0f0f0',
                    activecolor='#4A90D9',
                    bordercolor='#cccccc',
                ),
            ],
        )

        display(fig)


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