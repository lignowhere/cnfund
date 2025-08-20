# data_handler.py (Fixed version)
import uuid
from datetime import datetime
import pandas as pd
import streamlit as st
from helpers import calc_price_per_unit

# ==== KẾT NỐI GOOGLE SHEETS (streamlit-gsheets) ====
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError as e:
    st.error(
        "Thiếu gói 'streamlit-gsheets'. Hãy thêm vào requirements.txt (vd: streamlit-gsheets==0.0.9) rồi deploy lại."
    )
    st.stop()

# Khởi tạo connection
try:
    _conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Lỗi khi khởi tạo connection: {e}")
    st.error("Hãy kiểm tra secrets.toml và đảm bảo Google Drive API đã được bật.")
    st.stop()

# Lấy tên/URL spreadsheet từ secrets; fallback về "cnfund"
try:
    _SPREADSHEET = st.secrets["connections"]["gsheets"].get("spreadsheet", "cnfund")
except Exception:
    _SPREADSHEET = "cnfund"

# Tên worksheet
_WS_INVESTORS = "investors"
_WS_TRANCHES = "tranches"
_WS_TRANSACTIONS = "transactions"

# Tham số chung khi đọc/ghi
_READ_KW = dict(spreadsheet=_SPREADSHEET, ttl=0)  # ttl=0 để luôn mới

def _ensure_columns(df: pd.DataFrame, columns):
    """Đảm bảo DataFrame có đủ cột theo danh sách 'columns'."""
    if df is None or df.empty:
        return pd.DataFrame(columns=columns)
    missing = [c for c in columns if c not in df.columns]
    for c in missing:
        df[c] = pd.Series(dtype="object")
    return df[columns].copy()

