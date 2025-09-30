"""
Color Coding for Financial Data
Green for profit, Red for loss, consistent across system
"""

import streamlit as st

class ColorCoding:
    """Consistent color coding for financial data"""

    # Color constants
    GREEN = "#10b981"  # Success green for profit
    RED = "#ef4444"    # Error red for loss
    GRAY = "#6b7280"   # Neutral gray for zero/no change
    ORANGE = "#f59e0b" # Warning orange for alerts

    @staticmethod
    def format_profit_loss(value: float, prefix: str = "", suffix: str = "đ") -> str:
        """
        Format profit/loss with color coding

        Args:
            value: The numeric value
            prefix: Prefix (e.g., "+", "-")
            suffix: Suffix (e.g., "đ", "%")

        Returns:
            HTML string with colored value
        """
        if value > 0:
            color = ColorCoding.GREEN
            sign = "+" if not prefix else prefix
        elif value < 0:
            color = ColorCoding.RED
            sign = "" if prefix else ""  # Negative sign already in number
        else:
            color = ColorCoding.GRAY
            sign = ""

        # Format number with commas
        abs_value = abs(value)
        formatted = f"{abs_value:,.0f}"

        return f'<span style="color: {color}; font-weight: 600;">{sign}{formatted}{suffix}</span>'

    @staticmethod
    def format_percentage(value: float, show_sign: bool = True) -> str:
        """
        Format percentage with color coding

        Args:
            value: The percentage value (0.05 = 5%)
            show_sign: Whether to show +/- sign

        Returns:
            HTML string with colored percentage
        """
        percentage = value * 100

        if percentage > 0:
            color = ColorCoding.GREEN
            sign = "+" if show_sign else ""
        elif percentage < 0:
            color = ColorCoding.RED
            sign = "" if show_sign else ""
        else:
            color = ColorCoding.GRAY
            sign = ""

        return f'<span style="color: {color}; font-weight: 600;">{sign}{percentage:.2f}%</span>'

    @staticmethod
    def format_currency_change(value: float, show_arrow: bool = True) -> str:
        """
        Format currency change with color, sign, and optional arrow

        Args:
            value: The change amount
            show_arrow: Whether to show ↑/↓ arrows

        Returns:
            HTML string with colored value and arrow
        """
        if value > 0:
            color = ColorCoding.GREEN
            arrow = "↑ " if show_arrow else ""
            sign = "+"
        elif value < 0:
            color = ColorCoding.RED
            arrow = "↓ " if show_arrow else ""
            sign = ""
        else:
            color = ColorCoding.GRAY
            arrow = "→ " if show_arrow else ""
            sign = ""

        abs_value = abs(value)
        formatted = f"{abs_value:,.0f}"

        return f'<span style="color: {color}; font-weight: 600;">{arrow}{sign}{formatted}đ</span>'

    @staticmethod
    def metric_card_colored(label: str, value: float, delta: float = None,
                           format_type: str = "currency"):
        """
        Render a metric card with colored delta

        Args:
            label: Metric label
            value: Main value
            delta: Change amount
            format_type: 'currency' or 'percentage'
        """
        # Format main value
        if format_type == "currency":
            value_str = f"{value:,.0f}đ"
        elif format_type == "percentage":
            value_str = f"{value:.2f}%"
        else:
            value_str = str(value)

        # Format delta if provided
        delta_html = ""
        if delta is not None:
            if format_type == "currency":
                delta_html = ColorCoding.format_currency_change(delta)
            elif format_type == "percentage":
                delta_html = ColorCoding.format_percentage(delta / 100)  # Assuming delta is already %

        html = f"""
        <div style="
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
        ">
            <div style="color: #6b7280; font-size: 0.875rem; margin-bottom: 0.25rem;">
                {label}
            </div>
            <div style="color: #1f2937; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem;">
                {value_str}
            </div>
            {f'<div style="font-size: 0.875rem;">{delta_html}</div>' if delta_html else ''}
        </div>
        """

        st.markdown(html, unsafe_allow_html=True)

    @staticmethod
    def add_global_color_classes():
        """Add global CSS classes for profit/loss colors"""
        css = """
        <style>
        /* Profit/Loss Color Classes */
        .profit {
            color: #10b981 !important;
            font-weight: 600;
        }

        .loss {
            color: #ef4444 !important;
            font-weight: 600;
        }

        .neutral {
            color: #6b7280 !important;
            font-weight: 600;
        }

        /* Background variants */
        .profit-bg {
            background-color: #ecfdf5 !important;
            color: #10b981 !important;
        }

        .loss-bg {
            background-color: #fef2f2 !important;
            color: #ef4444 !important;
        }

        /* Table cell colors */
        .dataframe td.profit {
            background-color: #ecfdf5 !important;
        }

        .dataframe td.loss {
            background-color: #fef2f2 !important;
        }

        /* Arrow indicators */
        .arrow-up::before {
            content: "↑ ";
            color: #10b981;
        }

        .arrow-down::before {
            content: "↓ ";
            color: #ef4444;
        }

        .arrow-neutral::before {
            content: "→ ";
            color: #6b7280;
        }
        </style>
        """

        st.markdown(css, unsafe_allow_html=True)

    @staticmethod
    def color_dataframe_column(df, column_name: str, is_percentage: bool = False):
        """
        Apply color styling to a specific dataframe column

        Args:
            df: Pandas DataFrame
            column_name: Name of column to color
            is_percentage: Whether values are percentages

        Returns:
            Styled DataFrame
        """
        def color_value(val):
            """Color based on value"""
            try:
                numeric_val = float(str(val).replace('%', '').replace(',', '').replace('đ', ''))
                if numeric_val > 0:
                    return 'color: #10b981; font-weight: 600;'
                elif numeric_val < 0:
                    return 'color: #ef4444; font-weight: 600;'
                else:
                    return 'color: #6b7280; font-weight: 600;'
            except:
                return ''

        return df.style.applymap(color_value, subset=[column_name])


# Convenience functions
def profit_loss_html(value: float, suffix: str = "đ") -> str:
    """Quick profit/loss formatting"""
    return ColorCoding.format_profit_loss(value, suffix=suffix)

def percentage_html(value: float) -> str:
    """Quick percentage formatting"""
    return ColorCoding.format_percentage(value)

def currency_change_html(value: float) -> str:
    """Quick currency change formatting"""
    return ColorCoding.format_currency_change(value)