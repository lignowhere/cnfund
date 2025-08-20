import streamlit as st
import pandas as pd
from helpers import format_currency, parse_currency, get_latest_total_nav, highlight_negative, calc_balance_profit, calc_price_per_unit, calculate_fund_performance, calculate_investor_irr # Đã đổi tên hàm ở đây
from data_handler import load_data, save_data, add_investor, add_transaction, calculate_investor_fee_details
import altair as alt
from datetime import date, datetime
import re  # For validation

df_investors, df_tranches, df_transactions = load_data()
latest_total_nav = get_latest_total_nav(df_transactions)

st.sidebar.title("Menu")
page = st.sidebar.radio("Chọn chức năng", [
    "Thêm Nhà Đầu Tư", "Sửa Thông Tin Nhà Đầu Tư",
    "Thêm Giao Dịch", "Thêm Total NAV", "Tính Toán Phí", "Tính Phí Riêng", "Xem Lịch Sử và Thống Kê"
])
if latest_total_nav:
    st.sidebar.metric("Total NAV Mới Nhất", format_currency(latest_total_nav))
else:
    st.sidebar.info("Quỹ chưa có NAV. Hãy thêm giao dịch nạp đầu tiên.")

# ------------------- Thêm Nhà Đầu Tư -------------------
if page == "Thêm Nhà Đầu Tư":
    st.title("Thêm Nhà Đầu Tư")
    with st.form("investor_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Tên *")
        phone = col2.text_input("SĐT")
        col3, col4 = st.columns(2)
        address = col3.text_input("Địa chỉ")
        email = col4.text_input("Email")
        submitted = st.form_submit_button("Thêm")
        valid = True
        if submitted:
            if not name:
                st.error("Vui lòng nhập tên nhà đầu tư.")
                valid = False
            if phone and not re.match(r"^(0\d{9,10})$", phone):  # Ensure starts with 0 and 10-11 digits
                st.error("SĐT phải bắt đầu bằng 0 và có 10-11 chữ số.")
                valid = False
            if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Email không hợp lệ.")
                valid = False
            if valid:
                try:
                    df_investors = add_investor(df_investors, name, phone, address, email)
                    save_data(df_investors, df_tranches, df_transactions)
                    st.success("Đã thêm nhà đầu tư.")
                except Exception as e:
                    st.error(f"Lỗi khi thêm nhà đầu tư: {str(e)}")

# ------------------- Sửa Nhà Đầu Tư -------------------
elif page == "Sửa Thông Tin Nhà Đầu Tư":
    st.title("Sửa Thông Tin Nhà Đầu Tư")
    if df_investors.empty:
        st.info("Chưa có nhà đầu tư nào.")
    else:
        st.info("Sửa trực tiếp trên bảng bên dưới và bấm 'Lưu' để cập nhật.")
        edited_df = st.data_editor(df_investors, num_rows="dynamic", key="investor_editor")
        if st.button("Lưu Thay Đổi"):
            try:
                df_investors = edited_df
                df_investors['Phone'] = df_investors['Phone'].astype(str)  # Ensure string
                save_data(df_investors, df_tranches, df_transactions)
                st.success("Đã lưu thay đổi.")
            except Exception as e:
                st.error(f"Lỗi khi lưu: {str(e)}")

        investor_id = st.selectbox("Xem Tình Trạng cho ID", df_investors['ID'])
        if investor_id:
            st.subheader("Tình Trạng Lãi Lỗ Hiện Tại")
            total_nav_input = st.text_input("Total NAV Hiện Tại", value=format_currency(latest_total_nav) if latest_total_nav else "0đ")
            current_total_nav = parse_currency(total_nav_input) or 0.0
            if current_total_nav > 0:
                inv_tranches = df_tranches[df_tranches['InvestorID'] == investor_id]
                if not inv_tranches.empty:
                    balance, profit, profit_perc = calc_balance_profit(inv_tranches, current_total_nav, df_tranches)
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Số dư hiện tại", format_currency(balance))
                    col2.metric("Lãi/Lỗ hiện tại", format_currency(profit), delta_color="normal")
                    col3.metric("Tỷ lệ Lãi/Lỗ", f"{profit_perc:.2%}", delta_color="normal")
                else:
                    st.info("Nhà đầu tư chưa có giao dịch.")

