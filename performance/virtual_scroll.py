"""
Virtual Scrolling for Large Datasets in CNFund
Efficient rendering of large tables and lists
"""

import streamlit as st
import pandas as pd
from typing import List, Callable, Optional, Any
from .performance_monitor import track_performance

class VirtualScrollTable:
    """Virtual scrolling implementation for large datasets"""

    def __init__(self, data: pd.DataFrame, page_size: int = 50):
        """
        Initialize virtual scroll table

        Args:
            data: Full dataset
            page_size: Number of rows to display at once
        """
        self.data = data
        self.page_size = page_size
        self.total_rows = len(data)
        self.total_pages = (self.total_rows + page_size - 1) // page_size

    @track_performance("virtual_scroll_render")
    def render(self, container_key: str = "virtual_table"):
        """Render virtual scroll table with pagination"""

        # Initialize page state
        page_key = f"{container_key}_page"
        if page_key not in st.session_state:
            st.session_state[page_key] = 0

        current_page = st.session_state[page_key]

        # Calculate visible range
        start_idx = current_page * self.page_size
        end_idx = min(start_idx + self.page_size, self.total_rows)

        # Display info
        st.caption(f"Showing {start_idx + 1}-{end_idx} of {self.total_rows} rows")

        # Render visible data
        visible_data = self.data.iloc[start_idx:end_idx]
        st.dataframe(visible_data, use_container_width=True, hide_index=True)

        # Pagination controls
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

        with col1:
            if st.button("⏮️ First", key=f"{container_key}_first", disabled=current_page == 0):
                st.session_state[page_key] = 0
                st.rerun()

        with col2:
            if st.button("◀️ Prev", key=f"{container_key}_prev", disabled=current_page == 0):
                st.session_state[page_key] = current_page - 1
                st.rerun()

        with col3:
            # Page selector
            page_options = list(range(1, self.total_pages + 1))
            selected_page = st.selectbox(
                "Page",
                page_options,
                index=current_page,
                key=f"{container_key}_select",
                label_visibility="collapsed"
            )
            if selected_page - 1 != current_page:
                st.session_state[page_key] = selected_page - 1
                st.rerun()

        with col4:
            if st.button("Next ▶️", key=f"{container_key}_next", disabled=current_page >= self.total_pages - 1):
                st.session_state[page_key] = current_page + 1
                st.rerun()

        with col5:
            if st.button("Last ⏭️", key=f"{container_key}_last", disabled=current_page >= self.total_pages - 1):
                st.session_state[page_key] = self.total_pages - 1
                st.rerun()

class InfiniteScrollList:
    """Infinite scrolling for lists"""

    def __init__(self, data: List[Any], initial_count: int = 20, load_more_count: int = 20):
        """
        Initialize infinite scroll list

        Args:
            data: Full list of items
            initial_count: Initial number of items to show
            load_more_count: Number of items to load each time
        """
        self.data = data
        self.initial_count = initial_count
        self.load_more_count = load_more_count
        self.total_items = len(data)

    def render(self, render_item: Callable, container_key: str = "infinite_scroll"):
        """
        Render infinite scroll list

        Args:
            render_item: Function to render each item
            container_key: Unique key for this list
        """
        # Initialize visible count
        count_key = f"{container_key}_visible_count"
        if count_key not in st.session_state:
            st.session_state[count_key] = self.initial_count

        visible_count = st.session_state[count_key]
        visible_data = self.data[:visible_count]

        # Render visible items
        for item in visible_data:
            render_item(item)

        # Load more button
        if visible_count < self.total_items:
            remaining = self.total_items - visible_count
            load_count = min(self.load_more_count, remaining)

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(f"📥 Load {load_count} more ({remaining} remaining)", key=f"{container_key}_load_more"):
                    st.session_state[count_key] = visible_count + load_count
                    st.rerun()
        else:
            st.info("✅ All items loaded")

class FilteredVirtualTable:
    """Virtual table with built-in filtering"""

    def __init__(self, data: pd.DataFrame, page_size: int = 50):
        self.data = data
        self.page_size = page_size

    @track_performance("filtered_virtual_render")
    def render(self, container_key: str = "filtered_table", filterable_columns: Optional[List[str]] = None):
        """Render table with filters"""

        # Initialize filter state
        filter_key = f"{container_key}_filters"
        if filter_key not in st.session_state:
            st.session_state[filter_key] = {}

        # Filter UI
        with st.expander("🔍 Filters", expanded=False):
            if filterable_columns is None:
                filterable_columns = list(self.data.columns)

            filters = st.session_state[filter_key]

            for col in filterable_columns:
                if self.data[col].dtype == 'object':
                    # Text filter
                    unique_values = self.data[col].unique().tolist()
                    selected = st.multiselect(
                        col,
                        options=unique_values,
                        default=filters.get(col, unique_values),
                        key=f"{container_key}_filter_{col}"
                    )
                    filters[col] = selected

                elif pd.api.types.is_numeric_dtype(self.data[col]):
                    # Range filter
                    min_val = float(self.data[col].min())
                    max_val = float(self.data[col].max())

                    if col not in filters:
                        filters[col] = (min_val, max_val)

                    range_val = st.slider(
                        col,
                        min_value=min_val,
                        max_value=max_val,
                        value=filters[col],
                        key=f"{container_key}_filter_{col}"
                    )
                    filters[col] = range_val

            st.session_state[filter_key] = filters

        # Apply filters
        filtered_data = self.data.copy()

        for col, filter_val in filters.items():
            if col in filterable_columns:
                if isinstance(filter_val, list):
                    filtered_data = filtered_data[filtered_data[col].isin(filter_val)]
                elif isinstance(filter_val, tuple):
                    filtered_data = filtered_data[
                        (filtered_data[col] >= filter_val[0]) &
                        (filtered_data[col] <= filter_val[1])
                    ]

        # Show filter info
        if len(filtered_data) < len(self.data):
            st.info(f"📊 Filtered: {len(filtered_data)} of {len(self.data)} rows")

        # Render virtual table
        if not filtered_data.empty:
            virtual_table = VirtualScrollTable(filtered_data, self.page_size)
            virtual_table.render(container_key)
        else:
            st.warning("No data matches the selected filters")

