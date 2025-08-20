import pandas as pd
from datetime import datetime
import uuid
import streamlit as st
from helpers import calc_price_per_unit
from st_gsheets_connection import GSheetsConnection

# Kết nối Google Sheets qua secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection, credentials=st.secrets["gsheets"])

# Constants
HURDLE_RATE_ANNUAL = 0.06
PERFORMANCE_FEE_RATE = 0.20
DEFAULT_UNIT_PRICE = 1000.0  # Giá unit mặc định cho quỹ mới

# Tên Google Sheet của bạn
SPREADSHEET = "cnfund"


def load_data():
    try:
        df_investors = conn.read(spreadsheet=SPREADSHEET, worksheet="investors")
    except Exception:
        df_investors = pd.DataFrame(columns=['ID', 'Name', 'Phone', 'Address', 'Email', 'JoinDate'])

    try:
        df_tranches = conn.read(spreadsheet=SPREADSHEET, worksheet="tranches")
        if not df_tranches.empty:
            df_tranches['EntryDate'] = pd.to_datetime(df_tranches['EntryDate'])
    except Exception:
        df_tranches = pd.DataFrame(columns=['InvestorID', 'TrancheID', 'EntryDate', 'EntryNAV', 'Units'])

    try:
        df_transactions = conn.read(spreadsheet=SPREADSHEET, worksheet="transactions")
        if not df_transactions.empty:
            df_transactions['Date'] = pd.to_datetime(df_transactions['Date'])
    except Exception:
        df_transactions = pd.DataFrame(columns=['ID', 'InvestorID', 'Date', 'Type', 'Amount', 'NAV', 'UnitsChange'])

    return df_investors, df_tranches, df_transactions


def save_data(df_investors, df_tranches, df_transactions):
    conn.write(df_investors, spreadsheet=SPREADSHEET, worksheet="investors")
    conn.write(df_tranches, spreadsheet=SPREADSHEET, worksheet="tranches")
    conn.write(df_transactions, spreadsheet=SPREADSHEET, worksheet="transactions")


def add_investor(df, name, phone="", address="", email=""):
    new_id = df['ID'].max(skipna=True) + 1 if not df.empty else 1
    join_date = datetime.today().date()
    new_row = pd.DataFrame([{
        'ID': new_id, 'Name': name, 'Phone': phone,
        'Address': address, 'Email': email, 'JoinDate': join_date
    }])
    return pd.concat([df, new_row], ignore_index=True)