# ------------------- Thêm Giao Dịch -------------------
elif page == "Thêm Giao Dịch":
    st.title("Thêm Giao Dịch")
    if df_investors.empty:
        st.info("Chưa có nhà đầu tư nào.")
    else:
        if df_transactions.empty:
            st.warning("Quỹ mới, hãy bắt đầu bằng giao dịch Nạp tiền.")
        nav_option = st.radio("Chọn cách nhập Total NAV", ["Dùng Total NAV mới nhất", "Nhập thủ công"], index=0)
        with st.form("transaction_form"):
            col1, col2 = st.columns(2)
            investor_id = col1.selectbox("Chọn ID Nhà Đầu Tư", df_investors['ID'])
            trans_type = col2.selectbox("Loại Giao Dịch", ["Nạp", "Rút"])
            trans_date = st.date_input("Ngày Giao Dịch", value=date.today())
            amount_input = st.text_input("Số Tiền", "0đ")
            amount = parse_currency(amount_input) or 0.0
            if nav_option == "Dùng Total NAV mới nhất":
                total_nav = latest_total_nav if latest_total_nav else 0.0
                st.write(f"Total NAV đang dùng (sau giao dịch): {format_currency(total_nav)}")
            else:
                default_nav_str = format_currency(latest_total_nav) if latest_total_nav is not None else "0đ"
                nav_input = st.text_input("Nhập Total NAV sau giao dịch (đã bao gồm số tiền nạp/rút)", value=default_nav_str)
                total_nav = parse_currency(nav_input) or 0.0
            submitted = st.form_submit_button("Thêm")
            valid = True
            if submitted:
                if not investor_id:
                    st.error("Vui lòng chọn nhà đầu tư.")
                    valid = False
                if amount <= 0:
                    st.error("Số tiền phải lớn hơn 0.")
                    valid = False
                if total_nav <= 0:
                    st.error("Total NAV phải lớn hơn 0.")
                    valid = False
                if valid:
                    try:
                        df_tranches, df_transactions = add_transaction(
                            df_tranches, df_transactions,
                            investor_id, trans_type, amount, total_nav, trans_date
                        )
                        save_data(df_investors, df_tranches, df_transactions)
                        st.success("Đã thêm giao dịch.")
                    except ValueError as ve:
                        st.error(f"Lỗi giá trị: {str(ve)}")
                    except Exception as e:
                        st.error(f"Lỗi không mong muốn: {str(e)}")

# ------------------- Thêm Total NAV -------------------
elif page == "Thêm Total NAV":
    st.title("Thêm Total NAV")
    with st.form("nav_form"):
        trans_date = st.date_input("Ngày", value=date.today())
        total_nav_input = st.text_input("Total NAV", value=format_currency(latest_total_nav) if latest_total_nav else "0đ")
        total_nav = parse_currency(total_nav_input) or 0.0
        submitted = st.form_submit_button("Thêm")
        valid = True
        if submitted:
            if total_nav <= 0:
                st.error("Total NAV phải lớn hơn 0.")
                valid = False
            if valid:
                try:
                    df_tranches, df_transactions = add_transaction(df_tranches, df_transactions, 0, "NAV Update", 0, total_nav, trans_date)
                    save_data(df_investors, df_tranches, df_transactions)
                    st.success("Đã thêm Total NAV.")
                except Exception as e:
                    st.error(f"Lỗi khi thêm NAV: {str(e)}")

