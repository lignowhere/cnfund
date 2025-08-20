# helpers.py - FIXED VERSION without scipy dependency
import pandas as pd
import numpy as np
from datetime import datetime
import warnings

def format_currency(x):
    """Format currency với xử lý NaN và số âm"""
    if pd.isna(x) or x is None:
        return "0đ"
    try:
        return f"{float(x):,.0f}đ"
    except (ValueError, TypeError):
        return "0đ"

def parse_currency(s):
    """Parse currency string với error handling tốt hơn"""
    if isinstance(s, (int, float)):
        return float(s) if not pd.isna(s) else 0.0
    
    if not isinstance(s, str):
        return 0.0
    
    try:
        # Remove currency symbols and whitespace
        cleaned = s.replace('đ', '').replace(',', '').strip()
        if cleaned == '' or cleaned == 'N/A':
            return 0.0
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0

def get_latest_total_nav(df_transactions):
    """Lấy Total NAV mới nhất với validation"""
    if df_transactions.empty:
        return None
    
    # Lọc transactions có NAV > 0 và không phải phí
    df_nav = df_transactions[
        (df_transactions['NAV'] > 0) & 
        (df_transactions['Type'] != 'Phí') &
        (~pd.isna(df_transactions['NAV']))
    ]
    
    if df_nav.empty:
        return None
    
    # Lấy NAV mới nhất
    latest_nav = df_nav.sort_values('Date', ascending=False).iloc[0]['NAV']
    return float(latest_nav) if not pd.isna(latest_nav) else None

def highlight_negative(val):
    """Highlight negative values - ENHANCED"""
    try:
        num_val = val
        if isinstance(val, str):
            num_val = parse_currency(val)
        
        if num_val is not None and not pd.isna(num_val):
            if num_val < -1e-6:  # Use epsilon for floating point comparison
                return 'color: red; font-weight: bold'
            elif num_val > 1e-6:
                return 'color: green; font-weight: bold'
            else:
                return 'color: black'
    except:
        return ''
    return ''

def calc_price_per_unit(df_tranches, total_nav):
    """Tính giá per unit với validation - FIXED EDGE CASES"""
    if df_tranches.empty or total_nav is None or total_nav <= 0:
        return 1000.0  # Default unit price for empty fund
    
    try:
        total_units = float(df_tranches['Units'].sum())
        if total_units <= 1e-6:  # No units outstanding
            return 1000.0
        
        price = float(total_nav) / total_units
        
        # Sanity check - giá không nên quá thấp hoặc quá cao
        if price <= 0:
            return 1000.0
        elif price > 1e8:  # 100 triệu đồng per unit - có thể có lỗi
            warnings.warn(f"Giá per unit rất cao: {price:,.0f}đ - kiểm tra dữ liệu")
        
        return price
        
    except (ValueError, TypeError, ZeroDivisionError):
        return 1000.0

def calc_balance_profit(inv_tranches, total_nav, df_tranches_global):
    """Tính balance và profit cho investor - ENHANCED"""
    if inv_tranches.empty or total_nav is None or total_nav <= 0:
        return 0.0, 0.0, 0.0
    
    try:
        price_per_unit = calc_price_per_unit(df_tranches_global, total_nav)
        investor_units = float(inv_tranches['Units'].sum())
        balance = round(investor_units * price_per_unit, 2)
        
        # FIXED: Tính invested value chính xác
        invested_value = 0.0
        for _, tranche in inv_tranches.iterrows():
            entry_nav = float(tranche.get('EntryNAV', 0))
            units = float(tranche.get('Units', 0))
            invested_value += entry_nav * units
        
        profit = balance - invested_value
        profit_perc = profit / invested_value if invested_value > 1e-6 else 0.0
        
        return balance, profit, profit_perc
        
    except (ValueError, TypeError):
        return 0.0, 0.0, 0.0

def calculate_tav(df_tranches, total_nav):
    """Calculate Total Asset Value - alias for total_nav"""
    return float(total_nav) if total_nav is not None else 0.0