class SearchableVirtualTable:
    """Virtual table with search functionality"""

    def __init__(self, data: pd.DataFrame, page_size: int = 50):
        self.data = data
        self.page_size = page_size

    def render(self, container_key: str = "searchable_table", searchable_columns: Optional[List[str]] = None):
        """Render table with search"""

        if searchable_columns is None:
            searchable_columns = list(self.data.select_dtypes(include=['object']).columns)

        # Search UI
        search_query = st.text_input(
            "🔍 Search",
            key=f"{container_key}_search",
            placeholder=f"Search in: {', '.join(searchable_columns)}"
        )

        # Apply search
        if search_query:
            mask = pd.Series([False] * len(self.data))

            for col in searchable_columns:
                mask |= self.data[col].astype(str).str.contains(search_query, case=False, na=False)

            filtered_data = self.data[mask]

            if len(filtered_data) < len(self.data):
                st.info(f"🔍 Found: {len(filtered_data)} of {len(self.data)} rows")
        else:
            filtered_data = self.data

        # Render virtual table
        if not filtered_data.empty:
            virtual_table = VirtualScrollTable(filtered_data, self.page_size)
            virtual_table.render(container_key)
        else:
            st.warning("No results found")

# Efficient transaction table renderer
def render_transaction_table_virtual(transactions_df: pd.DataFrame, page_size: int = 50):
    """Optimized renderer for transaction tables"""

    if transactions_df.empty:
        st.info("No transactions found")
        return

    # Create searchable + filterable table
    col1, col2 = st.columns([2, 1])

    with col1:
        search_query = st.text_input("🔍 Search transactions", placeholder="Search by investor, type, etc.")

    with col2:
        # Quick filters
        if 'transaction_type' in transactions_df.columns:
            types = transactions_df['transaction_type'].unique().tolist()
            selected_types = st.multiselect("Type", types, default=types)
        else:
            selected_types = None

    # Apply filters
    filtered_df = transactions_df.copy()

    if search_query:
        search_cols = [col for col in filtered_df.columns if filtered_df[col].dtype == 'object']
        mask = pd.Series([False] * len(filtered_df))

        for col in search_cols:
            mask |= filtered_df[col].astype(str).str.contains(search_query, case=False, na=False)

        filtered_df = filtered_df[mask]

    if selected_types:
        filtered_df = filtered_df[filtered_df['transaction_type'].isin(selected_types)]

    # Show info
    if len(filtered_df) < len(transactions_df):
        st.caption(f"📊 Showing {len(filtered_df)} of {len(transactions_df)} transactions")

    # Render with virtual scrolling
    if not filtered_df.empty:
        virtual_table = VirtualScrollTable(filtered_df, page_size)
        virtual_table.render("transactions")
    else:
        st.warning("No transactions match your filters")

# Efficient investor list renderer
def render_investor_list_virtual(investors: List, page_size: int = 20):
    """Optimized renderer for investor lists"""

    if not investors:
        st.info("No investors found")
        return

    # Search
    search_query = st.text_input("🔍 Search investors", placeholder="Search by name, ID, etc.")

    # Filter investors
    if search_query:
        filtered_investors = [
            inv for inv in investors
            if search_query.lower() in str(inv).lower()
        ]
    else:
        filtered_investors = investors

    # Show count
    if len(filtered_investors) < len(investors):
        st.caption(f"👥 Showing {len(filtered_investors)} of {len(investors)} investors")

    # Render with infinite scroll
    def render_investor_card(investor):
        with st.container():
            st.markdown(f"**{investor.get('name', 'Unknown')}**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ID", investor.get('id', '-'))
            with col2:
                st.metric("Capital", f"{investor.get('capital', 0):,.0f}")
            with col3:
                st.metric("Shares", f"{investor.get('shares', 0):,.0f}")
            st.divider()

    scroll_list = InfiniteScrollList(filtered_investors, initial_count=page_size, load_more_count=page_size)
    scroll_list.render(render_investor_card, "investors")

# Export helper
@track_performance("export_filtered_data")
def export_filtered_dataframe(df: pd.DataFrame, filename: str = "export.csv"):
    """Export filtered dataframe efficiently"""
    csv = df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=filename,
        mime="text/csv"
    )