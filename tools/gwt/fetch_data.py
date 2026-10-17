#!/usr/bin/env python3
"""Market snapshot for the Ghost Wealth terminal.

Writes <out>/data.json (everything the launchpad shows) and <out>/hist/<CODE>.json
(per-security OHLCV used by the GP chart). Stdlib only.

Sources: CNBC quote + chart services, Nasdaq API (profiles, analysts, earnings,
short interest, calendars, per-symbol news), US Treasury yield curve, BLS,
NY Fed reference rates, CNN Fear & Greed, Coinbase Exchange, Federal Reserve.

    python3 fetch_data.py [out_dir]
"""
import concurrent.futures as cf
import csv
import datetime as dt
import html
import io
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
OUT = sys.argv[1] if len(sys.argv) > 1 else "data"
CACHE_S = float(os.environ.get("GWT_CACHE_HOURS", "3")) * 3600  # reuse history/extras younger than this
PROFILE_S = 7 * 86400  # company descriptions rarely change, so keep them a week regardless of CACHE_S
SLOW_S = 10  # log any request slower than this
TODAY = dt.date.today()
NET = {"retry": 0, "slow": 0}  # per-run counters, reported after the slow phases


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def get(url, headers=None, data=None, timeout=25, tries=3):
    err = None
    for i in range(tries):
        t = time.time()
        try:
            h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*"}
            h.update(headers or {})
            req = urllib.request.Request(url, headers=h, data=data)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
            took = time.time() - t
            if took >= SLOW_S:
                NET["slow"] += 1
                log(f"SLOW {took:.1f}s", url[:140])
            return body
        except Exception as e:  # noqa: BLE001
            err = e
            # A 4xx other than 429 will not succeed on retry, so give up at once.
            if isinstance(e, urllib.error.HTTPError) and 400 <= e.code < 500 and e.code != 429:
                break
            if i < tries - 1:
                NET["retry"] += 1
                log(f"RETRY {i + 1} after {time.time() - t:.1f}s", url[:140], e)
            time.sleep(1.2 * (i + 1))
    log("FAIL", url[:140], err)
    return None


def getj(url, **kw):
    b = get(url, **kw)
    try:
        return json.loads(b) if b else None
    except ValueError:
        return None


