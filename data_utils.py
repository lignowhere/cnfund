# data_utils.py

import pandas as pd
import numpy as np
import streamlit as st
from typing import Any, Union, List

# --- CÁC HÀM FORMAT ---

def format_currency_safe(amount: Union[float, int, str, None],
                         currency: str = "đ",
                         compact: bool = False) -> str:
    """
    Định dạng tiền tệ một cách an toàn, xử lý NaN, None và có tùy chọn compact.
    """
    if amount is None or (isinstance(amount, float) and np.isnan(amount)):
        return f"0 {currency}"

    try:
        numeric_amount = float(str(amount).replace(",", "").replace("đ", "").strip())
    except (ValueError, TypeError):
        return f"0 {currency}"

    if compact and abs(numeric_amount) >= 1_000_000:
        return f"{numeric_amount / 1_000_000:.1f}M {currency}"
    
    return f"{numeric_amount:,.0f} {currency}"

# --- CLASS TIỆN ÍCH ---

class DataCleaner:
    """Lớp tiện ích để làm sạch dữ liệu."""
    @staticmethod
    def clean_value(value: Any, default: str = "N/A") -> str:
        """Làm sạch giá trị đơn lẻ, thay thế NaN bằng text thân thiện."""
        if value is None or pd.isna(value):
            return default
        if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
            return default
        if isinstance(value, str):
            clean_str = value.strip().lower()
            if clean_str in ['nan', 'null', 'none', '', 'undefined']:
                return default
            return value.strip()
        return str(value)

class ErrorHandler:
    """
    Context manager để bắt lỗi và hiển thị thông báo thân thiện trên Streamlit.
    **ĐÃ CẬP NHẬT**: Bỏ qua các ngoại lệ điều khiển nội bộ của Streamlit.
    """
    def __init__(self, operation_name: str = "thao tác"):
        self.operation_name = operation_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Nếu không có lỗi, thoát ngay
        if not exc_type:
            return False

        # === SỬA LỖI CHÍNH ===
        # Kiểm tra xem đây có phải là ngoại lệ điều khiển của Streamlit không.
        # Nếu đúng, chúng ta phải để Streamlit tự xử lý.
        # Trả về False sẽ cho phép ngoại lệ tiếp tục được "ném" lên trên.
        streamlit_control_exceptions = ("RerunException", "StopException")
        if exc_type.__name__ in streamlit_control_exceptions:
            return False

        # Nếu đây là một lỗi thực sự, hiển thị thông báo cho người dùng.
        st.error(f"❌ Đã xảy ra lỗi trong khi {self.operation_name}:")
        st.error(f"`{exc_val}`")
        
        # Ghi log lỗi ra terminal để debug (rất hữu ích)
        import logging
        logging.error(f"Error in '{self.operation_name}': {exc_val}", exc_info=True)
        
        # Trả về True để ngăn ứng dụng bị crash hoàn toàn
        return True

# --- CÁC HÀM RENDER ---

def render_clean_table(df: pd.DataFrame, 
                       title: str, 
                       currency_cols: List[str] = None):
    """Render một bảng đã được làm sạch và định dạng."""
    if df.empty:
        st.info(f"📄 {title}: Chưa có dữ liệu.")
        return

    df_display = df.copy()
    
    # Định dạng các cột tiền tệ
    if currency_cols:
        for col in currency_cols:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(lambda x: format_currency_safe(x))

    # Làm sạch các cột còn lại
    for col in df_display.columns:
        if not currency_cols or col not in currency_cols:
             df_display[col] = df_display[col].apply(lambda x: DataCleaner.clean_value(x, "---"))

    st.subheader(f"📋 {title}")
    st.dataframe(df_display, use_container_width=True, hide_index=True)