def calculate_fund_performance(df_transactions, df_tranches):
    """Tính performance của fund - SIMPLIFIED VERSION"""
    if df_transactions.empty:
        return {}
    
    try:
        df_trans = df_transactions.sort_values('Date').copy()
        historical = []
        current_total_units = 0.0
        
        for _, trans in df_trans.iterrows():
            # Update units based on transaction type
            if trans['Type'] in ['Nạp', 'Rút', 'Phí'] and not pd.isna(trans['UnitsChange']):
                current_total_units += float(trans['UnitsChange'])
                current_total_units = max(0, current_total_units)  # Ensure non-negative
            
            # Record NAV data points
            if trans['Type'] == 'NAV Update' or (trans['NAV'] > 0 and trans['Type'] != 'Phí'):
                if current_total_units > 1e-6:  # Only if we have units
                    price = float(trans['NAV']) / current_total_units
                    historical.append({
                        'Date': trans['Date'], 
                        'NAV': float(trans['NAV']), 
                        'Units': current_total_units, 
                        'Price': price
                    })
        
        if not historical:
            return {}
        
        df_hist = pd.DataFrame(historical)
        
        # SIMPLIFIED: Time-weighted return calculation
        if len(df_hist) < 2:
            return {'TWR': 0.0, 'Max Drawdown': 0.0, 'Historical': df_hist}
        
        # Calculate period returns
        df_hist['Return'] = df_hist['Price'].pct_change().fillna(0)
        
        # Remove extreme outliers that might be data errors
        df_hist = df_hist[abs(df_hist['Return']) < 5.0]  # Max 500% return per period
        
        # Time-weighted return (geometric mean)
        twr = np.prod(1 + df_hist['Return'].fillna(0)) - 1
        
        # SIMPLIFIED: Drawdown calculation
        running_max = df_hist['Price'].expanding().max()
        drawdown = (df_hist['Price'] - running_max) / running_max
        max_dd = float(drawdown.min()) if not drawdown.empty else 0.0
        
        # Annualized metrics if we have enough data
        total_days = (df_hist['Date'].max() - df_hist['Date'].min()).days
        annualized_twr = 0.0
        if total_days > 30:  # At least 1 month of data
            years = total_days / 365.25
            annualized_twr = (1 + twr) ** (1/years) - 1 if years > 0 else twr
        
        return {
            'TWR': twr, 
            'Annualized_TWR': annualized_twr,
            'Max Drawdown': max_dd, 
            'Historical': df_hist,
            'Total_Days': total_days,
            'Volatility': float(df_hist['Return'].std()) if len(df_hist) > 1 else 0.0
        }
        
    except Exception as e:
        warnings.warn(f"Error calculating fund performance: {str(e)}")
        return {}

def calculate_xirr_simple(cashflows, dates, guess=0.1, max_iterations=1000):
    """Tính XIRR đơn giản không cần scipy - Newton-Raphson method"""
    if len(cashflows) != len(dates) or len(cashflows) < 2:
        return None
    
    # Convert to numpy arrays for better performance
    cashflows = np.array([float(cf) for cf in cashflows])
    dates = pd.to_datetime(dates)
    
    # Check for valid cashflow pattern
    if all(cf >= 0 for cf in cashflows) or all(cf <= 0 for cf in cashflows):
        return None  # Need both positive and negative cashflows
    
    min_date = dates.min()
    days_diff = np.array([(d - min_date).days for d in dates])
    
    def xnpv(rate):
        """Calculate XNPV for given rate"""
        if rate <= -1:  # Avoid division by zero
            return float('inf')
        return sum(cf / (1 + rate) ** (days / 365.25) for cf, days in zip(cashflows, days_diff))
    
    def xnpv_derivative(rate):
        """Derivative of XNPV for Newton-Raphson"""
        if rate <= -1:
            return float('inf')
        return sum(-cf * (days / 365.25) / (1 + rate) ** (days / 365.25 + 1) for cf, days in zip(cashflows, days_diff))
    
    # Newton-Raphson method
    rate = guess
    for i in range(max_iterations):
        try:
            npv = xnpv(rate)
            npv_derivative = xnpv_derivative(rate)
            
            if abs(npv) < 1e-6:  # Converged
                return rate
            
            if abs(npv_derivative) < 1e-10:  # Avoid division by zero
                break
                
            new_rate = rate - npv / npv_derivative
            
            # Keep rate in reasonable bounds
            if new_rate <= -0.99:
                new_rate = -0.99 + 1e-6
            elif new_rate > 10:
                new_rate = 10
            
            if abs(new_rate - rate) < 1e-8:  # Converged
                return new_rate
                
            rate = new_rate
            
        except (OverflowError, ZeroDivisionError):
            break
    
    # If Newton-Raphson fails, try binary search
    return _xirr_binary_search(cashflows, days_diff)

