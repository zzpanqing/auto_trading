from google.colab import output
output.enable_custom_widget_manager()

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

        # ── 预先加载所有 ticker 名称 ─────────────────────────────────
        # 避免 draw() 里更新 dropdown.options 触发额外事件
        print("⏳ 预加载公司名称...")
        ticker_labels = {}
        for t in self.tickers:
            res = self._get_computed_df(t)
            ticker_labels[t] = f"{res[0]} ({t})" if res else t
            print(f"  ✅ {ticker_labels[t]}")
        print("✅ 加载完成，启动界面...\n")

        # ── 导航 Widgets ─────────────────────────────────────────────
        btn_prev = widgets.Button(
            description='◀  Prev',
            layout=widgets.Layout(width='100px', height='34px'),
        )
        btn_next = widgets.Button(
            description='Next  ▶',
            layout=widgets.Layout(width='100px', height='34px'),
        )
        # ✅ dropdown 一开始就用完整的公司名，之后不再更新 options
        dropdown = widgets.Dropdown(
            options=[(ticker_labels[t], t) for t in self.tickers],
            value=self.tickers[0],
            layout=widgets.Layout(width='360px'),
        )
        status_label = widgets.Label(value='')

        # ── SMA ToggleButtons（横向）────────────────────────────────
        sma_buttons = []
        for w in self.sma_windows:
            is_default = w in [self.short_window, self.long_window]
            btn = widgets.ToggleButton(
                value=is_default,
                description=f'SMA {w}',
                layout=widgets.Layout(width='75px', height='28px'),
            )
            sma_buttons.append(btn)

        out = widgets.Output()

        # ✅ 用字典做锁，防止事件连锁触发
        state = {'idx': 0, 'updating': False}

        # ── 布局 ────────────────────────────────────────────────────
        nav_row = widgets.HBox(
            [btn_prev, dropdown, btn_next, status_label],
            layout=widgets.Layout(align_items='center', gap='6px', margin='0 0 6px 0'),
        )
        sma_label = widgets.HTML('<b style="font-size:13px">显示 SMA：</b>')
        sma_row = widgets.HBox(
            [sma_label] + sma_buttons,
            layout=widgets.Layout(align_items='center', gap='4px', margin='0 0 8px 0'),
        )

        # ✅ 先显示界面
        display(nav_row, sma_row, out)

        # ── 获取当前选中的 SMA 列表 ──────────────────────────────────
        def get_visible_smas():
            return [w for w, btn in zip(self.sma_windows, sma_buttons) if btn.value]

        # ── 绘图函数 ─────────────────────────────────────────────────
        def draw(ticker, visible_smas):
            status_label.value = f'⏳ {ticker_labels.get(ticker, ticker)}'
            res = self._get_computed_df(ticker)
            if res is None:
                with out:
                    clear_output(wait=True)
                    print(f"❌ 无法获取 {ticker} 的数据")
                status_label.value = '❌ 失败'
                return

            company_name, df = res

            fig = go.Figure()

            # 收盘价
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Close'],
                name='Close Price',
                line=dict(color='#5B8DB8', width=2),
                opacity=0.7,
            ))

            # SMA 曲线
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

            with out:
                clear_output(wait=True)
                display(fig)

            status_label.value = f'✅ {company_name}'

        # ── 事件处理 ─────────────────────────────────────────────────
        def on_prev(_):
            if state['updating']:
                return
            state['updating'] = True
            state['idx'] = (state['idx'] - 1) % len(self.tickers)
            ticker = self.tickers[state['idx']]
            # ✅ 直接设置 value，不更新 options，避免触发额外事件
            dropdown.value = ticker
            draw(ticker, get_visible_smas())
            state['updating'] = False

        def on_next(_):
            if state['updating']:
                return
            state['updating'] = True
            state['idx'] = (state['idx'] + 1) % len(self.tickers)
            ticker = self.tickers[state['idx']]
            dropdown.value = ticker
            draw(ticker, get_visible_smas())
            state['updating'] = False

        def on_dropdown_change(change):
            if state['updating']:
                return
            if change['type'] == 'change' and change['name'] == 'value':
                state['updating'] = True
                ticker = change['new']
                state['idx'] = self.tickers.index(ticker)
                draw(ticker, get_visible_smas())
                state['updating'] = False

        def make_sma_handler(w):
            def handler(change):
                if state['updating']:
                    return
                if change['name'] == 'value':
                    draw(self.tickers[state['idx']], get_visible_smas())
            return handler

        btn_prev.on_click(on_prev)
        btn_next.on_click(on_next)
        dropdown.observe(on_dropdown_change)
        for w, btn in zip(self.sma_windows, sma_buttons):
            btn.observe(make_sma_handler(w))

        # ✅ 最后画图（数据已在预加载时缓存，直接从缓存读取）
        draw(self.tickers[0], get_visible_smas())


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