def num(s):
    """'$1,234.5' / '4.913T' / '0.32%' / 'N/A' -> float or None."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip().replace(",", "").replace("$", "").replace("%", "")
    if s in ("", "N/A", "NA", "--", "-", "UNCH", "&nbsp;"):
        return 0.0 if s == "UNCH" else None
    mult = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}.get(s[-1:].upper())
    if mult:
        s = s[:-1]
    try:
        return float(s) * (mult or 1)
    except ValueError:
        return None


def mil(s):
    """CNBC reports enterprise value, cash and net debt in millions."""
    v = num(s)
    return None if v is None else v * 1e6


def r2(x, n=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(x, n)


def clean(s):
    if s is None:
        return ""
    s = html.unescape(html.unescape(str(s)))
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# --------------------------------------------------------------------------
# Universe
# --------------------------------------------------------------------------
# (code, cnbc symbol, display name, group, decimals)
INSTRUMENTS = [
    # World equity indices
    ("SPX", ".SPX", "S&P 500", "AMER", 2), ("INDU", ".DJI", "Dow Jones Indus.", "AMER", 2),
    ("CCMP", ".IXIC", "Nasdaq Composite", "AMER", 2), ("NDX", ".NDX", "Nasdaq 100", "AMER", 2),
    ("RTY", ".RUT", "Russell 2000", "AMER", 2), ("SPTSX", ".GSPTSE", "S&P/TSX Comp", "AMER", 2),
    ("IBOV", ".BVSP", "Bovespa", "AMER", 0), ("MEXBOL", ".MXX", "Mexico IPC", "AMER", 2),
    ("SX5E", ".STOXX50E", "Euro Stoxx 50", "EMEA", 2), ("UKX", ".FTSE", "FTSE 100", "EMEA", 2),
    ("DAX", ".GDAXI", "DAX", "EMEA", 2), ("CAC", ".FCHI", "CAC 40", "EMEA", 2),
    ("FTSEMIB", ".FTMIB", "FTSE MIB", "EMEA", 2), ("IBEX", ".IBEX", "IBEX 35", "EMEA", 2),
    ("SMI", ".SSMI", "Swiss Market", "EMEA", 2), ("AEX", ".AEX", "AEX", "EMEA", 2),
    ("NKY", ".N225", "Nikkei 225", "APAC", 2), ("HSI", ".HSI", "Hang Seng", "APAC", 2),
    ("SHCOMP", ".SSEC", "Shanghai Comp", "APAC", 2), ("KOSPI", ".KS11", "KOSPI", "APAC", 2),
    ("TWSE", ".TWII", "Taiwan Taiex", "APAC", 2), ("NIFTY", ".NSEI", "Nifty 50", "APAC", 2),
    ("AS51", ".AXJO", "S&P/ASX 200", "APAC", 2), ("STI", ".STI", "Straits Times", "APAC", 2),
    # US equity futures
    ("ES1", "@SP.1", "S&P 500 E-mini", "FUT", 2), ("NQ1", "@ND.1", "Nasdaq 100 E-mini", "FUT", 2),
    ("YM1", "@DJ.1", "Dow E-mini", "FUT", 0), ("RTY1", "@TFS.1", "Russell 2000 E-mini", "FUT", 2),
    # Volatility
    ("VIX", ".VIX", "CBOE VIX", "VOL", 2), ("VIX9D", ".VIX9D", "VIX 9-Day", "VOL", 2),
    ("VIX3M", ".VIX3M", "VIX 3-Month", "VOL", 2), ("VIX6M", ".VIX6M", "VIX 6-Month", "VOL", 2),
    ("MOVE", ".MOVE", "ICE BofA MOVE", "VOL", 2),
    # FX
    ("DXY", ".DXY", "US Dollar Index", "FX", 3), ("EURUSD", "EUR=", "EUR/USD", "FX", 4),
    ("USDJPY", "JPY=", "USD/JPY", "FX", 2), ("GBPUSD", "GBP=", "GBP/USD", "FX", 4),
    ("USDCHF", "CHF=", "USD/CHF", "FX", 4), ("USDCAD", "CAD=", "USD/CAD", "FX", 4),
    ("AUDUSD", "AUD=", "AUD/USD", "FX", 4), ("NZDUSD", "NZD=", "NZD/USD", "FX", 4),
    ("USDCNY", "CNY=", "USD/CNY", "FX", 4), ("USDMXN", "MXN=", "USD/MXN", "FX", 4),
    ("USDINR", "INR=", "USD/INR", "FX", 2), ("USDBRL", "BRL=", "USD/BRL", "FX", 4),
    ("USDKRW", "KRW=", "USD/KRW", "FX", 2), ("EURJPY", "EURJPY=", "EUR/JPY", "FX", 2),
    ("EURGBP", "EURGBP=", "EUR/GBP", "FX", 4),
    # Government bond yields (%)
    ("US1M", "US1M", "UST 1M", "RATES", 3), ("US3M", "US3M", "UST 3M", "RATES", 3),
    ("US6M", "US6M", "UST 6M", "RATES", 3), ("US1Y", "US1Y", "UST 1Y", "RATES", 3),
    ("US2Y", "US2Y", "UST 2Y", "RATES", 3), ("US5Y", "US5Y", "UST 5Y", "RATES", 3),
    ("US7Y", "US7Y", "UST 7Y", "RATES", 3), ("US10Y", "US10Y", "UST 10Y", "RATES", 3),
    ("US20Y", "US20Y", "UST 20Y", "RATES", 3), ("US30Y", "US30Y", "UST 30Y", "RATES", 3),
    ("DE10Y", "DE10Y-DE", "Germany 10Y", "GOVT", 3), ("GB10Y", "GB10Y-GB", "UK 10Y Gilt", "GOVT", 3),
    ("FR10Y", "FR10Y-FR", "France 10Y", "GOVT", 3), ("IT10Y", "IT10Y-IT", "Italy 10Y", "GOVT", 3),
    ("JP10Y", "JP10Y-JP", "Japan 10Y", "GOVT", 3), ("CA10Y", "CA10Y-CA", "Canada 10Y", "GOVT", 3),
    ("AU10Y", "AU10Y-AU", "Australia 10Y", "GOVT", 3), ("CN10Y", "CN10Y-CN", "China 10Y", "GOVT", 3),
    # Commodities (front month)
    ("CL1", "@CL.1", "WTI Crude", "ENERGY", 2), ("CO1", "@LCO.1", "Brent Crude", "ENERGY", 2),
    ("NG1", "@NG.1", "Natural Gas", "ENERGY", 3), ("XB1", "@RB.1", "RBOB Gasoline", "ENERGY", 4),
    ("HO1", "@HO.1", "Heating Oil", "ENERGY", 4),
    ("GC1", "@GC.1", "Gold", "METALS", 1), ("SI1", "@SI.1", "Silver", "METALS", 3),
    ("HG1", "@HG.1", "Copper", "METALS", 4), ("PL1", "@PL.1", "Platinum", "METALS", 1),
    ("PA1", "@PA.1", "Palladium", "METALS", 1),
    ("C1", "@C.1", "Corn", "AGS", 2), ("W1", "@W.1", "Wheat", "AGS", 2),
    ("S1", "@S.1", "Soybeans", "AGS", 2), ("KC1", "@KC.1", "Coffee", "AGS", 2),
    ("SB1", "@SB.1", "Sugar #11", "AGS", 2), ("CC1", "@CC.1", "Cocoa", "AGS", 0),
    ("LC1", "@LC.1", "Live Cattle", "AGS", 3),
]

ETFS = [
    ("SPY", "S&P 500", "BROAD"), ("QQQ", "Nasdaq 100", "BROAD"), ("IWM", "Russell 2000", "BROAD"),
    ("DIA", "Dow 30", "BROAD"), ("RSP", "S&P 500 Equal Wt", "BROAD"),
    ("XLK", "Technology", "SECTOR"), ("XLC", "Comm. Services", "SECTOR"),
    ("XLY", "Cons. Discretionary", "SECTOR"), ("XLP", "Cons. Staples", "SECTOR"),
    ("XLE", "Energy", "SECTOR"), ("XLF", "Financials", "SECTOR"), ("XLV", "Health Care", "SECTOR"),
    ("XLI", "Industrials", "SECTOR"), ("XLB", "Materials", "SECTOR"), ("XLU", "Utilities", "SECTOR"),
    ("XLRE", "Real Estate", "SECTOR"),
    ("SMH", "Semiconductors", "THEME"), ("IGV", "Software", "THEME"), ("XBI", "Biotech", "THEME"),
    ("KRE", "Regional Banks", "THEME"), ("ITB", "Homebuilders", "THEME"), ("ARKK", "ARK Innovation", "THEME"),
    ("IBIT", "Spot Bitcoin", "THEME"),
    ("TLT", "20+Y Treasuries", "XASSET"), ("IEF", "7-10Y Treasuries", "XASSET"),
    ("HYG", "High Yield Corp", "XASSET"), ("LQD", "IG Corp", "XASSET"), ("TIP", "TIPS", "XASSET"),
    ("GLD", "Gold", "XASSET"), ("SLV", "Silver", "XASSET"), ("USO", "Oil", "XASSET"),
    ("EFA", "Developed ex-US", "XASSET"), ("EEM", "Emerging Mkts", "XASSET"), ("FXI", "China Large Cap", "XASSET"),
    ("EWJ", "Japan", "XASSET"),
]

SECTORS = {
    "Information Technology": "AAPL MSFT NVDA AVGO ORCL CRM AMD ADBE CSCO ACN IBM INTC QCOM TXN INTU NOW AMAT MU LRCX KLAC PANW CRWD ANET PLTR SNOW SMCI ARM TSM ASML SHOP MSTR "
                              "MRVL ALAB CRDO MPWR DELL CIEN CLS DDOG NET MDB APP CRWV NBIS SNPS CDNS",
    "Communication Services": "GOOGL META NFLX DIS T VZ TMUS CMCSA",
    "Consumer Discretionary": "AMZN TSLA HD MCD NKE SBUX LOW BKNG TJX CMG RIVN",
    "Consumer Staples": "WMT PG KO PEP COST PM MO MDLZ CL",
    "Energy": "XOM CVX COP SLB OXY EOG",
    "Financials": "BRK.B JPM V MA BAC WFC GS MS C AXP SCHW BLK SPGI PYPL COIN HOOD SOFI",
    "Health Care": "LLY UNH JNJ ABBV MRK PFE TMO ABT AMGN ISRG DHR BMY GILD VRTX NVO TEM",
    "Industrials": "GE CAT BA HON UNP RTX LMT DE UPS UBER GEV VRT ETN",
    "Materials": "LIN FCX NEM",
    "Utilities": "NEE DUK SO CEG VST",
    "Real Estate": "PLD AMT EQIX",
}
STOCKS = [(t, sec) for sec, ts in SECTORS.items() for t in ts.split()]
SECTOR_ETF = {"Information Technology": "XLK", "Communication Services": "XLC",
              "Consumer Discretionary": "XLY", "Consumer Staples": "XLP", "Energy": "XLE",
              "Financials": "XLF", "Health Care": "XLV", "Industrials": "XLI", "Materials": "XLB",
              "Utilities": "XLU", "Real Estate": "XLRE"}
# Words a headline uses for the company (for tagging general news to tickers)
ALIASES = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", "AVGO": "Broadcom", "ORCL": "Oracle",
    "CRM": "Salesforce", "AMD": "AMD", "ADBE": "Adobe", "CSCO": "Cisco", "ACN": "Accenture", "IBM": "IBM",
    "INTC": "Intel", "QCOM": "Qualcomm", "TXN": "Texas Instruments", "INTU": "Intuit", "NOW": "ServiceNow",
    "AMAT": "Applied Materials", "MU": "Micron", "LRCX": "Lam Research", "KLAC": "KLA", "PANW": "Palo Alto",
    "CRWD": "CrowdStrike", "ANET": "Arista", "PLTR": "Palantir", "SNOW": "Snowflake", "SMCI": "Super Micro",
    "ARM": "Arm Holdings", "TSM": "TSMC", "ASML": "ASML", "SHOP": "Shopify", "MSTR": "MicroStrategy|Saylor",
    "GOOGL": "Google|Alphabet", "META": "Meta", "NFLX": "Netflix", "DIS": "Disney", "T": "AT&T",
    "VZ": "Verizon", "TMUS": "T-Mobile", "CMCSA": "Comcast", "AMZN": "Amazon", "TSLA": "Tesla|Musk",
    "HD": "Home Depot", "MCD": "McDonald", "NKE": "Nike", "SBUX": "Starbucks", "LOW": "Lowe's",
    "BKNG": "Booking", "TJX": "TJX", "CMG": "Chipotle", "RIVN": "Rivian", "WMT": "Walmart",
    "PG": "Procter", "KO": "Coca-Cola", "PEP": "PepsiCo", "COST": "Costco", "PM": "Philip Morris",
    "MO": "Altria", "MDLZ": "Mondelez", "CL": "Colgate", "XOM": "Exxon", "CVX": "Chevron",
    "COP": "Conoco", "SLB": "SLB|Schlumberger", "OXY": "Occidental", "EOG": "EOG",
    "BRK.B": "Berkshire|Buffett", "JPM": "JPMorgan|Dimon", "V": "Visa", "MA": "Mastercard",
    "BAC": "Bank of America", "WFC": "Wells Fargo", "GS": "Goldman", "MS": "Morgan Stanley",
    "C": "Citigroup|Citi", "AXP": "American Express|Amex", "SCHW": "Schwab", "BLK": "BlackRock",
    "SPGI": "S&P Global", "PYPL": "PayPal", "COIN": "Coinbase", "HOOD": "Robinhood", "SOFI": "SoFi",
    "LLY": "Eli Lilly|Lilly", "UNH": "UnitedHealth", "JNJ": "Johnson & Johnson|J&J", "ABBV": "AbbVie",
    "MRK": "Merck", "PFE": "Pfizer", "TMO": "Thermo Fisher", "ABT": "Abbott", "AMGN": "Amgen",
    "ISRG": "Intuitive Surgical", "DHR": "Danaher", "BMY": "Bristol", "GILD": "Gilead", "VRTX": "Vertex",
    "NVO": "Novo Nordisk|Novo", "GE": "GE Aerospace", "CAT": "Caterpillar", "BA": "Boeing",
    "HON": "Honeywell", "UNP": "Union Pacific", "RTX": "RTX|Raytheon", "LMT": "Lockheed",
    "DE": "Deere", "UPS": "UPS", "UBER": "Uber", "GEV": "GE Vernova", "LIN": "Linde",
    "FCX": "Freeport", "NEM": "Newmont", "NEE": "NextEra", "DUK": "Duke Energy", "SO": "Southern Co",
    "CEG": "Constellation", "VST": "Vistra", "PLD": "Prologis", "AMT": "American Tower", "EQIX": "Equinix",
    "MRVL": "Marvell", "ALAB": "Astera Labs", "CRDO": "Credo", "MPWR": "Monolithic Power", "DELL": "Dell",
    "CIEN": "Ciena", "CLS": "Celestica", "DDOG": "Datadog", "NET": "Cloudflare", "MDB": "MongoDB",
    "APP": "AppLovin", "CRWV": "CoreWeave", "NBIS": "Nebius", "SNPS": "Synopsys", "CDNS": "Cadence",
    "VRT": "Vertiv", "ETN": "Eaton", "TEM": "Tempus",
}


# --------------------------------------------------------------------------
# CNBC
# --------------------------------------------------------------------------
def cnbc_quotes(symbols):
    out = {}
    for i in range(0, len(symbols), 40):
        chunk = symbols[i:i + 40]
        url = ("https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols="
               + urllib.parse.quote("|".join(chunk), safe="")
               + "&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json")
        d = getj(url)
        try:
            qs = d["FormattedQuoteResult"]["FormattedQuote"]
        except (TypeError, KeyError):
            continue
        for q in qs:
            if q.get("name"):
                out[q["symbol"]] = q
    return out


def cnbc_bars(symbol, rng, tries=5):
    """rng: a chart preset (1Y, 5Y, 5D) or 'D2Y' for two years of daily bars by explicit dates."""
    bars = []
    if rng == "D2Y":
        end = dt.datetime.now()
        url = (f"https://ts-api.cnbc.com/harmony/app/bars/{urllib.parse.quote(symbol, safe='')}/1D/"
               f"{(end - dt.timedelta(days=731)):%Y%m%d}000000/{end:%Y%m%d%H%M%S}/adjusted/EST5EDT.json")
    else:
        url = (f"https://ts-api.cnbc.com/harmony/app/charts/{rng}.json?symbol="
               + urllib.parse.quote(symbol, safe=""))
    for attempt in range(tries):  # the chart service throttles bursts with empty bodies
        d = getj(url)
        try:
            bars = d["barData"]["priceBars"] or []
        except (TypeError, KeyError):
            bars = []
        if bars:
            break
        time.sleep(1.5 * (attempt + 1))
    out = []
    for b in bars:
        t = b.get("tradeTime")
        c = num(b.get("close"))
        if not t or c is None:
            continue
        # tradeTime is exchange-local wall clock; encode it as if UTC so charts show ET/local time
        ts = int(dt.datetime.strptime(t, "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc).timestamp())
        out.append([ts, num(b.get("open")) or c, num(b.get("high")) or c, num(b.get("low")) or c, c,
                    int(b.get("volume") or 0)])
    return out


def cached_hist(code, max_age=None):
    """Reuse a hist file written by a run in the last few hours (fast re-runs)."""
    path = os.path.join(OUT, "hist", f"{code}.json")
    try:
        if time.time() - os.path.getmtime(path) < (max_age or CACHE_S):
            with open(path) as f:
                h = json.load(f)
            if h.get("d"):
                return h["d"], h.get("i") or []
    except (OSError, ValueError):
        pass
    return None


def history(symbol):
    # The 1Y preset errors for some symbols (e.g. .SPX); explicit dates work for all.
    daily = cnbc_bars(symbol, "D2Y", tries=3) or cnbc_bars(symbol, "1Y", tries=2)
    weekly = cnbc_bars(symbol, "5Y")
    intra = cnbc_bars(symbol, "5D")
    return daily, weekly, intra


# --------------------------------------------------------------------------
# Derived analytics
# --------------------------------------------------------------------------
def closes_on_or_before(daily, ts):
    c = None
    for b in daily:
        if b[0] <= ts:
            c = b[4]
        else:
            break
    return c


def pct(a, b):
    return None if a is None or not b else (a / b - 1) * 100


def analytics(daily, last):
    """Returns, moving averages, RSI, realized vol from a daily OHLCV list."""
    if not daily:
        return {}
    cl = [b[4] for b in daily]
    last = last if last is not None else cl[-1]
    end = dt.datetime.fromtimestamp(daily[-1][0], dt.timezone.utc)

    def back(days):
        return closes_on_or_before(daily, int((end - dt.timedelta(days=days)).timestamp()))

    ye = dt.datetime(end.year - 1, 12, 31, 23, 59, tzinfo=dt.timezone.utc)
    prev = cl[-2] if len(cl) > 1 else None
    out = {
        "d1": pct(cl[-1], prev),
        "w1": pct(last, back(7)), "m1": pct(last, back(30)), "m3": pct(last, back(91)),
        "m6": pct(last, back(182)), "ytd": pct(last, closes_on_or_before(daily, int(ye.timestamp()))),
        "y1": pct(last, back(365)),
    }
    yr = daily[-252:]
    out["hi52"] = max(b[2] for b in yr)
    out["lo52"] = min(b[3] for b in yr)
    if len(cl) >= 50:
        out["sma50"] = sum(cl[-50:]) / 50
    if len(cl) >= 200:
        out["sma200"] = sum(cl[-200:]) / 200
    if len(cl) >= 15:
        gains = losses = 0.0
        for a, b in zip(cl[-15:-1], cl[-14:]):
            ch = b - a
            gains += max(ch, 0)
            losses += max(-ch, 0)
        out["rsi"] = 100.0 if losses == 0 else 100 - 100 / (1 + gains / losses)
    rets = [math.log(b / a) for a, b in zip(cl[-31:-1], cl[-30:]) if a and b]
    if len(rets) > 5:
        m = sum(rets) / len(rets)
        out["vol30"] = math.sqrt(sum((r - m) ** 2 for r in rets) / (len(rets) - 1)) * math.sqrt(252) * 100
    vols = [b[5] for b in daily[-21:-1] if b[5]]
    if vols:
        out["avgv20"] = sum(vols) / len(vols)
    return {k: (r2(v, 4) if isinstance(v, float) else v) for k, v in out.items()}


def sanitize(o):
    if isinstance(o, float):
        return None if math.isnan(o) or math.isinf(o) else o
    if isinstance(o, dict):
        return {k: sanitize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [sanitize(v) for v in o]
    return o


def downsample(rows, n):
    if len(rows) <= n:
        return rows
    step = len(rows) / n
    return [rows[int(i * step)] for i in range(n - 1)] + [rows[-1]]


def write_hist(code, daily, weekly, intra, dec):
    def rnd(rows):
        return [[r[0], r2(r[1], dec), r2(r[2], dec), r2(r[3], dec), r2(r[4], dec), r[5]] for r in rows]
    os.makedirs(os.path.join(OUT, "hist"), exist_ok=True)
    with open(os.path.join(OUT, "hist", f"{code}.json"), "w") as f:
        json.dump({"d": rnd(daily), "w": rnd(weekly), "i": rnd(downsample(intra, 600))}, f,
                  separators=(",", ":"))


# --------------------------------------------------------------------------
# Nasdaq extras for single stocks
# --------------------------------------------------------------------------
PROFILES = {}  # ticker -> {ts, desc, industry}; loaded from and saved to .profile-cache.json in main()
NQH = {"Accept": "application/json, text/plain, */*", "Origin": "https://www.nasdaq.com",
       "Referer": "https://www.nasdaq.com/"}


def nasdaq_extras(t):
    try:
        return _nasdaq_extras(t)
    except Exception as e:  # noqa: BLE001 - one bad payload must not sink the snapshot
        log("extras failed", t, e)
        return {}


def _nasdaq_extras(t):
    sym = t.replace(".", "/") if t == "BRK.B" else t
    s = urllib.parse.quote(sym, safe="")
    out = {}
    cached = PROFILES.get(t) or {}
    if time.time() - cached.get("ts", 0) < PROFILE_S:
        out.update({k: cached[k] for k in ("desc", "industry") if k in cached})
    else:
        prof = getj(f"https://api.nasdaq.com/api/company/{s}/company-profile", headers=NQH)
        try:
            desc = clean(prof["data"]["CompanyDescription"]["value"])
            if len(desc) > 900:
                cut = desc[:900].rfind(". ")
                desc = desc[:cut + 1] if cut > 300 else desc[:900] + "…"
            out["desc"] = desc
            out["industry"] = prof["data"]["Industry"]["value"]
            PROFILES[t] = {"ts": time.time(), "desc": desc, "industry": out["industry"]}
        except (TypeError, KeyError):
            # keep last week's profile rather than showing none
            out.update({k: cached[k] for k in ("desc", "industry") if k in cached})
    ed = getj(f"https://api.nasdaq.com/api/analyst/{s}/earnings-date", headers=NQH)
    try:
        txt = clean(ed["data"]["reportText"])
        m = re.search(r"on\s+(\d{2}/\d{2}/\d{4})", txt)
        e = {"text": txt}
        if m:
            e["date"] = dt.datetime.strptime(m.group(1), "%m/%d/%Y").date().isoformat()
        e["when"] = "AMC" if "after market close" in txt else "BMO" if "before market open" in txt else ""
        m = re.search(r"consensus EPS forecast for the quarter is \$?(-?\d+(?:\.\d+)?)", txt)
        if m:
            e["eps"] = float(m.group(1))
        m = re.search(r"same quarter last year was \$?(-?\d+(?:\.\d+)?)", txt)
        if m:
            e["lastEps"] = float(m.group(1))
        e["expected"] = "expected" in txt
        out["earn"] = e
    except (TypeError, KeyError):
        pass
    tp = getj(f"https://api.nasdaq.com/api/analyst/{s}/targetprice", headers=NQH)
    try:
        co = tp["data"]["consensusOverview"]
        hc = tp["data"].get("historicalConsensus") or []
        out["target"] = {"lo": co.get("lowPriceTarget"), "hi": co.get("highPriceTarget"),
                         "mean": co.get("priceTarget"), "buy": co.get("buy"), "hold": co.get("hold"),
                         "sell": co.get("sell"),
                         "rating": (hc[-1].get("z") or {}).get("consensus") if hc else None,
                         "hist": [[h["x"], h["y"]] for h in hc if h.get("y")]}
    except (TypeError, KeyError):
        pass
    si = getj(f"https://api.nasdaq.com/api/quote/{s}/short-interest?assetClass=stocks", headers=NQH)
    try:
        rows = si["data"]["shortInterestTable"]["rows"]
        out["short"] = {"date": rows[0]["settlementDate"], "shares": num(rows[0]["interest"]),
                        "dtc": r2(rows[0]["daysToCover"], 2),
                        "prev": num(rows[1]["interest"]) if len(rows) > 1 else None}
    except (TypeError, KeyError, IndexError):
        pass
    rss = get(f"https://www.nasdaq.com/feed/rssoutbound?symbol={s}", headers={"Accept": "*/*"})
    out["news"] = parse_rss(rss, 8, "Nasdaq")
    return out


def parse_rss(raw, limit, source):
    items = []
    if not raw:
        return items
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return items
    for it in root.iter("item"):
        title = clean(it.findtext("title"))
        link = (it.findtext("link") or "").strip()
        pub = it.findtext("pubDate") or ""
        try:
            ts = int(dt.datetime.strptime(pub.strip()[:25].strip(), "%a, %d %b %Y %H:%M:%S").replace(
                tzinfo=dt.timezone.utc).timestamp())
            m = re.search(r"([+-]\d{4})$", pub.strip())
            if m:
                off = int(m.group(1)[:3]) * 3600 + int(m.group(1)[0] + m.group(1)[3:]) * 60
                ts -= off
        except ValueError:
            ts = None
        desc = clean(it.findtext("description"))[:280]
        if title and link.startswith("http"):
            items.append({"t": ts, "title": title, "link": link, "src": source, "desc": desc})
        if len(items) >= limit:
            break
    return items


# --------------------------------------------------------------------------
# Macro / calendars / sentiment
# --------------------------------------------------------------------------
def treasury_curve():
    rows = []
    for year in (TODAY.year - 1, TODAY.year):
        raw = get("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
                  f"daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve"
                  f"&field_tdr_date_value={year}&page&_format=csv", headers={"Accept": "text/csv"})
        if not raw:
            continue
        rd = csv.DictReader(io.StringIO(raw.decode("utf-8", "replace")))
        for r in rd:
            try:
                d = dt.datetime.strptime(r["Date"], "%m/%d/%Y").date()
            except (KeyError, ValueError):
                continue
            rows.append((d, r))
    rows.sort(key=lambda x: x[0])
    tenors = [("1M", "1 Mo"), ("3M", "3 Mo"), ("6M", "6 Mo"), ("1Y", "1 Yr"), ("2Y", "2 Yr"),
              ("3Y", "3 Yr"), ("5Y", "5 Yr"), ("7Y", "7 Yr"), ("10Y", "10 Yr"), ("20Y", "20 Yr"),
              ("30Y", "30 Yr")]
    if not rows:
        return None

    def at(target):
        best = None
        for d, r in rows:
            if d <= target:
                best = (d, r)
        return best

    def vals(r):
        return [num(r.get(col)) for _, col in tenors]

    last_d, last_r = rows[-1]
    snaps = {"now": (last_d, last_r)}
    for key, days in (("w1", 7), ("m1", 30), ("m6", 182), ("y1", 365)):
        b = at(last_d - dt.timedelta(days=days))
        if b:
            snaps[key] = b
    spreads = []
    for d, r in rows[-260:]:
        y2, y10, m3, y5, y30 = (num(r.get(c)) for c in ("2 Yr", "10 Yr", "3 Mo", "5 Yr", "30 Yr"))
        if None not in (y2, y10, m3):
            spreads.append([d.isoformat(), r2((y10 - y2) * 100, 1), r2((y10 - m3) * 100, 1),
                            r2(((y30 or 0) - (y5 or 0)) * 100, 1), y10, y2])
    return {"tenors": [t for t, _ in tenors],
            "snaps": {k: {"date": d.isoformat(), "v": vals(r)} for k, (d, r) in snaps.items()},
            "spreads": spreads}


BLS_SERIES = {
    "CUUR0000SA0": "CPI", "CUUR0000SA0L1E": "Core CPI", "LNS14000000": "Unemployment",
    "CES0000000001": "Payrolls", "CES0500000003": "Avg Hourly Earnings", "WPUFD4": "PPI Final Demand",
    "LNS11300000": "Participation", "JTS000000000000000JOL": "JOLTS Openings",
}


def bls():
    body = json.dumps({"seriesid": list(BLS_SERIES), "startyear": str(TODAY.year - 3),
                       "endyear": str(TODAY.year)}).encode()
    d = getj("https://api.bls.gov/publicAPI/v2/timeseries/data/", data=body,
             headers={"Content-Type": "application/json"})
    out = {}
    try:
        series = d["Results"]["series"]
    except (TypeError, KeyError):
        return out
    for s in series:
        pts = []
        for p in s["data"]:
            if not p["period"].startswith("M") or p["period"] == "M13":
                continue
            v = num(p["value"])
            if v is not None:
                pts.append([f'{p["year"]}-{p["period"][1:]}', v])
        pts.sort()
        out[s["seriesID"]] = pts
    return out


def nyfed():
    out = {}
    d = getj("https://markets.newyorkfed.org/api/rates/all/latest.json")
    for r in (d or {}).get("refRates", []):
        if r.get("type") in ("EFFR", "SOFR", "OBFR", "TGCR", "BGCR"):
            out[r["type"]] = {"date": r.get("effectiveDate"), "rate": r.get("percentRate"),
                              "lo": r.get("targetRateFrom"), "hi": r.get("targetRateTo"),
                              "vol": r.get("volumeInBillions")}
    for typ, path in (("EFFR", "unsecured/effr"), ("SOFR", "secured/sofr")):
        h = getj(f"https://markets.newyorkfed.org/api/rates/{path}/last/260.json")
        pts = [[r["effectiveDate"], r["percentRate"]] for r in (h or {}).get("refRates", [])
               if r.get("percentRate") is not None]
        if typ in out:
            out[typ]["hist"] = sorted(pts)
    return out


def fear_greed():
    d = getj("https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
             headers={"Referer": "https://www.cnn.com/", "Origin": "https://www.cnn.com"})
    if not d:
        return None
    fg = d.get("fear_and_greed", {})
    comps = {}
    names = {"market_momentum_sp500": "Market momentum", "stock_price_strength": "Price strength",
             "stock_price_breadth": "Price breadth", "put_call_options": "Put/call options",
             "market_volatility_vix": "Volatility", "junk_bond_demand": "Junk bond demand",
             "safe_haven_demand": "Safe-haven demand"}
    for k, label in names.items():
        c = d.get(k) or {}
        if "score" in c:
            comps[k] = {"label": label, "score": r2(c["score"], 1), "rating": c.get("rating")}
    hist = [[int(p["x"] / 1000), r2(p["y"], 1)] for p in
            (d.get("fear_and_greed_historical") or {}).get("data", [])]
    return {"score": r2(fg.get("score"), 1), "rating": fg.get("rating"),
            "prev": r2(fg.get("previous_close"), 1), "w1": r2(fg.get("previous_1_week"), 1),
            "m1": r2(fg.get("previous_1_month"), 1), "y1": r2(fg.get("previous_1_year"), 1),
            "ts": fg.get("timestamp"), "comps": comps, "hist": downsample(hist, 260)}


def weekdays(start, end):
    d = start
    while d <= end:
        if d.weekday() < 5:
            yield d
        d += dt.timedelta(days=1)


def econ_calendar():
    rows = []
    start = TODAY - dt.timedelta(days=TODAY.weekday() + 7)  # Monday of last week
    end = start + dt.timedelta(days=18)

    def day(d):
        j = getj(f"https://api.nasdaq.com/api/calendar/economicevents?date={d.isoformat()}", headers=NQH)
        out = []
        for r in ((j or {}).get("data") or {}).get("rows") or []:
            out.append({"date": d.isoformat(), "gmt": clean(r.get("gmt")), "c": clean(r.get("country")),
                        "e": clean(r.get("eventName")), "a": clean(r.get("actual")),
                        "f": clean(r.get("consensus")), "p": clean(r.get("previous"))})
        return out

    with cf.ThreadPoolExecutor(4) as ex:
        for res in ex.map(day, list(weekdays(start, end))):
            rows.extend(res)
    return rows


def earnings_calendar():
    rows = []
    start = TODAY - dt.timedelta(days=TODAY.weekday() + 7)
    end = TODAY + dt.timedelta(days=14)

    def day(d):
        j = getj(f"https://api.nasdaq.com/api/calendar/earnings?date={d.isoformat()}", headers=NQH)
        out = []
        for r in ((j or {}).get("data") or {}).get("rows") or []:
            mc = num(r.get("marketCap"))
            if not mc or mc < 5e9:
                continue
            out.append({"date": d.isoformat(), "sym": r.get("symbol"), "n": clean(r.get("name")),
                        "when": {"time-pre-market": "BMO", "time-after-hours": "AMC"}.get(r.get("time"), ""),
                        "mc": mc, "eps": num(r.get("epsForecast")), "ests": num(r.get("noOfEsts")),
                        "q": r.get("fiscalQuarterEnding"), "ly": num(r.get("lastYearEPS"))})
        return out

    with cf.ThreadPoolExecutor(4) as ex:
        for res in ex.map(day, list(weekdays(start, end))):
            rows.extend(res)
    return rows


def fomc():
    raw = get("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", headers={"Accept": "text/html"})
    if not raw:
        return []
    t = raw.decode("utf-8", "replace")
    out = []
    for year in (TODAY.year, TODAY.year + 1):
        i = t.find(f"{year} FOMC Meetings")
        if i < 0:
            continue
        j = t.find("FOMC Meetings", i + 20)
        seg = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t[i:j if j > 0 else i + 20000])))
        for m in re.finditer(r"(January|February|March|April|May|June|July|August|September|October|"
                             r"November|December)(?:/\w+)?\s+(\d{1,2})-(\d{1,2})(\*?)", seg):
            try:
                d = dt.datetime.strptime(f"{m.group(1)} {m.group(3)} {year}", "%B %d %Y").date()
            except ValueError:
                continue
            out.append({"date": d.isoformat(), "label": f"{m.group(1)[:3]} {m.group(2)}–{m.group(3)}",
                        "sep": bool(m.group(4))})
    # keep a strictly increasing run (the page also lists tentative later-year dates)
    kept = []
    for f in out:
        if not kept or f["date"] > kept[-1]["date"]:
            kept.append(f)
    return kept


CNBC_FEEDS = [("TOP", "100003114"), ("MARKETS", "15839069"), ("ECONOMY", "20910258"),
              ("EARNINGS", "15839135"), ("TECH", "19854910"), ("FINANCE", "10000664"),
              ("ENERGY", "19836768"), ("WORLD", "100727362")]


def news():
    out, seen = [], set()

    def feed(arg):
        sec, fid = arg
        raw = get(f"https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id={fid}",
                  headers={"Accept": "application/rss+xml, */*"})
        return sec, parse_rss(raw, 40, "CNBC")

    with cf.ThreadPoolExecutor(4) as ex:
        for sec, items in ex.map(feed, CNBC_FEEDS):
            for it in items:
                if it["link"] in seen:
                    continue
                seen.add(it["link"])
                it["sec"] = sec
                out.append(it)
    out.sort(key=lambda x: x["t"] or 0, reverse=True)
    return out


# (Coinbase base currency, name, theme). Majors plus mid and small caps across sectors.
COINBASE = [
    ("BTC", "Bitcoin", "Store of value"), ("ETH", "Ether", "Smart contracts"), ("SOL", "Solana", "Layer 1"),
    ("XRP", "XRP", "Payments"), ("BNB", "BNB", "Exchange chain"), ("DOGE", "Dogecoin", "Meme"),
    ("ADA", "Cardano", "Layer 1"), ("HYPE", "Hyperliquid", "DeFi exchange"), ("LINK", "Chainlink", "Oracle"),
    ("AVAX", "Avalanche", "Layer 1"), ("SUI", "Sui", "Layer 1"), ("XLM", "Stellar", "Payments"),
    ("BCH", "Bitcoin Cash", "Payments"), ("HBAR", "Hedera", "Layer 1"), ("TON", "Toncoin", "Layer 1"),
    ("LTC", "Litecoin", "Payments"), ("DOT", "Polkadot", "Layer 1"), ("NEAR", "NEAR", "AI / Layer 1"),
    ("APT", "Aptos", "Layer 1"), ("ICP", "Internet Computer", "AI / compute"), ("ETC", "Ethereum Classic", "Layer 1"),
    ("ATOM", "Cosmos", "Interop"), ("SEI", "Sei", "Layer 1"), ("TIA", "Celestia", "Modular"),
    ("INJ", "Injective", "DeFi chain"), ("ARB", "Arbitrum", "Layer 2"), ("OP", "Optimism", "Layer 2"),
    ("STX", "Stacks", "Bitcoin L2"), ("POL", "Polygon", "Layer 2"), ("ALGO", "Algorand", "Layer 1"),
    ("XTZ", "Tezos", "Layer 1"),
    ("TAO", "Bittensor", "AI"), ("FET", "Artificial Superintelligence", "AI agents"), ("RENDER", "Render", "AI / GPU"),
    ("VIRTUAL", "Virtuals Protocol", "AI agents"), ("AKT", "Akash", "AI / GPU cloud"), ("GRT", "The Graph", "AI / data"),
    ("WLD", "Worldcoin", "AI identity"), ("IO", "io.net", "AI / GPU"), ("KAITO", "Kaito", "AI / data"),
    ("AIOZ", "AIOZ Network", "AI / DePIN"),
    ("UNI", "Uniswap", "DeFi"), ("AAVE", "Aave", "DeFi lending"), ("ONDO", "Ondo", "Tokenized assets"),
    ("ENA", "Ethena", "DeFi"), ("PENDLE", "Pendle", "DeFi"), ("MORPHO", "Morpho", "DeFi lending"),
    ("JTO", "Jito", "Staking"), ("PYTH", "Pyth", "Oracle"), ("LDO", "Lido", "Staking"),
    ("EIGEN", "EigenLayer", "Restaking"), ("CRV", "Curve", "DeFi"),
    ("SHIB", "Shiba Inu", "Meme"), ("PEPE", "Pepe", "Meme"), ("BONK", "Bonk", "Meme"), ("WIF", "dogwifhat", "Meme"),
    ("FLOKI", "Floki", "Meme"), ("PENGU", "Pudgy Penguins", "Meme"), ("FARTCOIN", "Fartcoin", "Meme"),
    ("TRUMP", "Official Trump", "Meme"),
    ("HNT", "Helium", "DePIN"), ("FIL", "Filecoin", "Storage"), ("ZEC", "Zcash", "Privacy"),
    ("IMX", "Immutable", "Gaming"), ("QNT", "Quant", "Interop"), ("ZRO", "LayerZero", "Interop"),
    ("JASMY", "JasmyCoin", "IoT data"),
]


def price_dec(x):
    x = abs(x or 0)
    return 2 if x >= 1 else 4 if x >= 0.01 else 6 if x >= 0.0001 else 8


def crypto(item):
    code, name, theme = item
    p = f"{code}-USD"
    st = getj(f"https://api.exchange.coinbase.com/products/{p}/stats")
    if not st:
        return None
    candles = getj(f"https://api.exchange.coinbase.com/products/{p}/candles?granularity=86400") or []
    hourly = getj(f"https://api.exchange.coinbase.com/products/{p}/candles?granularity=3600") or []
    to_rows = lambda cs: sorted([[int(c[0]), c[3], c[2], c[1], c[4], c[5]] for c in cs])
    daily, intra = to_rows(candles), to_rows(hourly)[-120:]
    last, opn = num(st.get("last")), num(st.get("open"))
    if not last:
        return None
    dec = price_dec(last)
    write_hist(code, [r[:5] + [int(r[5])] for r in daily], [], [r[:5] + [int(r[5])] for r in intra], dec)
    a = analytics(daily, last)
    cl = [r[4] for r in daily]
    vol24 = (num(st.get("volume")) or 0) * last
    usd_vols = [r[5] * r[4] for r in daily[-31:-1]]  # completed days only
    avg30 = sum(usd_vols) / len(usd_vols) if usd_vols else None
    return code, {"n": name, "theme": theme, "g": "CRYPTO", "last": last,
                  "chg": r2(last - opn, dec) if opn else None, "pct": r2(pct(last, opn), 3),
                  "high": num(st.get("high")), "low": num(st.get("low")), "vol": r2(vol24, 0),
                  "avgVol30": r2(avg30, 0), "volRatio": r2(vol24 / avg30, 2) if avg30 else None,
                  "sma20": r2(sum(cl[-20:]) / 20, dec + 2) if len(cl) >= 20 else None,
                  "hi90": max(r[2] for r in daily[-90:]) if daily else None,
                  "lo90": min(r[3] for r in daily[-90:]) if daily else None,
                  "dec": dec, "spark": [r2(b[4], dec) for b in daily[-60:]],
                  "closes": [[b[0], r2(b[4], dec)] for b in daily[-260:]], **a, "src": "Coinbase"}


def coingecko():
    """Market cap, rank and all-time-high context for the top 500 coins, plus global stats."""
    out, best = {}, {}
    for page in (1, 2):
        rows = getj("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc"
                    f"&per_page=250&page={page}&price_change_percentage=7d,30d") or []
        for r in rows:
            sym = (r.get("symbol") or "").upper()
            mc = r.get("market_cap") or 0
            if sym and mc > best.get(sym, -1):
                best[sym] = mc
                out[sym] = {"mcap": mc, "rank": r.get("market_cap_rank"), "fdv": r.get("fully_diluted_valuation"),
                            "gvol": r.get("total_volume"),
                            "ath": r.get("ath"), "athPct": r2(r.get("ath_change_percentage"), 1),
                            "athDate": (r.get("ath_date") or "")[:10], "circ": r.get("circulating_supply"),
                            "maxSupply": r.get("max_supply"), "cgId": r.get("id")}
        time.sleep(1.5)
    g = (getj("https://api.coingecko.com/api/v3/global") or {}).get("data") or {}
    glob = {"totalMcap": (g.get("total_market_cap") or {}).get("usd"),
            "totalVol": (g.get("total_volume") or {}).get("usd"),
            "mcapChg24": r2(g.get("market_cap_change_percentage_24h_usd"), 2),
            "btcDom": r2((g.get("market_cap_percentage") or {}).get("btc"), 2),
            "ethDom": r2((g.get("market_cap_percentage") or {}).get("eth"), 2)}
    return out, glob


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    stock_syms = [t for t, _ in STOCKS]
    etf_syms = [t for t, _, _ in ETFS]
    log("quotes…")
    quotes = cnbc_quotes([s for _, s, *_ in INSTRUMENTS] + etf_syms + stock_syms)
    log(f"  {len(quotes)} quotes")

    jobs = [(c, s, d) for c, s, _, _, d in INSTRUMENTS] + [(t, t, 2) for t in etf_syms + stock_syms]
    hists = {}

    def hjob(j):
        code, sym, dec = j
        hit = cached_hist(code)
        if hit:
            return code, hit[0], hit[1]
        daily, weekly, intra = history(sym)
        if daily:
            write_hist(code, daily, weekly, intra, dec)
        return code, daily, intra

    log("history…")
    with cf.ThreadPoolExecutor(5) as ex:
        for code, daily, intra in ex.map(hjob, jobs):
            hists[code] = (daily, intra)
    log(f"  {sum(1 for v in hists.values() if v[0])} with daily bars ({time.time() - t0:.0f}s)")

    def base(code, sym, dec):
        q = quotes.get(sym, {})
        daily, intra = hists.get(code, ([], []))
        last = num(q.get("last"))
        if last is None and daily:
            last = daily[-1][4]
        a = analytics(daily, last)
        prev = num(q.get("previous_day_closing"))
        chg, pc = num(q.get("change")), num(q.get("change_pct"))
        # Futures/commodities show UNCH vs settlement on weekends: fall back to last two daily closes
        if (not chg) and daily and len(daily) > 1:
            prev = daily[-2][4]
            chg = last - prev if last is not None else None
            pc = pct(last, prev)
        session = [b for b in intra if dt.datetime.fromtimestamp(b[0], dt.timezone.utc).date()
                   == dt.datetime.fromtimestamp(intra[-1][0], dt.timezone.utc).date()] if intra else []
        return {"last": last, "chg": r2(chg, dec + 1), "pct": r2(pc, 3), "prev": prev,
                "open": num(q.get("open")), "high": num(q.get("high")), "low": num(q.get("low")),
                "vol": num(q.get("volume")), "time": q.get("last_time"), "dec": dec,
                "spark": [r2(b[4], dec) for b in daily[-60:]],
                "intra": [r2(b[4], dec) for b in downsample(session, 80)],
                "closes": [[b[0], r2(b[4], dec)] for b in daily[-260:]],
                **a}

    instruments = {}
    for code, sym, name, group, dec in INSTRUMENTS:
        if sym not in quotes and not hists.get(code, ([], []))[0]:
            log("  skip", code)
            continue
        instruments[code] = {"n": name, "g": group, "sym": sym, **base(code, sym, dec), "src": "CNBC"}

    log("crypto…")
    with cf.ThreadPoolExecutor(4) as ex:
        for res in ex.map(crypto, COINBASE):
            if res:
                instruments[res[0]] = res[1]
    cg, crypto_global = coingecko()
    for code, _, _ in COINBASE:
        if code in instruments and code in cg:
            instruments[code].update(cg[code])
    log(f"  {sum(1 for c, _, _ in COINBASE if c in instruments)} coins, {sum(1 for c, _, _ in COINBASE if c in cg)} with CoinGecko data")

    etfs = {}
    for t, name, group in ETFS:
        q = quotes.get(t, {})
        etfs[t] = {"n": name, "full": q.get("name"), "g": group, **base(t, t, 2), "src": "CNBC"}

    log("nasdaq extras…")
    cache_path = os.path.join(OUT, ".extras-cache.json")
    try:
        with open(cache_path) as f:
            extras = json.load(f) if time.time() - os.path.getmtime(cache_path) < CACHE_S else {}
    except (OSError, ValueError):
        extras = {}
    prof_path = os.path.join(OUT, ".profile-cache.json")
    try:
        with open(prof_path) as f:
            PROFILES.update(json.load(f))
    except (OSError, ValueError):
        pass
    todo = [t for t in stock_syms if not extras.get(t)]
    t1, n0 = time.time(), dict(NET)
    with cf.ThreadPoolExecutor(4) as ex:
        for t, res in zip(todo, ex.map(nasdaq_extras, todo)):
            extras[t] = res
    with open(cache_path, "w") as f:
        json.dump(extras, f)
    with open(prof_path, "w") as f:
        json.dump(PROFILES, f)
    log(f"  done ({time.time() - t0:.0f}s) · {len(todo)} stocks in {time.time() - t1:.0f}s"
        f" · {NET['retry'] - n0['retry']} retries · {NET['slow'] - n0['slow']} slow requests")

    stocks = {}
    for t, sector in STOCKS:
        q = quotes.get(t)
        if not q:
            log("  missing quote", t)
            continue
        b = base(t, t, 2)
        mcap = num(q.get("mktcapView"))
        shares = num(q.get("sharesout"))
        ex_ = extras.get(t, {})
        si = ex_.get("short")
        if si and shares and si.get("shares"):
            si["pctOut"] = r2(si["shares"] / shares * 100, 2)
        stocks[t] = {
            "n": q.get("name"), "sector": sector, "etf": SECTOR_ETF[sector],
            "ind": ex_.get("industry"), "alias": ALIASES.get(t, t), **b,
            "mcap": mcap, "pe": num(q.get("pe")), "fpe": num(q.get("fpe")), "eps": num(q.get("eps")),
            "feps": num(q.get("feps")), "beta": num(q.get("beta")), "dy": num(q.get("dividendyield")),
            "div": num(q.get("dividend")), "roe": num(q.get("ROETTM")), "gm": num(q.get("GROSMGNTTM")),
            "nm": num(q.get("NETPROFTTM")), "rev": num(q.get("revenuettm")), "ebitda": num(q.get("TTMEBITD")),
            "de": num(q.get("DEBTEQTYQ")), "ev": mil(q.get("enterpriseValue")), "ps": num(q.get("psales")),
            "fps": num(q.get("fpsales")), "cash": mil(q.get("cashmrq")), "netDebt": mil(q.get("netDebtttm")),
            "shares": shares, "avgv10": num(q.get("tendayavgvol")), "exch": q.get("exchange"),
            "hi52d": q.get("yrhidate"), "lo52d": q.get("yrlodate"),
            "ext": {k: q["ExtendedMktQuote"].get(k) for k in ("last", "change", "change_pct", "type", "last_time")}
            if isinstance(q.get("ExtendedMktQuote"), dict) else None,
            "desc": ex_.get("desc"), "earn": ex_.get("earn"), "target": ex_.get("target"),
            "short": si, "news": ex_.get("news") or [], "src": "CNBC · Nasdaq",
        }

    log("macro…")
    with cf.ThreadPoolExecutor(8) as ex:
        f_curve, f_bls, f_fed, f_fg, f_eco, f_earn, f_news, f_fomc = (
            ex.submit(treasury_curve), ex.submit(bls), ex.submit(nyfed), ex.submit(fear_greed),
            ex.submit(econ_calendar), ex.submit(earnings_calendar), ex.submit(news), ex.submit(fomc))
    bls_raw = f_bls.result()
    macro = {sid: {"n": BLS_SERIES[sid], "pts": pts[-40:]} for sid, pts in bls_raw.items()}

    mkt_date = None
    if hists.get("SPX", ([], []))[0]:
        mkt_date = dt.datetime.fromtimestamp(hists["SPX"][0][-1][0], dt.timezone.utc).date().isoformat()
    data = {
        "meta": {"asOf": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                 "marketDate": mkt_date, "build": int(time.time() - t0)},
        "instruments": instruments, "etfs": etfs, "stocks": stocks,
        "curve": f_curve.result(), "macro": macro, "fed": f_fed.result(), "fg": f_fg.result(),
        "eco": f_eco.result(), "earn": f_earn.result(), "news": f_news.result()[:220],
        "fomc": f_fomc.result(), "cryptoGlobal": crypto_global,
    }
    with open(os.path.join(OUT, "data.json"), "w") as f:
        json.dump(sanitize(data), f, separators=(",", ":"), allow_nan=False, default=str)
    log(f"wrote {OUT}/data.json · {len(instruments)} instruments · {len(etfs)} ETFs · "
        f"{len(stocks)} stocks · {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
