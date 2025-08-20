import pandas as pd
from datetime import datetime
import uuid
import streamlit as st
from helpers import calc_price_per_unit
import numpy as np  # Added for np.maximum
import os
import shutil  # Added for backup
from datetime import datetime as dt  # For timestamp

# Constants
INVESTORS_FILE = 'investors.csv'
TRANCHES_FILE = 'tranches.csv'
TRANSACTIONS_FILE = 'transactions.csv'
AUDIT_LOG = 'audit.log'
HURDLE_RATE_ANNUAL = 0.06
PERFORMANCE_FEE_RATE = 0.20
DEFAULT_UNIT_PRICE = 1000.0  # Giá unit mặc định cho quỹ mới

def log_audit(message):
    try:
        with open(AUDIT_LOG, 'a') as f:
            f.write(f"{dt.now()}: {message}\n")
    except Exception as e:
        st.warning(f"Không thể log audit: {str(e)}")

def load_data():
    try:
        df_investors = pd.read_csv(INVESTORS_FILE)
        df_investors['Phone'] = df_investors['Phone'].astype(str)
        log_audit(f"Loaded investors data with {len(df_investors)} records")
    except FileNotFoundError:
        df_investors = pd.DataFrame(columns=['ID', 'Name', 'Phone', 'Address', 'Email', 'JoinDate'])
    except Exception as e:
        st.error(f"Lỗi không mong muốn khi đọc {INVESTORS_FILE}: {str(e)}")
        df_investors = pd.DataFrame(columns=['ID', 'Name', 'Phone', 'Address', 'Email', 'JoinDate'])

    try:
        df_tranches = pd.read_csv(TRANCHES_FILE)
        if not df_tranches.empty:
            df_tranches['EntryDate'] = pd.to_datetime(df_tranches['EntryDate'])
            if 'HWM' not in df_tranches.columns:  # Backwards compatibility for HWM
                df_tranches['HWM'] = df_tranches['EntryNAV']
        log_audit(f"Loaded tranches data with {len(df_tranches)} records")
    except FileNotFoundError:
        df_tranches = pd.DataFrame(columns=['InvestorID', 'TrancheID', 'EntryDate', 'EntryNAV', 'Units', 'HWM'])
    except Exception as e:
        st.error(f"Lỗi không mong muốn khi đọc {TRANCHES_FILE}: {str(e)}")
        df_tranches = pd.DataFrame(columns=['InvestorID', 'TrancheID', 'EntryDate', 'EntryNAV', 'Units', 'HWM'])

    try:
        df_transactions = pd.read_csv(TRANSACTIONS_FILE)
        if not df_transactions.empty:
            df_transactions['Date'] = pd.to_datetime(df_transactions['Date'])
        log_audit(f"Loaded transactions data with {len(df_transactions)} records")
    except FileNotFoundError:
        df_transactions = pd.DataFrame(columns=['ID', 'InvestorID', 'Date', 'Type', 'Amount', 'NAV', 'UnitsChange'])
    except Exception as e:
        st.error(f"Lỗi không mong muốn khi đọc {TRANSACTIONS_FILE}: {str(e)}")
        df_transactions = pd.DataFrame(columns=['ID', 'InvestorID', 'Date', 'Type', 'Amount', 'NAV', 'UnitsChange'])

    return df_investors, df_tranches, df_transactions

def save_data(df_investors, df_tranches, df_transactions):
    # Auto backup
    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
    if os.path.exists(INVESTORS_FILE):
        shutil.copy(INVESTORS_FILE, f"backup/investors_{timestamp}.csv")  # Assume backup dir exists, or create
    if os.path.exists(TRANCHES_FILE):
        shutil.copy(TRANCHES_FILE, f"backup/tranches_{timestamp}.csv")
    if os.path.exists(TRANSACTIONS_FILE):
        shutil.copy(TRANSACTIONS_FILE, f"backup/transactions_{timestamp}.csv")
    log_audit(f"Backed up data at {timestamp}")

    try:
        df_investors.to_csv(INVESTORS_FILE, index=False)
        df_tranches.to_csv(TRANCHES_FILE, index=False)
        df_transactions.to_csv(TRANSACTIONS_FILE, index=False)
        log_audit("Saved data successfully")
    except Exception as e:
        st.error(f"Lỗi khi lưu dữ liệu: {str(e)}")
        log_audit(f"Error saving data: {str(e)}")

def add_investor(df, name, phone="", address="", email=""):
    new_id = df['ID'].max(skipna=True) + 1 if not df.empty else 1
    join_date = datetime.today().date()
    new_row = pd.DataFrame([{'ID': new_id, 'Name': name, 'Phone': phone, 'Address': address, 'Email': email, 'JoinDate': join_date}])
    df = pd.concat([df, new_row], ignore_index=True)
    log_audit(f"Added investor ID: {new_id}, Name: {name}")
    return df