# ------------------- Tính Toán Phí -------------------
elif page == "Tính Toán Phí":
    st.title("Tính Toán Phí Cuối Năm")
    year = st.number_input("Năm", value=2025)
    ending_date = st.date_input("Ngày Kết Thúc", value=date(2025, 12, 31))
    ending_total_nav_input = st.text_input("Total NAV Kết Thúc", value=format_currency(latest_total_nav) if latest_total_nav else "0đ")
    ending_total_nav = parse_currency(ending_total_nav_input) or 0.0
    tab1, tab2 = st.tabs(["Phí Chi Tiết", "Chi Tiết Tranches"])
    with tab1:
        if st.button("Tính Toán"):
            if ending_total_nav <= 0:
                st.error("Total NAV kết thúc phải lớn hơn 0.")
            else:
                try:
                    ending_date_dt = datetime.combine(ending_date, datetime.min.time())
                    results = []
                    for inv_id in df_investors['ID']:
                        inv_tranches = df_tranches[df_tranches['InvestorID'] == inv_id]
                        details = calculate_investor_fee_details(inv_tranches, ending_date_dt, ending_total_nav, df_tranches)
                        results.append({
                            'InvestorID': inv_id,
                            'TotalUnits': inv_tranches['Units'].sum(),
                            'InvestedValue': format_currency(details['invested_value']),
                            'Balance': format_currency(details['balance']),
                            'Profit': format_currency(details['profit']),
                            '%Profit': f"{details['profit_perc']:.2%}",
                            'HurdleValue': format_currency(details['hurdle_value']),
                            'HWMValue': format_currency(details['hwm_value']),  # Added for HWM display
                            'ExcessProfit': format_currency(details['excess_profit']),
                            'Fee': format_currency(details['total_fee'])
                        })
                    df_results = pd.DataFrame(results)
                    st.dataframe(df_results.style.applymap(highlight_negative, subset=['Profit', 'ExcessProfit', 'Fee']))
                except Exception as e:
                    st.error(f"Lỗi khi tính toán phí: {str(e)}")
    with tab2:
        df_tranches_display = df_tranches.copy()
        df_tranches_display['EntryNAV'] = df_tranches_display['EntryNAV'].apply(format_currency)
        df_tranches_display['HWM'] = df_tranches_display['HWM'].apply(format_currency)  # Added
        st.dataframe(df_tranches_display)
    st.warning("Áp dụng phí sẽ thay đổi dữ liệu vĩnh viễn. Hãy chắc chắn trước khi tiếp tục.")
    confirm_apply = st.checkbox("Tôi chắc chắn muốn áp dụng phí và reset base.")
    if confirm_apply and st.button("Xác Nhận và Áp Dụng Phí"):
        if ending_total_nav <= 0:
            st.error("Total NAV kết thúc phải lớn hơn 0.")
        else:
            try:
                ending_date_dt = datetime.combine(ending_date, datetime.min.time())
                ending_price_per_unit = calc_price_per_unit(df_tranches, ending_total_nav)
                for inv_id in df_investors['ID']:
                    inv_tranches = df_tranches[df_tranches['InvestorID'] == inv_id]
                    details = calculate_investor_fee_details(inv_tranches, ending_date_dt, ending_total_nav, df_tranches)
                    total_fee = details['total_fee']
                    if total_fee > 0:
                        units_fee = total_fee / ending_price_per_unit
                        investor_units = inv_tranches['Units'].sum()
                        if investor_units < units_fee:
                            st.error(f"Không đủ đơn vị cho phí của ID {inv_id}")
                            continue
                        ratio = units_fee / investor_units
                        df_tranches.loc[df_tranches['InvestorID'] == inv_id, 'Units'] *= (1 - ratio)
                        new_trans_id = df_transactions['ID'].max(skipna=True) + 1 if not df_transactions.empty else 1
                        new_trans = pd.DataFrame({
                            'ID': [new_trans_id], 'InvestorID': [inv_id], 'Date': [ending_date_dt],
                            'Type': ['Phí'], 'Amount': [-total_fee], 'NAV': [ending_total_nav], 'UnitsChange': [-units_fee]
                        })
                        df_transactions = pd.concat([df_transactions, new_trans], ignore_index=True)
                        df_tranches.loc[df_tranches['InvestorID'] == inv_id, 'EntryDate'] = ending_date_dt
                        df_tranches.loc[df_tranches['InvestorID'] == inv_id, 'EntryNAV'] = ending_price_per_unit
                        df_tranches.loc[df_tranches['InvestorID'] == inv_id, 'HWM'] = ending_price_per_unit  # Added HWM reset
                    # Clean up zero-unit tranches
                    df_tranches = df_tranches[df_tranches['Units'] >= 1e-6]
                save_data(df_investors, df_tranches, df_transactions)
                st.success("Đã áp dụng phí và reset base.")
            except Exception as e:
                st.error(f"Lỗi khi áp dụng phí: {str(e)}")

