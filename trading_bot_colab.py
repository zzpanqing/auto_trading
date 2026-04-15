#v8
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
            '#F4A261', "#170B5C", '#E76F51', '#9B5DE5',
            '#A8DADC', '#F72585', '#4CC9F0', "#89BF14",
        ]
        win_colors = {w: SMA_COLORS[i % len(SMA_COLORS)]
                      for i, w in enumerate(self.sma_windows)}

        # ── 预加载所有数据 ───────────────────────────────────────────
        #print("⏳ 预加载数据...")
        res_list = []
        for t in self.tickers:
            res = self._get_computed_df(t)
            if res:
                company_name, df = res[0], res[1]

                # 获取历史财报日期
                q_dates, a_dates = [], []
                try:
                    stock = yf.Ticker(t)
                    df_idx = df.index.normalize()

                    qe = stock.quarterly_earnings
                    if qe is not None and not qe.empty:
                        dates = pd.to_datetime(qe.index).normalize()
                        q_dates = [d for d in dates if d in df_idx]

                    ae = stock.earnings
                    if ae is not None and not ae.empty:
                        dates = pd.to_datetime(ae.index).normalize()
                        a_dates = [d for d in dates if d in df_idx]
                except Exception:
                    pass

                res_list.append((t, company_name, df, q_dates, a_dates))
            else:
                print(f"  ❌ {t} 数据获取失败")
        print("✅ 完成，正在绘图...\n")

        # 每个 ticker 的 trace 数量：Close + SMAs + Buy + Sell + 季度财报 + 年度财报
        N_SMA    = len(self.sma_windows)
        N_TRACES = 1 + N_SMA + 2 + 2

        # ── 构建图表 ─────────────────────────────────────────────────
        fig = go.Figure()
        traces_info = []

        for ticker_idx, (ticker, company_name, df, q_dates, a_dates) in enumerate(res_list):
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
                legendgroup='close',
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
                    legendgroup=f'sma{w}',
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
                legendgroup='buy',
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
                legendgroup='sell',
                showlegend=is_first,
            ))

            # 季度财报标记（向下三角，橙色）
            q_prices = df['Close'].reindex(q_dates) if q_dates else pd.Series(dtype=float)
            fig.add_trace(go.Scatter(
                x=q_prices.index, y=q_prices.values,
                mode='markers', name='季度财报',
                visible=is_first,
                marker=dict(symbol='triangle-down', size=14, color='#FF8C00',
                            line=dict(color='white', width=1)),
                legendgroup='q_earnings',
                showlegend=is_first,
                hovertemplate='季度财报<br>%{x|%Y-%m-%d}<br>€%{y:.2f}<extra></extra>',
            ))

            # 年度财报标记（向下三角，紫色，更大）
            a_prices = df['Close'].reindex(a_dates) if a_dates else pd.Series(dtype=float)
            fig.add_trace(go.Scatter(
                x=a_prices.index, y=a_prices.values,
                mode='markers', name='年度财报',
                visible=is_first,
                marker=dict(symbol='triangle-down', size=18, color='#9B59B6',
                            line=dict(color='white', width=1.5)),
                legendgroup='a_earnings',
                showlegend=is_first,
                hovertemplate='年度财报<br>%{x|%Y-%m-%d}<br>€%{y:.2f}<extra></extra>',
            ))

            traces_info.append((start, company_name, ticker, signal_emoji, current_price))

        total_traces = len(fig.data)

        # ── 构建 ticker 切换按钮 ─────────────────────────────────────
        # 每个按钮切换时：
        #   - 只显示当前 ticker 的 traces
        #   - SMA 默认显示 short/long，其余 legendonly
        #   - 更新图例只显示当前 ticker 的条目
        #   - 更新标题
        ticker_buttons = []
        for i, (start, company_name, ticker, signal_emoji, price) in enumerate(traces_info):

            # 构建 visibility 数组
            vis = []
            showlegend = []
            for j, (s, _, _, _, _) in enumerate(traces_info):
                if j == i:
                    # Close
                    vis.append(True)
                    showlegend.append(True)
                    # SMAs
                    for w in self.sma_windows:
                        is_default = w in [self.short_window, self.long_window]
                        vis.append(True if is_default else 'legendonly')
                        showlegend.append(True)
                    # Buy / Sell
                    vis.append(True)
                    showlegend.append(True)
                    vis.append(True)
                    showlegend.append(True)
                    # 季度财报 / 年度财报
                    vis.append(True)
                    showlegend.append(True)
                    vis.append(True)
                    showlegend.append(True)
                else:
                    # 其他 ticker 全隐藏，图例也隐藏
                    vis.extend([False] * N_TRACES)
                    showlegend.extend([False] * N_TRACES)
            if(len(company_name) > 20):
                company_name = company_name[:17] + '...'
            ticker_buttons.append(dict(
                label=company_name,
                method='update',
                args=[
                    {
                        'visible': vis,
                        'showlegend': showlegend,
                    },
                    {
                        'title': f'<b>{company_name}</b>  |  €{price:.2f}  |  {signal_emoji}',
                    },
                ],
            ))

        # 初始标题
        first = traces_info[0]
        init_title = f'<b>{first[1]}</b>  |  €{first[4]:.2f}  |  {first[3]}'

        fig.update_layout(
            title=init_title,
            height=580,
            template='plotly_white',
            hovermode='x unified',
            xaxis_title='Date',
            yaxis_title='Price (€)',
            # ✅ 图例横排在图表上方，点击可显示/隐藏 SMA
            legend=dict(
                orientation='h',
                yanchor='bottom', y=1.10,
                xanchor='right', x=1,
                itemclick='toggle',        # 单击切换
                itemdoubleclick='toggleothers',  # 双击只显示这条
            ),
            margin=dict(l=50, r=30, t=140, b=50),
            updatemenus=[
                dict(
                    type='dropdown',
                    direction='down',
                    buttons=ticker_buttons,
                    x=0, xanchor='left',
                    y=1.35, yanchor='top',
                    showactive=True,
                    bgcolor='white',
                    bordercolor='#aaaaaa',
                    font=dict(size=13),
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
    'FR001400AJ45',   # MICHELIN
    'FR0000121709',   # SEB
    'FR0000075954'    # RIBER
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