def _xirr_binary_search(cashflows, days_diff, tolerance=1e-6):
    """Binary search fallback for XIRR calculation"""
    def xnpv(rate):
        if rate <= -1:
            return float('inf')
        return sum(cf / (1 + rate) ** (days / 365.25) for cf, days in zip(cashflows, days_diff))
    
    # Binary search
    low, high = -0.99, 10.0  # Reasonable range: -99% to 1000%
    
    for _ in range(1000):  # Max iterations
        if high - low < tolerance:
            break
            
        mid = (low + high) / 2
        npv = xnpv(mid)
        
        if abs(npv) < tolerance:
            return mid
        elif npv > 0:
            low = mid
        else:
            high = mid
    
    return (low + high) / 2 if abs(xnpv((low + high) / 2)) < 1e6 else None

def calculate_investor_irr(investor_id, df_transactions, current_nav, df_tranches, df_investors):
    """Tính IRR cho nhà đầu tư - SIMPLIFIED VERSION"""
    try:
        # Get all transactions for this investor
        trans = df_transactions[df_transactions['InvestorID'] == investor_id].sort_values('Date')
        
        if trans.empty:
            return None
        
        cashflows = []
        dates = []
        
        for _, t in trans.iterrows():
            # Negative for outflows (from investor perspective)
            if t['Type'] == 'Nạp':
                cashflows.append(-float(t['Amount']))  # Money out from investor
            elif t['Type'] in ['Rút', 'Phí']:
                cashflows.append(-float(t['Amount']))  # Money in to investor (amount is already negative)
            
            dates.append(t['Date'])
        
        # Add current balance as final positive cashflow
        inv_tranches = df_tranches[df_tranches['InvestorID'] == investor_id]
        if not inv_tranches.empty and current_nav > 0:
            balance, _, _ = calc_balance_profit(inv_tranches, current_nav, df_tranches)
            if balance > 1e-6:  # Only if there's meaningful balance
                cashflows.append(float(balance))
                dates.append(datetime.now())
        
        # Need at least one inflow and one outflow
        if len(cashflows) < 2:
            return None
            
        return calculate_xirr_simple(cashflows, dates)
        
    except Exception as e:
        warnings.warn(f"Error calculating IRR for investor {investor_id}: {str(e)}")
        return None