# ------------------- Tính Phí Riêng -------------------
elif page == "Tính Phí Riêng":
    st.title("Tính Phí Riêng Cho Nhà Đầu Tư")
    if df_investors.empty:
        st.info("Chưa có nhà đầu tư nào.")
    else:
        investor_id = st.selectbox("Chọn ID Nhà Đầu Tư", df_investors['ID'])
        calc_date = st.date_input("Ngày Tính Phí", value=date.today())
        calc_total_nav_input = st.text_input("Total NAV Tại Ngày Tính", value=format_currency(latest_total_nav) if latest_total_nav else "0đ")
        calc_total_nav = parse_currency(calc_total_nav_input) or 0.0
        if st.button("Tính Toán"):
            if calc_total_nav <= 0:
                st.error("Total NAV phải lớn hơn 0.")
            else:
                try:
                    calc_date_dt = datetime.combine(calc_date, datetime.min.time())
                    inv_tranches = df_tranches[df_tranches['InvestorID'] == investor_id]
                    details = calculate_investor_fee_details(inv_tranches, calc_date_dt, calc_total_nav, df_tranches)
                    st.write(f"**Investor ID:** {investor_id}")
                    st.write(f"**Total Units:** {inv_tranches['Units'].sum():.2f}")
                    st.write(f"**Invested Value:** {format_currency(details['invested_value'])}")
                    st.write(f"**Balance:** {format_currency(details['balance'])}")
                    st.write(f"**Profit:** {format_currency(details['profit'])} ({details['profit_perc']:.2%})")
                    st.write(f"**Hurdle Value (6% pro-rata):** {format_currency(details['hurdle_value'])}")
                    st.write(f"**HWM Value:** {format_currency(details['hwm_value'])}")  # Added
                    st.write(f"**Excess Profit:** {format_currency(details['excess_profit'])}")
                    st.write(f"**Fee (20% on excess):** {format_currency(details['total_fee'])}")
                except Exception as e:
                    st.error(f"Lỗi khi tính phí: {str(e)}")
        st.info("Chỉ tính toán, không áp dụng. Dùng cho xem trước khi rút giữa năm.")