def _parse_dates(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

def _parse_numbers(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def _read_ws(worksheet: str) -> pd.DataFrame:
    """Đọc worksheet với error handling tốt hơn"""
    try:
        df = _conn.read(worksheet=worksheet, **_READ_KW)
        if df is None or df.empty:
            return pd.DataFrame()
        return df.replace({None: pd.NA})
    except Exception as e:
        error_msg = str(e)
        if "SERVICE_DISABLED" in error_msg or "Google Drive API" in error_msg:
            st.error("🚨 **Google Drive API chưa được bật!**")
            st.error("Vui lòng:")
            st.error("1. Truy cập: https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=129071271267")
            st.error("2. Click 'Enable' để bật Google Drive API")
            st.error("3. Tương tự bật Google Sheets API")
            st.error("4. Đợi vài phút rồi thử lại")
        else:
            st.error(f"Lỗi khi đọc worksheet '{worksheet}': {e}")
        return pd.DataFrame()

def _write_ws(worksheet: str, df: pd.DataFrame):
    """Ghi worksheet với error handling tốt hơn"""
    df_to_save = df.copy()
    # Chuyển datetime về ISO để lưu lên Sheets đẹp
    for col in df_to_save.columns:
        if pd.api.types.is_datetime64_any_dtype(df_to_save[col]):
            df_to_save[col] = df_to_save[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        _conn.update(worksheet=worksheet, data=df_to_save, spreadsheet=_SPREADSHEET)
    except Exception as e:
        error_msg = str(e)
        if "SERVICE_DISABLED" in error_msg or "Google Drive API" in error_msg:
            st.error("🚨 **Google Drive API chưa được bật khi ghi dữ liệu!**")
            st.error("Hãy bật API như hướng dẫn ở trên.")
        else:
            st.error(f"Lỗi khi ghi worksheet '{worksheet}': {e}")
        raise

def load_data():
    """Đọc toàn bộ dữ liệu từ Google Sheets."""
    # investors
    inv_cols = ["ID", "Name", "Phone", "Address", "Email", "JoinDate"]
    df_investors = _ensure_columns(_read_ws(_WS_INVESTORS), inv_cols)
    df_investors = _parse_dates(df_investors, ["JoinDate"])
    if "ID" in df_investors.columns:
        df_investors["ID"] = pd.to_numeric(df_investors["ID"], errors="coerce").astype("Int64")

    # tranches - FIX: Thêm HWM column
    tr_cols = ["InvestorID", "TrancheID", "EntryDate", "EntryNAV", "Units", "HWM"]
    df_tranches = _ensure_columns(_read_ws(_WS_TRANCHES), tr_cols)
    df_tranches = _parse_dates(df_tranches, ["EntryDate"])
    df_tranches = _parse_numbers(df_tranches, ["EntryNAV", "Units", "HWM"])
    if "InvestorID" in df_tranches.columns:
        df_tranches["InvestorID"] = pd.to_numeric(df_tranches["InvestorID"], errors="coerce").astype("Int64")
    
    # Nếu HWM column rỗng, set = EntryNAV
    if "HWM" in df_tranches.columns:
        df_tranches["HWM"] = df_tranches["HWM"].fillna(df_tranches["EntryNAV"])

    # transactions
    tx_cols = ["ID", "InvestorID", "Date", "Type", "Amount", "NAV", "UnitsChange"]
    df_transactions = _ensure_columns(_read_ws(_WS_TRANSACTIONS), tx_cols)
    df_transactions = _parse_dates(df_transactions, ["Date"])
    df_transactions = _parse_numbers(df_transactions, ["Amount", "NAV", "UnitsChange"])
    if "ID" in df_transactions.columns:
        df_transactions["ID"] = pd.to_numeric(df_transactions["ID"], errors="coerce").astype("Int64")
    if "InvestorID" in df_transactions.columns:
        df_transactions["InvestorID"] = pd.to_numeric(df_transactions["InvestorID"], errors="coerce").astype("Int64")

    return df_investors, df_tranches, df_transactions

def save_data(df_investors, df_tranches, df_transactions):
    """Ghi toàn bộ dữ liệu về Google Sheets."""
    _write_ws(_WS_INVESTORS, df_investors)
    _write_ws(_WS_TRANCHES, df_tranches)
    _write_ws(_WS_TRANSACTIONS, df_transactions)

def add_investor(df, name, phone="", address="", email=""):
    """Thêm nhà đầu tư mới vào DF (chưa lưu)."""
    # Tạo ID tăng dần
    if df is None or df.empty or "ID" not in df.columns:
        new_id = 1
    else:
        cur_max = pd.to_numeric(df["ID"], errors="coerce").dropna()
        new_id = int(cur_max.max()) + 1 if not cur_max.empty else 1
    
    join_date = datetime.today()
    new_row = pd.DataFrame([{
        "ID": new_id,
        "Name": name,
        "Phone": phone,
        "Address": address,
        "Email": email,
        "JoinDate": join_date
    }])
    return pd.concat([df, new_row], ignore_index=True)

def add_transaction(df_tranches, df_transactions, investor_id, trans_type, amount, total_nav, trans_date=None):
    """
    Ghi logic Nạp/Rút/NAV Update giống bản CSV cũ, nhưng làm trên DF rồi trả về DF đã cập nhật.
    """
    if trans_date is None:
        trans_date = datetime.today()
    else:
        # date -> datetime
        trans_date = datetime.combine(trans_date, datetime.min.time())

    # Tạo ID giao dịch mới
    if df_transactions is None or df_transactions.empty or "ID" not in df_transactions.columns:
        new_trans_id = 1
    else:
        cur_max = pd.to_numeric(df_transactions["ID"], errors="coerce").dropna()
        new_trans_id = int(cur_max.max()) + 1 if not cur_max.empty else 1

    if trans_type == "Nạp":
        # total_nav = TAV_old + amount → TAV_old = total_nav - amount
        old_total_nav = total_nav - (amount or 0.0)
        if old_total_nav < 0:
            st.error("Total NAV sau trừ amount âm, không hợp lệ.")
            return df_tranches, df_transactions

        old_price_per_unit = calc_price_per_unit(df_tranches, old_total_nav)
        units_change = (amount or 0.0) / old_price_per_unit

        tranche_id = str(uuid.uuid4())
        new_tranche = pd.DataFrame([{
            "InvestorID": investor_id,
            "TrancheID": tranche_id,
            "EntryDate": trans_date,
            "EntryNAV": old_price_per_unit,
            "Units": units_change,
            "HWM": old_price_per_unit  # FIX: Thêm HWM
        }])
        df_tranches = pd.concat([df_tranches, new_tranche], ignore_index=True)

        new_trans = pd.DataFrame([{
            "ID": new_trans_id, "InvestorID": investor_id, "Date": trans_date,
            "Type": "Nạp", "Amount": amount, "NAV": total_nav, "UnitsChange": units_change
        }])
        df_transactions = pd.concat([df_transactions, new_trans], ignore_index=True)

    elif trans_type == "Rút":
        # total_nav = TAV_old - amount → TAV_old = total_nav + amount
        old_total_nav = total_nav + (amount or 0.0)
        old_price_per_unit = calc_price_per_unit(df_tranches, old_total_nav)

        investor_tranches = df_tranches[df_tranches["InvestorID"] == investor_id]
        investor_units = float(investor_tranches["Units"].sum())
        balance_before = investor_units * old_price_per_unit
        if (amount or 0.0) > balance_before + 1e-9:
            st.error("Số tiền rút vượt balance.")
            return df_tranches, df_transactions

        # Không phải cuối năm thì tính phí pro-rata
        is_end_year = (trans_date.month == 12 and trans_date.day == 31)
        fee = 0.0
        if not is_end_year:
            details = calculate_investor_fee_details(investor_tranches, trans_date, old_total_nav, df_tranches)
            fee = float(details["total_fee"])
            if (amount or 0.0) < balance_before:  # Rút một phần
                fee *= ((amount or 0.0) / balance_before)

        effective_amount = (amount or 0.0) - fee
        units_change = -(effective_amount / old_price_per_unit)
        if investor_units + 1e-9 < abs(units_change):
            st.error("Không đủ đơn vị sau trừ phí.")
            return df_tranches, df_transactions

        # Tỷ lệ giảm units theo tổng units của NĐT
        ratio = abs(units_change) / investor_units if investor_units > 0 else 0.0
        df_tranches.loc[df_tranches["InvestorID"] == investor_id, "Units"] *= (1 - ratio)
        # Xóa tranche 0 units
        df_tranches = df_tranches[df_tranches["Units"] >= 1e-6]

        # Ghi giao dịch rút
        new_trans = pd.DataFrame([{
            "ID": new_trans_id, "InvestorID": investor_id, "Date": trans_date,
            "Type": "Rút", "Amount": -effective_amount, "NAV": total_nav, "UnitsChange": units_change
        }])
        df_transactions = pd.concat([df_transactions, new_trans], ignore_index=True)

        # Nếu có phí → ghi thêm 1 giao dịch 'Phí'
        if fee > 0:
            new_trans_id_fee = new_trans_id + 1
            if not df_transactions.empty:
                cur_max = pd.to_numeric(df_transactions["ID"], errors="coerce").dropna()
                new_trans_id_fee = int(cur_max.max()) + 1 if not cur_max.empty else new_trans_id + 1
            new_trans_fee = pd.DataFrame([{
                "ID": new_trans_id_fee, "InvestorID": investor_id, "Date": trans_date,
                "Type": "Phí", "Amount": -fee, "NAV": total_nav, "UnitsChange": 0
            }])
            df_transactions = pd.concat([df_transactions, new_trans_fee], ignore_index=True)

        # Reset EntryNAV/EntryDate cho phần còn lại (giống bản trước)
        if df_tranches[df_tranches["InvestorID"] == investor_id]["Units"].sum() > 1e-6:
            df_tranches.loc[df_tranches["InvestorID"] == investor_id, "EntryDate"] = trans_date
            df_tranches.loc[df_tranches["InvestorID"] == investor_id, "EntryNAV"] = old_price_per_unit
            df_tranches.loc[df_tranches["InvestorID"] == investor_id, "HWM"] = old_price_per_unit

    elif trans_type == "NAV Update":
        new_trans = pd.DataFrame([{
            "ID": new_trans_id, "InvestorID": 0, "Date": trans_date,
            "Type": "NAV Update", "Amount": 0, "NAV": total_nav, "UnitsChange": 0
        }])
        df_transactions = pd.concat([df_transactions, new_trans], ignore_index=True)

    return df_tranches, df_transactions

# Tham số phí
HURDLE_RATE_ANNUAL = 0.06
PERFORMANCE_FEE_RATE = 0.20

def calculate_investor_fee_details(investor_tranches, ending_date_dt, ending_total_nav, df_tranches_global):
    """Tính phí theo hurdle 6% pro-rata và fee 20% excess, giống bản trước."""
    if investor_tranches is None or investor_tranches.empty or (ending_total_nav or 0.0) <= 0:
        return {
            "total_fee": 0.0, "hurdle_value": 0.0, "excess_profit": 0.0,
            "invested_value": 0.0, "balance": 0.0, "profit": 0.0, "profit_perc": 0.0,
            "hwm_value": 0.0  # FIX: Thêm HWM value
        }

    ending_price_per_unit = calc_price_per_unit(df_tranches_global, ending_total_nav)
    investor_units = float(investor_tranches["Units"].sum())
    balance = round(investor_units * ending_price_per_unit, 2)
    invested_value = float((investor_tranches["EntryNAV"] * investor_tranches["Units"]).sum())
    profit = balance - invested_value
    profit_perc = (profit / invested_value) if invested_value > 1e-9 else 0.0

    total_fee = 0.0
    hurdle_value = 0.0
    hwm_value = 0.0  # FIX: Tính HWM value
    excess_profit = 0.0

    for _, tr in investor_tranches.iterrows():
        units = float(tr.get("Units", 0.0) or 0.0)
        if units < 1e-9:
            continue
        entry_date = tr.get("EntryDate")
        if pd.isna(entry_date):
            continue
        days = (ending_date_dt - entry_date).days / 365.0
        if days <= 0:
            continue
        entry_nav = float(tr.get("EntryNAV", 0.0) or 0.0)
        hwm = float(tr.get("HWM", entry_nav) or entry_nav)  # FIX: Sử dụng HWM
        
        # Hurdle calculation
        hurdle_rate = HURDLE_RATE_ANNUAL * days
        hurdle_price = entry_nav * (1 + hurdle_rate)
        
        # Use higher of hurdle and HWM
        threshold_price = max(hurdle_price, hwm)
        profit_per_unit = max(0.0, ending_price_per_unit - threshold_price)
        tranche_excess = profit_per_unit * units
        tranche_fee = PERFORMANCE_FEE_RATE * tranche_excess
        
        total_fee += tranche_fee
        hurdle_value += hurdle_price * units
        hwm_value += hwm * units  # FIX: Tính tổng HWM value
        excess_profit += tranche_excess

    return {
        "total_fee": round(total_fee, 2),
        "hurdle_value": round(hurdle_value, 2),
        "hwm_value": round(hwm_value, 2),  # FIX: Thêm HWM value
        "excess_profit": round(excess_profit, 2),
        "invested_value": round(invested_value, 2),
        "balance": round(balance, 2),
        "profit": round(profit, 2),
        "profit_perc": profit_perc,
    }