def validate_financial_data(df_investors, df_tranches, df_transactions):
    """Comprehensive validation of financial data integrity"""
    errors = []
    warnings_list = []
    
    try:
        # Check for data consistency
        if not df_transactions.empty:
            # Check for future dates
            future_trans = df_transactions[df_transactions['Date'] > datetime.now()]
            if not future_trans.empty:
                errors.append(f"Có {len(future_trans)} giao dịch ở tương lai")
            
            # Check for impossible values
            extreme_amounts = df_transactions[abs(df_transactions['Amount']) > 1e12]
            if not extreme_amounts.empty:
                warnings_list.append(f"Có {len(extreme_amounts)} giao dịch với số tiền cực lớn")
            
            # Check for missing NAV
            missing_nav = df_transactions[(df_transactions['NAV'] <= 0) & (df_transactions['Type'] != 'Phí')]
            if not missing_nav.empty:
                errors.append(f"Có {len(missing_nav)} giao dịch với NAV <= 0")
        
        if not df_tranches.empty:
            # Check for negative units
            negative_units = df_tranches[df_tranches['Units'] < 0]
            if not negative_units.empty:
                errors.append(f"Có {len(negative_units)} tranche với units âm")
            
            # Check HWM consistency
            hwm_errors = df_tranches[df_tranches['HWM'] < df_tranches['EntryNAV']]
            if not hwm_errors.empty:
                warnings_list.append(f"Có {len(hwm_errors)} tranche với HWM < EntryNAV")
        
        # Cross-table validations
        if not df_investors.empty and not df_tranches.empty:
            orphaned_tranches = df_tranches[~df_tranches['InvestorID'].isin(df_investors['ID'])]
            if not orphaned_tranches.empty:
                errors.append(f"Có {len(orphaned_tranches)} tranche không có investor tương ứng")
    
    except Exception as e:
        errors.append(f"Lỗi khi validate dữ liệu: {str(e)}")
    
    return {
        'errors': errors,
        'warnings': warnings_list,
        'is_valid': len(errors) == 0
    }

def calculate_risk_metrics(df_transactions, df_tranches, current_nav):
    """Calculate risk metrics for the fund - SIMPLIFIED VERSION"""
    try:
        performance = calculate_fund_performance(df_transactions, df_tranches)
        
        if not performance or performance.get('Historical', pd.DataFrame()).empty:
            return {}
        
        df_hist = performance['Historical']
        returns = df_hist['Return'].dropna()
        
        if len(returns) < 2:
            return {}
        
        # Basic risk metrics
        volatility = float(returns.std())
        downside_returns = returns[returns < 0]
        downside_volatility = float(downside_returns.std()) if len(downside_returns) > 0 else 0.0
        
        # Sharpe ratio (assuming 0% risk-free rate)
        avg_return = float(returns.mean())
        sharpe_ratio = avg_return / volatility if volatility > 0 else 0.0
        
        # Sortino ratio
        sortino_ratio = avg_return / downside_volatility if downside_volatility > 0 else 0.0
        
        # Value at Risk (95% confidence) - simple percentile method
        var_95 = float(returns.quantile(0.05)) if len(returns) > 20 else 0.0
        
        return {
            'Volatility': volatility,
            'Downside_Volatility': downside_volatility,
            'Sharpe_Ratio': sharpe_ratio,
            'Sortino_Ratio': sortino_ratio,
            'VaR_95': var_95,
            'Max_Drawdown': performance.get('Max Drawdown', 0.0),
            'Skewness': float(returns.skew()) if hasattr(returns, 'skew') else 0.0,
            'Kurtosis': float(returns.kurtosis()) if hasattr(returns, 'kurtosis') else 0.0
        }
        
    except Exception as e:
        warnings.warn(f"Error calculating risk metrics: {str(e)}")
        return {}

def format_percentage(value, decimal_places=2):
    """Format percentage with proper handling of edge cases"""
    if pd.isna(value) or value is None:
        return "N/A"
    
    try:
        return f"{float(value):.{decimal_places}%}"
    except (ValueError, TypeError):
        return "N/A"

def calculate_compound_return(start_value, end_value, years):
    """Calculate compound annual growth rate"""
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    
    try:
        return (end_value / start_value) ** (1 / years) - 1
    except (ValueError, ZeroDivisionError, OverflowError):
        return 0.0

def safe_divide(numerator, denominator, default=0.0):
    """Safe division with default value for zero denominator"""
    try:
        if abs(denominator) < 1e-10:
            return default
        return float(numerator) / float(denominator)
    except (ValueError, TypeError, ZeroDivisionError):
        return default