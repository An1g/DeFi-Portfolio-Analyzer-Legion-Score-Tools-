import requests, pandas as pd, matplotlib.pyplot as plt
from datetime import datetime

COINGECKO_MAP = {
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "PENGU": "pengu",
    "LINEA": "linea"
}

def fetch_prices(ids):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ",".join(ids), "vs_currencies": "usd"}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def load_holdings(path="holdings.csv"):
    df = pd.read_csv(path)
    df["symbol"] = df["symbol"].str.upper().str.strip()
    return df

def build_portfolio(df):
    ids = [COINGECKO_MAP[s] for s in df["symbol"] if s in COINGECKO_MAP]
    prices = fetch_prices(ids)

    current = []
    for _, row in df.iterrows():
        sym = row["symbol"]
        if sym in COINGECKO_MAP and COINGECKO_MAP[sym] in prices:
            cur = prices[COINGECKO_MAP[sym]]["usd"]
        else:
            cur = None
        current.append(cur)
    df["price_now"] = current

    df["cost_basis"]  = df["amount"] * df["buy_price_usd"]
    df["value_now"]   = df["amount"] * df["price_now"]
    df["roi_abs"]     = df["value_now"] - df["cost_basis"]
    df["roi_pct"]     = (df["roi_abs"] / df["cost_basis"]) * 100

    totals = {
        "cost_basis": df["cost_basis"].sum(),
        "value_now": df["value_now"].sum(),
        "roi_abs": df["roi_abs"].sum(),
        "roi_pct": (df["value_now"].sum()/df["cost_basis"].sum()-1)*100 if df["cost_basis"].sum()>0 else 0
    }
    return df, totals

def plot_allocation(df, out="portfolio_allocation.png"):
    pie = df.dropna(subset=["value_now"]).copy()
    if pie.empty: 
        return
    pie = pie[pie["value_now"]>0]
    plt.figure(figsize=(6,6))
    plt.title("Portfolio allocation (by current value)")
    plt.pie(pie["value_now"], labels=pie["symbol"], autopct="%1.1f%%")
    plt.tight_layout()
    plt.savefig(out, dpi=160)

def main():
    df = load_holdings()
    df, totals = build_portfolio(df)
    print("\n=== PORTFOLIO ===")
    print(df[["symbol","amount","buy_price_usd","price_now","cost_basis","value_now","roi_pct"]]
            .round(4)
            .to_string(index=False))
    print("\nTotals:", {k: round(v,2) for k,v in totals.items()})
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    out_csv = f"report-{stamp}.csv"
    df.to_csv(out_csv, index=False)
    plot_allocation(df)

if __name__ == "__main__":
    main()
