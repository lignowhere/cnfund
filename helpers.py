# helpers.py (Updated - Minor changes for consistency)
import pandas as pd
def format_currency(x):
    return f"{x:,.0f}đ"

def parse_currency(s):
    if isinstance(s, (int, float)):
        return float(s)
    try:
        return float(s.replace('đ', '').replace(',', ''))
    except (ValueError, AttributeError):
        return None

def get_latest_total_nav(df_transactions):
    df_nav = df_transactions[(df_transactions['NAV'] > 0) & (df_transactions['Type'] != 'Phí')]
    if df_nav.empty:
        return None
    return df_nav.sort_values('Date', ascending=False).iloc[0]['NAV']

def highlight_negative(val):
    try:
        num_val = val
        if isinstance(val, str):
            num_val = parse_currency(val)
        if num_val is not None:
            return 'color: red' if num_val < 0 else 'color: black'
    except:
        return ''
    return ''

def calc_price_per_unit(df_tranches, total_nav):
    total_units = df_tranches['Units'].sum() if not df_tranches.empty else 0
    if total_units == 0:
        return 1000.0
    return total_nav / total_units if total_nav > 0 else 0.0

def calc_balance_profit(inv_tranches, total_nav, df_tranches_global):
    if inv_tranches.empty or total_nav is None or total_nav <= 0:
        return 0, 0, 0
        
    price_per_unit = calc_price_per_unit(df_tranches_global, total_nav)
    investor_units = inv_tranches['Units'].sum()
    balance = round(investor_units * price_per_unit, 2)
    invested_value = sum(tranche['EntryNAV'] * tranche['Units'] for _, tranche in inv_tranches.iterrows())
    profit = balance - invested_value
    profit_perc = profit / invested_value if invested_value > 0 else 0
    return balance, profit, profit_perc

def calculate_tav(df_tranches, total_nav):
    return total_nav
# helpers.py (Added functions)
import numpy as np
from datetime import datetime

def calculate_fund_performance(df_transactions, df_tranches):
    df_trans = df_transactions.sort_values('Date').copy()
    historical = []
    current_total_units = 0.0
    for _, trans in df_trans.iterrows():
        if trans['Type'] in ['Nạp', 'Rút', 'Phí']:
            current_total_units += trans['UnitsChange']
        if trans['Type'] == 'NAV Update' or trans['NAV'] > 0:
            if current_total_units > 0:
                price = trans['NAV'] / current_total_units
                historical.append({'Date': trans['Date'], 'NAV': trans['NAV'], 'Units': current_total_units, 'Price': price})
    if not historical:
        return {}
    df_hist = pd.DataFrame(historical)
    df_hist['Return'] = df_hist['Price'].pct_change().fillna(0)
    twr = np.prod(1 + df_hist['Return']) - 1
    peak = df_hist['Price'].cummax()
    drawdown = (df_hist['Price'] - peak) / peak
    max_dd = drawdown.min()
    return {'TWR': twr, 'Max Drawdown': max_dd, 'Historical': df_hist}

def calculate_xirr(cashflows, dates):
    if len(cashflows) != len(dates) or len(cashflows) < 2:
        return None
    min_date = min(dates)
    def xnpv(r):
        return sum(cf / (1 + r)**((d - min_date).days / 365.0) for cf, d in zip(cashflows, dates))
    low, high = -0.99, 10.0
    while high - low > 1e-10:
        mid = (low + high) / 2
        if xnpv(mid) > 0:
            low = mid
        else:
            high = mid
    return mid

def calculate_investor_irr(investor_id, df_transactions, current_nav, df_tranches, df_investors):
    trans = df_transactions[df_transactions['InvestorID'] == investor_id].sort_values('Date')
    if trans.empty:
        return None
    cashflows = []
    dates = []
    for _, t in trans.iterrows():
        if t['Type'] == 'Nạp':
            cashflows.append(-t['Amount'])
        elif t['Type'] in ['Rút', 'Phí']:
            cashflows.append(-t['Amount'])  # Positive for withdrawal from investor view
        dates.append(t['Date'])
    # Add final balance as positive cashflow at current date
    inv_tranches = df_tranches[df_tranches['InvestorID'] == investor_id]
    if not inv_tranches.empty:
        balance, _, _ = calc_balance_profit(inv_tranches, current_nav, df_tranches)
        cashflows.append(balance)
        dates.append(datetime.now())
    return calculate_xirr(cashflows, dates)