def add_transaction(df_tranches, df_transactions, investor_id, trans_type, amount, total_nav, trans_date=None):
    if trans_date is None:
        trans_date = datetime.today()
    else:
        trans_date = datetime.combine(trans_date, datetime.min.time())

    new_trans_id = df_transactions['ID'].max(skipna=True) + 1 if not df_transactions.empty else 1

    if trans_type == "Nạp":
        old_total_nav = total_nav - amount
        if old_total_nav < 0:
            log_audit(f"Attempted deposit with negative old NAV: {old_total_nav}")
            raise ValueError("Total NAV sau giao dịch phải lớn hơn hoặc bằng số tiền nạp (edge case old NAV âm đã được xử lý bằng lỗi).")
        old_price_per_unit = calc_price_per_unit(df_tranches, old_total_nav)
        units_change = amount / old_price_per_unit
        tranche_id = str(uuid.uuid4())
        new_tranche = pd.DataFrame([{
            'InvestorID': investor_id, 'TrancheID': tranche_id,
            'EntryDate': trans_date, 'EntryNAV': old_price_per_unit, 'Units': units_change,
            'HWM': old_price_per_unit  # Initialize HWM
        }])
        df_tranches = pd.concat([df_tranches, new_tranche], ignore_index=True)
        new_trans = pd.DataFrame([{
            'ID': new_trans_id, 'InvestorID': investor_id, 'Date': trans_date,
            'Type': 'Nạp', 'Amount': amount, 'NAV': total_nav, 'UnitsChange': units_change
        }])
        df_transactions = pd.concat([df_transactions, new_trans], ignore_index=True)
        log_audit(f"Added deposit for ID {investor_id}: Amount {amount}, NAV {total_nav}")

    elif trans_type == "Rút":
        old_total_nav = total_nav + amount
        if old_total_nav <= 0:
            raise ValueError("Total NAV trước rút không hợp lệ.")
        old_price_per_unit = calc_price_per_unit(df_tranches, old_total_nav)
        investor_tranches = df_tranches[df_tranches['InvestorID'] == investor_id]
        investor_units = investor_tranches['Units'].sum()
        balance_before = investor_units * old_price_per_unit
        if amount > balance_before:
            log_audit(f"Attempted withdrawal exceeding balance for ID {investor_id}: {amount} > {balance_before}")
            raise ValueError("Số tiền rút vượt balance.")
        
        # Tính phí nếu không phải cuối năm
        is_end_year = (trans_date.month == 12 and trans_date.day == 31)
        fee = 0.0
        if not is_end_year:
            details = calculate_investor_fee_details(investor_tranches, trans_date, old_total_nav, df_tranches)
            fee = details['total_fee']
            if amount < balance_before:  # Partial withdrawal
                fee *= (amount / balance_before)  # Pro-rata fee
        
        effective_amount = amount - fee
        if effective_amount <= 0:
            raise ValueError("Số tiền rút hiệu quả sau phí không hợp lệ.")
        units_change = - (effective_amount / old_price_per_unit)
        if investor_units < abs(units_change):
            raise ValueError("Không đủ đơn vị sau trừ phí.")
        
        ratio = abs(units_change) / investor_units
        df_tranches.loc[df_tranches['InvestorID'] == investor_id, 'Units'] *= (1 - ratio)
        # Clean up zero-unit tranches
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
        
        # Handle full withdrawal explicitly
        remaining_units = df_tranches[df_tranches['InvestorID'] == investor_id]['Units'].sum()
        if remaining_units < 1e-6:
            df_tranches = df_tranches[df_tranches['InvestorID'] != investor_id]
            log_audit(f"Removed all tranches for ID {investor_id} due to full withdrawal")
        # NO RESET for partial withdrawal

        log_audit(f"Added withdrawal for ID {investor_id}: Amount {amount}, Fee {fee}, NAV {total_nav}")

    elif trans_type == "NAV Update":
        new_trans = pd.DataFrame([{
            'ID': new_trans_id, 'InvestorID': 0, 'Date': trans_date,
            'Type': 'NAV Update', 'Amount': 0, 'NAV': total_nav, 'UnitsChange': 0
        }])
        df_transactions = pd.concat([df_transactions, new_trans], ignore_index=True)
        # Update HWM for all tranches
        total_units = df_tranches['Units'].sum()
        if total_units > 0:
            current_price = total_nav / total_units
            mask = df_tranches['EntryDate'] <= trans_date
            df_tranches.loc[mask, 'HWM'] = np.maximum(df_tranches.loc[mask, 'HWM'], current_price)
        log_audit(f"Updated NAV: {total_nav}, Updated HWMs")

    return df_tranches, df_transactions

def calculate_investor_fee_details(investor_tranches, ending_date_dt, ending_total_nav, df_tranches_global):
    if investor_tranches.empty or ending_total_nav <= 0:
        return {
            'total_fee': 0.0, 'hurdle_value': 0.0, 'hwm_value': 0.0, 'excess_profit': 0.0,
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
    hwm_value = 0.0
    excess_profit = 0.0
    for _, tranche in investor_tranches.iterrows():
        if tranche['Units'] < 1e-6:
            continue
        time_delta = (ending_date_dt - tranche['EntryDate']).days / 365.0
        if time_delta <= 0:
            continue
        hurdle_rate = HURDLE_RATE_ANNUAL * time_delta
        hurdle_price = tranche['EntryNAV'] * (1 + hurdle_rate)
        effective_hurdle = max(hurdle_price, tranche['HWM'])  # High Water Mark integration
        profit_per_unit = max(0, ending_price_per_unit - effective_hurdle)
        tranche_excess = profit_per_unit * tranche['Units']
        tranche_fee = PERFORMANCE_FEE_RATE * tranche_excess
        total_fee += tranche_fee
        hurdle_value += hurdle_price * tranche['Units']
        hwm_value += tranche['HWM'] * tranche['Units']  # Added for display
        excess_profit += tranche_excess
    
    return {
        'total_fee': round(total_fee, 2),
        'hurdle_value': round(hurdle_value, 2),
        'hwm_value': round(hwm_value, 2),  # Added
        'excess_profit': round(excess_profit, 2),
        'invested_value': round(invested_value, 2),
        'balance': balance,
        'profit': round(profit, 2),
        'profit_perc': profit_perc
    }