# ------------------- Xem Lịch Sử và Thống Kê -------------------
elif page == "Xem Lịch Sử và Thống Kê":
    st.title("Lịch Sử và Thống Kê")
    tab1, tab2, tab3 = st.tabs(["Thống Kê Giá Trị", "Lịch Sử Giao Dịch", "Chi Tiết Tranches"])
    
    with tab1:
        investor_filter = st.multiselect("Lọc theo Nhà Đầu Tư", df_investors['ID'], default=[])
        current_total_nav_input = st.text_input("Total NAV Hiện Tại", value=format_currency(latest_total_nav) if latest_total_nav else "0đ")
        current_total_nav = parse_currency(current_total_nav_input) or 0.0
        filtered_ids = investor_filter if investor_filter else df_investors['ID']

        balances = []
        chart_data = []
        for inv_id in filtered_ids:
            inv_tranches = df_tranches[df_tranches['InvestorID'] == inv_id]
            if not inv_tranches.empty:
                balance, profit, profit_perc = calc_balance_profit(inv_tranches, current_total_nav, df_tranches)
                balances.append({
                    'InvestorID': inv_id,
                    'TotalUnits': inv_tranches['Units'].sum(),
                    'Balance': balance,
                    'Profit': profit,
                    'Profit %': profit_perc
                })
                for _, tranche in inv_tranches.iterrows():
                    chart_data.append({
                        'InvestorID': inv_id,
                        'Date': tranche['EntryDate'],
                        'EntryPrice': tranche['EntryNAV'],
                        'InvestedValue': tranche['Units'] * tranche['EntryNAV']
                    })

        if balances:
            df_balances = pd.DataFrame(balances)
            st.dataframe(df_balances.style.format({
                'Balance': "{:,.0f}đ",
                'Profit': "{:,.0f}đ",
                'Profit %': "{:.2%}"
            }).applymap(lambda x: 'color: red' if isinstance(x, float) and x < 0 else '', subset=['Profit']))

            # Added pie chart for advanced visualization
            pie_data = df_balances[['InvestorID', 'Balance']]
            pie_chart = alt.Chart(pie_data).mark_arc().encode(
                theta='Balance:Q',
                color='InvestorID:N',
                tooltip=['InvestorID', 'Balance']
            ).properties(title="Phân bổ NAV theo Nhà Đầu Tư")
            st.altair_chart(pie_chart, use_container_width=True)

        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            line_chart = alt.Chart(df_chart).mark_line(point=True).encode(
                x='Date:T',
                y='InvestedValue:Q',
                color='InvestorID:N',
                tooltip=['InvestorID', 'Date', 'InvestedValue']
            ).properties(title="Giá trị đầu tư theo thời gian")
            st.altair_chart(line_chart, use_container_width=True)

            nav_df = df_transactions[df_transactions['Type'] == 'NAV Update'][['Date', 'NAV']]
            if not nav_df.empty:
                nav_chart = alt.Chart(nav_df).mark_line(point=True, color='orange').encode(
                    x='Date:T',
                    y='NAV:Q',
                    tooltip=['Date', 'NAV']
                ).properties(title="Total NAV theo thời gian")
                st.altair_chart(nav_chart, use_container_width=True)

            profit_chart_data = []
            for inv_id in filtered_ids:
                inv_tranches = df_tranches[df_tranches['InvestorID'] == inv_id]
                current_price = calc_price_per_unit(df_tranches, current_total_nav)
                for _, tranche in inv_tranches.iterrows():
                    profit_val = (current_price - tranche['EntryNAV']) * tranche['Units']
                    profit_chart_data.append({'InvestorID': inv_id, 'Date': tranche['EntryDate'], 'Profit': profit_val})
            df_profit_chart = pd.DataFrame(profit_chart_data)
            profit_chart = alt.Chart(df_profit_chart).mark_bar().encode(
                x='Date:T',
                y='Profit:Q',
                color='InvestorID:N',
                tooltip=['InvestorID', 'Date', 'Profit']
            ).properties(title="Lãi/Lỗ theo thời gian")
            st.altair_chart(profit_chart, use_container_width=True)

        # Filter
        year_filter = st.selectbox("Lọc theo Năm", ["Tất cả"] + sorted(df_transactions['Date'].dt.year.unique()))
        quarter_filter = st.selectbox("Lọc theo Quý", ["Tất cả", 1, 2, 3, 4])
        
        # Fund performance
        performance = calculate_fund_performance(df_transactions, df_tranches)
        if performance:
            st.subheader("Chỉ Số Hiệu Suất Quỹ")
            col1, col2 = st.columns(2)
            col1.metric("Time-Weighted Return (TWR)", f"{performance['TWR']:.2%}")
            col2.metric("Max Drawdown", f"{performance['Max Drawdown']:.2%}")
            
            # NAV per unit chart
            df_hist = performance['Historical']
            if year_filter != "Tất cả":
                df_hist = df_hist[df_hist['Date'].dt.year == year_filter]
            if quarter_filter != "Tất cả":
                df_hist = df_hist[df_hist['Date'].dt.quarter == quarter_filter]
            nav_unit_chart = alt.Chart(df_hist).mark_line(point=True).encode(
                x='Date:T',
                y='Price:Q',
                tooltip=['Date', 'Price']
            ).properties(title="NAV per Unit theo Thời Gian")
            st.altair_chart(nav_unit_chart, use_container_width=True)
        
        # Investor balances...
        # Add MWR for selected investor
        investor_id = st.selectbox("Tính MWR cho Nhà Đầu Tư", df_investors['ID'])
        if investor_id:
            current_total_nav = parse_currency(st.text_input("Total NAV Hiện Tại cho MWR", format_currency(latest_total_nav))) or 0.0
            irr = calculate_investor_irr(investor_id, df_transactions, current_total_nav, df_tranches, df_investors)
            st.metric("Money-Weighted Return (MWR/IRR)", f"{irr:.2%}" if irr is not None else "N/A")

    with tab2:
        if not df_transactions.empty:
            df_transactions_display = df_transactions.sort_values('Date', ascending=False).copy()
            df_transactions_display['Amount'] = df_transactions_display['Amount'].apply(format_currency)
            df_transactions_display['NAV'] = df_transactions_display['NAV'].apply(format_currency)
            st.dataframe(df_transactions_display.style.applymap(highlight_negative, subset=['Amount']))
        else:
            st.info("Chưa có giao dịch nào.")

    with tab3:
        if not df_tranches.empty:
            df_tranches_display = df_tranches.copy()
            df_tranches_display['EntryNAV'] = df_tranches_display['EntryNAV'].apply(format_currency)
            df_tranches_display['HWM'] = df_tranches_display['HWM'].apply(format_currency)  # Added
            st.dataframe(df_tranches_display)
        else:
            st.info("Chưa có tranches nào.")