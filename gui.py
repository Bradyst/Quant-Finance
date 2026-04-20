"""
MILESTONE 4 - Implementing full GUI, so that every feature is
accessible through the interface and output is displayed in
various formats.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as mticker
import pandas as pd

from portfolioInput import validate_tickers, normalize_weights
from dataFetch import fetch_close
from cleaning import align_and_clean_prices
from basicMetrics import compute_daily_returns, compute_portfolio_returns, basic_summary
from riskMetrics import portfolio_risk_summary

#color pallette
BG        = "#f0f2f5"
SIDEBAR   = "#1e293b"
CARD      = "#ffffff"
PRIMARY   = "#2563eb"
PRIMARY_H = "#1d4ed8"
TEXT_DARK = "#1e293b"
TEXT_MID  = "#475569"
TEXT_LITE = "#94a3b8"
BORDER    = "#e2e8f0"
GREEN     = "#16a34a"
AMBER     = "#d97706"
RED_C     = "#dc2626"
FONT      = "Helvetica"

#UI helpers

def _card(parent, **kw):
    return tk.Frame(parent, bg=CARD, relief="flat",
                    highlightthickness=1, highlightbackground=BORDER, **kw)

def _label(parent, text, size=11, bold=False, color=TEXT_DARK, **kw):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, font=(FONT, size, weight),
                    fg=color, bg=parent["bg"], **kw)

def _entry(parent, textvariable=None, width=28, **kw):
    defaults = dict(font=(FONT, 11), relief="flat",
                    highlightthickness=1, highlightbackground=BORDER,
                    highlightcolor=PRIMARY, bg="#f8fafc", fg=TEXT_DARK,
                    insertbackground=TEXT_DARK)
    defaults.update(kw)
    e = tk.Entry(parent, textvariable=textvariable, width=width, **defaults)
    return e


#main app

class PortfolioApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Portfolio Risk Analyzer")
        self.root.geometry("1380x860")
        self.root.minsize(1100, 720)
        self.root.configure(bg=BG)
        self._results = None
        self._build()

    #layout

    def _build(self):
        #top bar
        bar = tk.Frame(self.root, bg=SIDEBAR, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        _label(bar, "  Portfolio Risk Analyzer", size=14, bold=True,
               color="white").pack(side="left", padx=8, pady=12)
        _label(bar, "Data from Yahoo Finance  ",
               size=9, color="#94a3b8").pack(side="right", padx=8)

        #body
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)

        #sidebar
        sidebar = tk.Frame(body, bg=SIDEBAR, width=320)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        #main content
        content = tk.Frame(body, bg=BG)
        content.pack(side="left", fill="both", expand=True, padx=18, pady=14)
        self._build_content(content)

    def _build_sidebar(self, parent):
        wrap = tk.Frame(parent, bg=SIDEBAR, padx=18, pady=16)
        wrap.pack(fill="both", expand=True)

        _label(wrap, "Portfolio Setup", size=12, bold=True,
               color="white").pack(anchor="w", pady=(0, 14))

        #tickers
        _label(wrap, "Tickers  (comma separated)", size=9,
               color=TEXT_LITE).pack(anchor="w")
        self.var_tickers = tk.StringVar(value="AAPL, MSFT, GOOGL") #default tickers
        _entry(wrap, textvariable=self.var_tickers,
               bg="#1e293b", fg="white", highlightbackground="#334155",
               highlightcolor=PRIMARY, insertbackground="white"
               ).pack(fill="x", pady=(3, 10))

        #allocation mode selection (equal weights, custom weights, or shares)
        _label(wrap, "Allocation Mode", size=9, color=TEXT_LITE).pack(anchor="w")
        self.var_mode = tk.StringVar(value="equal") #default mode is equal weights
        modes = tk.Frame(wrap, bg=SIDEBAR)
        modes.pack(fill="x", pady=(3, 10))
        for text, val in [("Equal Weight", "equal"),
                          ("Custom Weights", "weights"),
                          ("Shares", "shares")]:
            tk.Radiobutton(modes, text=text, variable=self.var_mode, value=val,
                           command=self._on_mode_change,
                           font=(FONT, 10), fg="white", bg=SIDEBAR,
                           selectcolor="#2563eb", activebackground=SIDEBAR,
                           activeforeground="white", cursor="hand2",
                           ).pack(anchor="w")

        #values
        self.lbl_values = _label(wrap, "Weights  (match ticker order)", size=9,
                                 color=TEXT_LITE)
        self.lbl_values.pack(anchor="w")
        self.var_values = tk.StringVar(value="")
        self.ent_values = _entry(wrap, textvariable=self.var_values,
                                 bg="#1e293b", fg="white",
                                 highlightbackground="#334155",
                                 highlightcolor=PRIMARY,
                                 insertbackground="white")
        self.ent_values.pack(fill="x", pady=(3, 10))
        self.lbl_values_hint = _label(wrap, "Leave blank for equal weight",
                                      size=8, color="#64748b")
        self.lbl_values_hint.pack(anchor="w", pady=(0, 10))
        self._on_mode_change()

        #historical period options
        _label(wrap, "Historical Period", size=9, color=TEXT_LITE).pack(anchor="w")
        self.var_period = tk.StringVar(value="5y") #default historical period set to 5 years
        periods = ["1y", "2y", "3y", "5y", "10y"]
        period_frame = tk.Frame(wrap, bg=SIDEBAR)
        period_frame.pack(fill="x", pady=(3, 10))
        for p in periods:
            tk.Radiobutton(period_frame, text=p, variable=self.var_period, value=p,
                           font=(FONT, 10), fg="white", bg=SIDEBAR,
                           selectcolor="#2563eb", activebackground=SIDEBAR,
                           activeforeground="white", cursor="hand2",
                           ).pack(side="left", padx=(0, 6))

        #risk-free rate
        _label(wrap, "Risk-Free Rate (%)", size=9, color=TEXT_LITE).pack(anchor="w")
        self.var_rf = tk.StringVar(value="3.5") #default risk-free rate set to 3.5%
        _entry(wrap, textvariable=self.var_rf, width=10,
               bg="#1e293b", fg="white", highlightbackground="#334155",
               highlightcolor=PRIMARY, insertbackground="white"
               ).pack(anchor="w", pady=(3, 14))

        #run analysis button
        self.btn_run = tk.Button(
            wrap, text="▶  Run Analysis", command=self._run,
            font=(FONT, 12, "bold"), fg="white", bg=PRIMARY,
            activebackground=PRIMARY_H, activeforeground="white",
            relief="flat", cursor="hand2", padx=14, pady=10,
        )
        self.btn_run.pack(fill="x", pady=(0, 12))

        #status
        self.var_status = tk.StringVar(value="Ready")
        self.lbl_status = tk.Label(wrap, textvariable=self.var_status,
                                   font=(FONT, 9), fg=TEXT_LITE, bg=SIDEBAR,
                                   wraplength=260, justify="left")
        self.lbl_status.pack(anchor="w")

        #example input format (makes it clear for users)
        tk.Frame(wrap, bg="#334155", height=1).pack(fill="x", pady=16)
        _label(wrap, "Example:", size=9, bold=True, color=TEXT_LITE).pack(anchor="w")
        hint = "Tickers:  AAPL, MSFT, TSLA\nWeights:  0.5, 0.3, 0.2\nPeriod:   5y\nRF Rate:  3.5"
        _label(wrap, hint, size=9, color="#64748b").pack(anchor="w", pady=(3, 0))

    def _build_content(self, parent):
        #metric cards
        self.cards_frame = tk.Frame(parent, bg=BG)
        self.cards_frame.pack(fill="x", pady=(0, 14))
        self._build_placeholder_cards()

        #notebook style for chart selecting tab
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", font=(FONT, 10, "bold"),
                        padding=(14, 7), background=BORDER,
                        foreground=TEXT_MID)
        style.map("TNotebook.Tab",
                  background=[("selected", CARD)],
                  foreground=[("selected", PRIMARY)])

        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True)

        self.tab_returns   = tk.Frame(self.notebook, bg=BG)
        self.tab_volatility = tk.Frame(self.notebook, bg=BG)
        self.tab_corr      = tk.Frame(self.notebook, bg=BG)
        self.tab_weights   = tk.Frame(self.notebook, bg=BG)
        self.tab_data      = tk.Frame(self.notebook, bg=BG)

        self.notebook.add(self.tab_returns,    text="  Cumulative Returns  ")
        self.notebook.add(self.tab_volatility, text="  Asset Volatility  ")
        self.notebook.add(self.tab_corr,       text="  Correlation Matrix  ")
        self.notebook.add(self.tab_weights,    text="  Portfolio Weights  ")
        self.notebook.add(self.tab_data,       text="  Raw Statistics  ")

        self._show_empty_tabs()

    #empty tabs
    def _show_empty_tabs(self):
        for tab in [self.tab_returns, self.tab_volatility,
                    self.tab_corr, self.tab_weights, self.tab_data]:
            for w in tab.winfo_children():
                w.destroy()
            tk.Label(tab, text="Run an analysis to see results here.",
                     font=(FONT, 12), fg=TEXT_LITE, bg=BG).pack(expand=True)

    #update input hints based on allocation mode
    def _on_mode_change(self):
        mode = self.var_mode.get()
        if mode == "equal":
            self.lbl_values.config(text="Weights  (not needed for equal weight)")
            self.lbl_values_hint.config(text="Weights are auto-calculated equally")
            self.ent_values.config(state="disabled")
        elif mode == "weights":
            self.lbl_values.config(text="Weights  (decimals, match ticker order, and must add to 1)")
            self.lbl_values_hint.config(text='e.g. "0.5, 0.3, 0.2"  — auto-normalised')
            self.ent_values.config(state="normal")
        else:
            self.lbl_values.config(text="Shares  (match ticker order)")
            self.lbl_values_hint.config(text='e.g. "10, 25, 5"  — converted to weights')
            self.ent_values.config(state="normal")

    #top card placeholders

    def _build_placeholder_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()
        placeholders = [
            ("Annualized Return", "—", ""),
            ("Annualized Volatility", "—", ""),
            ("Sharpe Ratio", "—", ""),
            ("Trading Days", "—", ""),
            ("vs. Benchmark (SPY)", "—", ""),
        ]
        for title, val, sub in placeholders:
            c = _card(self.cards_frame, padx=18, pady=14)
            c.pack(side="left", fill="both", expand=True, padx=(0, 10))
            _label(c, title, size=9, color=TEXT_MID).pack(anchor="w")
            _label(c, val, size=20, bold=True, color=TEXT_LITE).pack(anchor="w", pady=(2, 0))
            if sub:
                _label(c, sub, size=9, color=TEXT_LITE).pack(anchor="w")
    #update card values with new data after analysis is ran
    def _refresh_cards(self, risk: dict, summary: dict):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        ann_ret = risk["annualized_return"]
        ann_vol = risk["annualized_volatility"]
        sharpe  = risk["sharpe_ratio"]
        days    = summary["num_days"]
        port_mean = summary["portfolio_mean_daily"]
        bm_mean   = summary["benchmark_mean_daily"]
        excess_ann = (port_mean - bm_mean) * 252

        ret_color  = GREEN if ann_ret >= 0 else RED_C
        sharpe_color = GREEN if sharpe >= 1 else (AMBER if sharpe >= 0 else RED_C)
        exc_color  = GREEN if excess_ann >= 0 else RED_C
        exc_sign   = "+" if excess_ann >= 0 else ""

        metrics = [
            ("Annualized Return",     f"{ann_ret*100:+.2f}%",        "vs 252 trading days",         ret_color),
            ("Annualized Volatility", f"{ann_vol*100:.2f}%",          "std dev × √252",              AMBER),
            ("Sharpe Ratio",          f"{sharpe:.3f}",                 "excess return / volatility",  sharpe_color),
            ("Trading Days",          f"{days:,}",                     "clean data points",           TEXT_DARK),
            ("vs. Benchmark (SPY)",   f"{exc_sign}{excess_ann*100:.2f}%", "annualized excess return",  exc_color),
        ]
        for title, val, sub, color in metrics:
            c = _card(self.cards_frame, padx=18, pady=14)
            c.pack(side="left", fill="both", expand=True, padx=(0, 10))
            _label(c, title, size=9, color=TEXT_MID).pack(anchor="w")
            _label(c, val, size=20, bold=True, color=color).pack(anchor="w", pady=(2, 0))
            _label(c, sub, size=9, color=TEXT_LITE).pack(anchor="w")

    #show placeholder text in tabs before analysis is ran
        for tab in [self.tab_returns, self.tab_volatility,
                    self.tab_corr, self.tab_weights, self.tab_data]:
            for w in tab.winfo_children():
                w.destroy()
            tk.Label(tab, text="Run an analysis to see results here.",
                     font=(FONT, 12), fg=TEXT_LITE, bg=BG).pack(expand=True)

    #analysis run section
    def _set_status(self, msg, color=TEXT_LITE):
        self.var_status.set(msg)
        self.lbl_status.config(fg=color)
    #run analysis
    def _run(self):
        self.btn_run.config(state="disabled", text="Analyzing…")
        self._set_status("Fetching data from Yahoo Finance…")
        threading.Thread(target=self._analysis_worker, daemon=True).start()

    #runs background analysis so that UI doesn't freeze when fetching data
    def _analysis_worker(self):
        try:
            raw_tickers = [t.strip().upper() for t in
                           self.var_tickers.get().split(",") if t.strip()]
            tickers = validate_tickers(raw_tickers)

            mode = self.var_mode.get()
            raw_vals = [v.strip() for v in
                        self.var_values.get().split(",") if v.strip()]

            if mode == "equal":
                n = len(tickers)
                vals = [1.0 / n] * n
            elif mode == "weights":
                if not raw_vals:
                    vals = [1.0 / len(tickers)] * len(tickers)
                else:
                    vals = [float(v) for v in raw_vals]
            else:
                shares = [float(v) for v in raw_vals]
                total  = sum(shares)
                vals   = [s / total for s in shares]

            if len(vals) != len(tickers):
                raise ValueError(
                    f"Got {len(tickers)} tickers but {len(vals)} values.")

            portfolio = pd.DataFrame({"weight": vals}, index=tickers)
            portfolio = normalize_weights(portfolio)
            period = self.var_period.get()
            rf = float(self.var_rf.get()) / 100.0

            self.root.after(0, self._set_status, "Downloading price history…")
            all_tickers = list(tickers) + (["SPY"] if "SPY" not in tickers else [])
            prices_raw = fetch_close(all_tickers, period)

            self.root.after(0, self._set_status, "Cleaning data…")
            prices = align_and_clean_prices(prices_raw)

            self.root.after(0, self._set_status, "Computing returns…")
            returns  = compute_daily_returns(prices)
            port_ret = compute_portfolio_returns(returns, portfolio)
            summary  = basic_summary(returns, port_ret, "SPY")
            risk     = portfolio_risk_summary(returns, port_ret,
                                              list(tickers), rf)

            results = dict(
                tickers=list(tickers),
                portfolio=portfolio,
                prices=prices,
                returns=returns,
                port_ret=port_ret,
                summary=summary,
                risk=risk,
            )
            self.root.after(0, self._display_results, results)

        except Exception as exc:
            self.root.after(0, self._on_error, str(exc))

    def _on_error(self, msg):
        self._set_status(f"Error: {msg}", RED_C)
        self.btn_run.config(state="normal", text="▶  Run Analysis")
        messagebox.showerror("Analysis Error", msg)

    #display results in UI after analysis is complete
    def _display_results(self, r):
        self._results = r
        self._refresh_cards(r["risk"], r["summary"])
        self._tab_returns(r)
        self._tab_volatility(r)
        self._tab_corr(r)
        self._tab_weights(r)
        self._tab_data(r)
        self._set_status(
            f"Analysis complete — {r['summary']['num_days']:,} trading days.", GREEN)
        self.btn_run.config(state="normal", text="▶  Run Analysis")

    #cumulative returns tab
    def _tab_returns(self, r):
        for w in self.tab_returns.winfo_children():
            w.destroy()

        fig = Figure(figsize=(9, 4.5), dpi=100, facecolor=CARD)
        ax  = fig.add_subplot(111)
        ax.set_facecolor("#f8fafc")

        port_cumret = (1 + r["port_ret"]).cumprod() - 1
        ax.plot(port_cumret.index, port_cumret.values * 100,
                color=PRIMARY, linewidth=2, label="Portfolio")

        if "SPY" in r["returns"].columns:
            spy_cumret = (1 + r["returns"]["SPY"]).cumprod() - 1
            ax.plot(spy_cumret.index, spy_cumret.values * 100,
                    color="#94a3b8", linewidth=1.5,
                    linestyle="--", label="SPY (Benchmark)")

        ax.axhline(0, color=BORDER, linewidth=0.8)
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.set_title("Cumulative Return", fontsize=12,
                     fontweight="bold", color=TEXT_DARK, pad=12)
        ax.set_xlabel("Date", fontsize=9, color=TEXT_MID)
        ax.set_ylabel("Return", fontsize=9, color=TEXT_MID)
        ax.tick_params(colors=TEXT_MID, labelsize=8)
        ax.legend(fontsize=9, framealpha=0.7)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.tab_returns)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)

    #asset volatility tab
    def _tab_volatility(self, r):
        for w in self.tab_volatility.winfo_children():
            w.destroy()

        asset_vol = r["risk"]["asset_volatility"]
        port_vol  = r["risk"]["annualized_volatility"]

        fig = Figure(figsize=(9, 4.5), dpi=100, facecolor=CARD)
        ax  = fig.add_subplot(111)
        ax.set_facecolor("#f8fafc")

        tickers = list(asset_vol.index)
        values  = [v * 100 for v in asset_vol.values]
        colors  = [PRIMARY if t in r["tickers"] else "#94a3b8" for t in tickers]

        bars = ax.bar(tickers, values, color=colors, width=0.55, zorder=2)
        ax.axhline(port_vol * 100, color=AMBER, linewidth=1.5,
                   linestyle="--", label=f"Portfolio Vol ({port_vol*100:.1f}%)")

        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, val + 0.3,
                    f"{val:.1f}%", ha="center", va="bottom",
                    fontsize=8, color=TEXT_MID)

        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.set_title("Annualized Volatility by Asset",
                     fontsize=12, fontweight="bold", color=TEXT_DARK, pad=12)
        ax.set_ylabel("Annualized Volatility", fontsize=9, color=TEXT_MID)
        ax.tick_params(colors=TEXT_MID, labelsize=9)
        ax.legend(fontsize=9, framealpha=0.7)
        ax.grid(axis="y", color=BORDER, linewidth=0.6, zorder=0)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.tab_volatility)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)

    #correlation matrix tab
    def _tab_corr(self, r):
        for w in self.tab_corr.winfo_children():
            w.destroy()

        corr = r["risk"]["correlation_matrix"]
        labels = list(corr.columns)
        n = len(labels)

        fig = Figure(figsize=(max(5, n * 0.9 + 1), max(4, n * 0.8 + 1)),
                     dpi=100, facecolor=CARD)
        ax = fig.add_subplot(111)

        im = ax.imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
        fig.colorbar(im, ax=ax, shrink=0.8, label="Correlation")

        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(labels, fontsize=9, color=TEXT_DARK)
        ax.set_yticklabels(labels, fontsize=9, color=TEXT_DARK)
        ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)

        for i in range(n):
            for j in range(n):
                val = corr.values[i, j]
                text_color = "white" if abs(val) > 0.6 else TEXT_DARK
                ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=9, color=text_color, fontweight="bold")

        ax.set_title("Correlation Matrix", fontsize=12,
                     fontweight="bold", color=TEXT_DARK, pad=20)
        fig.tight_layout()

        frame = tk.Frame(self.tab_corr, bg=BG)
        frame.pack(expand=True)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(padx=20, pady=20)

    #portfolio weights tab
    def _tab_weights(self, r):
        for w in self.tab_weights.winfo_children():
            w.destroy()

        portfolio = r["portfolio"]
        tickers   = list(portfolio.index)
        weights   = [portfolio.loc[t, "weight"] for t in tickers]

        fig = Figure(figsize=(7, 4.8), dpi=100, facecolor=CARD)

        palette = [PRIMARY, "#10b981", AMBER, RED_C,
                   "#8b5cf6", "#06b6d4", "#f97316", "#ec4899"]
        colors  = [palette[i % len(palette)] for i in range(len(tickers))]

        ax = fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(
            weights, labels=tickers, autopct="%1.1f%%",
            colors=colors, startangle=140,
            wedgeprops={"edgecolor": "white", "linewidth": 2},
            textprops={"fontsize": 10, "color": TEXT_DARK},
        )
        for at in autotexts:
            at.set_fontsize(9)
            at.set_color("white")
            at.set_fontweight("bold")

        ax.set_title("Portfolio Allocation", fontsize=12,
                     fontweight="bold", color=TEXT_DARK, pad=16)
        fig.tight_layout()

        frame = tk.Frame(self.tab_weights, bg=BG)
        frame.pack(expand=True)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(padx=20, pady=20)

    #raw statistics tab

    def _tab_data(self, r):
        for w in self.tab_data.winfo_children():
            w.destroy()

        risk    = r["risk"]
        summary = r["summary"]
        tickers = r["tickers"]

        scroll = tk.Frame(self.tab_data, bg=BG)
        scroll.pack(fill="both", expand=True, padx=18, pady=12)

        # ── Portfolio summary block ──
        section = _card(scroll, padx=20, pady=16)
        section.pack(fill="x", pady=(0, 10))
        _label(section, "Portfolio Summary", size=11, bold=True,
               color=TEXT_DARK).grid(row=0, column=0, columnspan=4,
                                     sticky="w", pady=(0, 10))

        rows = [
            ("Annualized Return",    f"{risk['annualized_return']*100:+.4f}%"),
            ("Annualized Volatility",f"{risk['annualized_volatility']*100:.4f}%"),
            ("Sharpe Ratio",         f"{risk['sharpe_ratio']:.4f}"),
            ("Mean Daily Return",    f"{summary['portfolio_mean_daily']*100:+.4f}%"),
            ("Daily Std Dev",        f"{summary['portfolio_std_daily']*100:.4f}%"),
            ("Benchmark Daily Mean", f"{summary['benchmark_mean_daily']*100:+.4f}%"),
            ("Benchmark Daily Std",  f"{summary['benchmark_std_daily']*100:.4f}%"),
            ("Trading Days",         f"{summary['num_days']:,}"),
        ]
        for idx, (lbl, val) in enumerate(rows):
            row, col = divmod(idx, 2)
            tk.Label(section, text=lbl + ":", font=(FONT, 10, "bold"),
                     fg=TEXT_MID, bg=CARD, anchor="w", width=26
                     ).grid(row=row+1, column=col*2, sticky="w", padx=(0, 4))
            tk.Label(section, text=val, font=(FONT, 10),
                     fg=TEXT_DARK, bg=CARD, anchor="w"
                     ).grid(row=row+1, column=col*2+1, sticky="w", padx=(0, 30))

        #per asset statistics section
        asset_section = _card(scroll, padx=20, pady=16)
        asset_section.pack(fill="x", pady=(0, 10))
        _label(asset_section, "Per-Asset Statistics",
               size=11, bold=True, color=TEXT_DARK).pack(anchor="w", pady=(0, 10))

        headers = ["Ticker", "Weight", "Ann. Volatility",
                   "Mean Daily Return", "Correlation to Portfolio"]
        header_frame = tk.Frame(asset_section, bg=BORDER)
        header_frame.pack(fill="x")
        widths = [10, 10, 18, 20, 26]
        for h, w in zip(headers, widths):
            tk.Label(header_frame, text=h, font=(FONT, 9, "bold"),
                     fg=TEXT_MID, bg=BORDER, width=w, anchor="w", padx=6
                     ).pack(side="left")

        asset_vol  = risk["asset_volatility"]
        port_ret   = r["port_ret"]
        returns_df = r["returns"]

        for i, ticker in enumerate(tickers):
            row_bg = CARD if i % 2 == 0 else "#f8fafc"
            row_frame = tk.Frame(asset_section, bg=row_bg)
            row_frame.pack(fill="x")

            weight  = r["portfolio"].loc[ticker, "weight"]
            vol     = asset_vol[ticker] * 100 if ticker in asset_vol else float("nan")
            mean_d  = returns_df[ticker].mean() * 100 if ticker in returns_df else float("nan")
            corr_val = (returns_df[ticker].corr(port_ret)
                        if ticker in returns_df else float("nan"))

            row_vals = [
                ticker,
                f"{weight*100:.1f}%",
                f"{vol:.2f}%",
                f"{mean_d:+.4f}%",
                f"{corr_val:.4f}",
            ]
            for val, w in zip(row_vals, widths):
                tk.Label(row_frame, text=val, font=(FONT, 10),
                         fg=TEXT_DARK, bg=row_bg, width=w, anchor="w", padx=6
                         ).pack(side="left")

        #correlation matrix table
        corr_section = _card(scroll, padx=20, pady=16)
        corr_section.pack(fill="x", pady=(0, 10))
        _label(corr_section, "Correlation Matrix (Daily Returns)",
               size=11, bold=True, color=TEXT_DARK).pack(anchor="w", pady=(0, 10))

        corr = risk["correlation_matrix"]
        col_labels = [""] + list(corr.columns)
        hf = tk.Frame(corr_section, bg=BORDER)
        hf.pack(fill="x")
        cw = 10
        for lbl in col_labels:
            tk.Label(hf, text=lbl, font=(FONT, 9, "bold"),
                     fg=TEXT_MID, bg=BORDER, width=cw, anchor="center", padx=4
                     ).pack(side="left")

        for ri, row_lbl in enumerate(corr.index):
            row_bg = CARD if ri % 2 == 0 else "#f8fafc"
            rf2 = tk.Frame(corr_section, bg=row_bg)
            rf2.pack(fill="x")
            tk.Label(rf2, text=row_lbl, font=(FONT, 9, "bold"),
                     fg=TEXT_DARK, bg=row_bg, width=cw, anchor="center", padx=4
                     ).pack(side="left")
            for ci, col_lbl in enumerate(corr.columns):
                val = corr.loc[row_lbl, col_lbl]
                if ri == ci:
                    fg, bg = "white", PRIMARY
                elif abs(val) > 0.6:
                    fg, bg = "white", AMBER
                else:
                    fg, bg = TEXT_DARK, row_bg
                tk.Label(rf2, text=f"{val:.3f}", font=(FONT, 9),
                         fg=fg, bg=bg, width=cw, anchor="center", padx=4
                         ).pack(side="left")


#entry point

if __name__ == "__main__":
    root = tk.Tk()
    app = PortfolioApp(root)
    root.mainloop()