def add_transaction(df_tranches, df_transactions, investor_id, trans_type, amount, total_nav, trans_date=None):
    if trans_date is None:
        trans_date = datetime.today()
    else:
        trans_date = datetime.combine(trans_date, datetime.min.time())

    new_trans_id = df_transactions['ID'].max(skipna=True) + 1 if not df_transactions.empty else 1

    if trans_type == "Nạp":
        old_total_nav = total_nav - amount
        if old_total_nav < 0:
            st.error("Total NAV sau trừ amount âm, không hợp lệ.")
            return df_tranches, df_transactions
        old_price_per_unit = calc_price_per_unit(df_tranches, old_total_nav)
        units_change = amount / old_price_per_unit
        tranche_id = str(uuid.uuid4())
        new_tranche = pd.DataFrame([{
            'InvestorID': investor_id, 'TrancheID': tranche_id,
            'EntryDate': trans_date, 'EntryNAV': old_price_per_unit, 'Units': units_change
        }])
        df_tranches = pd.concat([df_tranches, new_tranche], ignore_index=True)
        new_trans = pd.DataFrame([{
            'ID': new_trans_id, 'InvestorID': investor_id, 'Date': trans_date,
            'Type': 'Nạp', 'Amount': amount, 'NAV': total_nav, 'UnitsChange': units_change
        }])
        df_transactions = pd.concat([df_transactions, new_trans], ignore_index=True)

    elif trans_type == "Rút":
        old_total_nav = total_nav + amount
        old_price_per_unit = calc_price_per_unit(df_tranches, old_total_nav)
        investor_tranches = df_tranches[df_tranches['InvestorID'] == investor_id]
        investor_units = investor_tranches['Units'].sum()
        balance_before = investor_units * old_price_per_unit
        if amount > balance_before:
            st.error("Số tiền rút vượt balance.")
            return df_tranches, df_transactions

        is_end_year = (trans_date.month == 12 and trans_date.day == 31)
        fee = 0.0
        if not is_end_year:
            details = calculate_investor_fee_details(investor_tranches, trans_date, old_total_nav, df_tranches)
            fee = details['total_fee']
            if amount < balance_before:
                fee *= (amount / balance_before)

        effective_amount = amount - fee
        units_change = - (effective_amount / old_price_per_unit)
        if investor_units < abs(units_change):
            st.error("Không đủ sau trừ phí.")
            return df_tranches, df_transactions

        ratio = abs(units_change) / investor_units
        df_tranches.loc[df_tranches['InvestorID'] == investor_id, 'Units'] *= (1 - ratio)
        df_tranches = df_tranches[df_tranches['Units'] >= 1e-6]

        new_trans = pd.DataFrame([{
            'ID': new_trans_id, 'InvestorID': investor_id, 'Date': trans_date,
            'Type': 'Rút', 'Amount': -effective_amount, 'NAV': total_nav, 'UnitsChange': units_change
        }])
        df_transactions = pd.concat([df_transactions, new_trans], ignore_index=True)

        if fee > 0:
            new_trans_id_fee = df_transactions['ID'].max(skipna=True) + 1
            new_trans_fee = pd.DataFrame([{
                'ID': new_trans_id_fee, 'InvestorID': investor_id, 'Date': trans_date,
                'Type': 'Phí', 'Amount': -fee, 'NAV': total_nav, 'UnitsChange': 0
            }])
            df_transactions = pd.concat([df_transactions, new_trans_fee], ignore_index=True)

        if investor_tranches['Units'].sum() > 1e-6:
            df_tranches.loc[df_tranches['InvestorID'] == investor_id, 'EntryDate'] = trans_date
            df_tranches.loc[df_tranches['InvestorID'] == investor_id, 'EntryNAV'] = old_price_per_unit

    elif trans_type == "NAV Update":
        new_trans = pd.DataFrame([{
            'ID': new_trans_id, 'InvestorID': 0, 'Date': trans_date,
            'Type': 'NAV Update', 'Amount': 0, 'NAV': total_nav, 'UnitsChange': 0
        }])
        df_transactions = pd.concat([df_transactions, new_trans], ignore_index=True)

    return df_tranches, df_transactions


def calculate_investor_fee_details(investor_tranches, ending_date_dt, ending_total_nav, df_tranches_global):
    if investor_tranches.empty or ending_total_nav <= 0:
        return {
            'total_fee': 0.0, 'hurdle_value': 0.0, 'excess_profit': 0.0,
            'invested_value': 0.0, 'balance': 0.0, 'profit': 0.0, 'profit_perc': 0.0
        }

    ending_price_per_unit = calc_price_per_unit(df_tranches_global, ending_total_nav)
    investor_units = investor_tranches['Units'].sum()
    balance = round(investor_units * ending_price_per_unit, 2)
    invested_value = sum(tranche['EntryNAV'] * tranche['Units'] for _, tranche in investor_tranches.iterrows())
    profit = balance - invested_value
    profit_perc = profit / invested_value if invested_value > 0 else 0

    total_fee = 0.0
    hurdle_value = 0.0
    excess_profit = 0.0
    for _, tranche in investor_tranches.iterrows():
        if tranche['Units'] < 1e-6:
            continue
        time_delta = (ending_date_dt - tranche['EntryDate']).days / 365.0
        if time_delta <= 0:
            continue
        hurdle_rate = HURDLE_RATE_ANNUAL * time_delta
        hurdle_price = tranche['EntryNAV'] * (1 + hurdle_rate)
        profit_per_unit = max(0, ending_price_per_unit - hurdle_price)
        tranche_excess = profit_per_unit * tranche['Units']
        tranche_fee = PERFORMANCE_FEE_RATE * tranche_excess
        total_fee += tranche_fee
        hurdle_value += hurdle_price * tranche['Units']
        excess_profit += tranche_excess

    return {
        'total_fee': round(total_fee, 2),
        'hurdle_value': round(hurdle_value, 2),
        'excess_profit': round(excess_profit, 2),
        'invested_value': round(invested_value, 2),
        'balance': balance,
        'profit': round(profit, 2),
        'profit_perc': profit_perc
    }
