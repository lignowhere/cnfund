#!/usr/bin/env python3
"""
Comprehensive Stress Test for Fund Management System
Tests with multiple investors, transactions, fee periods to validate calculations
"""

import random
import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import pandas as pd
from decimal import Decimal, getcontext

# Set high precision for financial calculations
getcontext().prec = 28

class FundStressTester:
    """Comprehensive stress tester for fund management system"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
        self.test_results = {}
        self.validation_errors = []
        self.performance_metrics = {}
        
        # Test scenarios configuration
        self.scenarios = {
            'light': {
                'investors': 5,
                'transactions_per_investor': 3,
                'fee_periods': 2,
                'nav_updates': 20
            },
            'medium': {
                'investors': 15,
                'transactions_per_investor': 8,
                'fee_periods': 3,
                'nav_updates': 50
            },
            'heavy': {
                'investors': 50,
                'transactions_per_investor': 15,
                'fee_periods': 5,
                'nav_updates': 100
            },
            'extreme': {
                'investors': 100,
                'transactions_per_investor': 25,
                'fee_periods': 7,
                'nav_updates': 200
            }
        }
    
    def run_comprehensive_test(self, scenario: str = 'medium') -> Dict[str, Any]:
        """Run comprehensive stress test"""
        print(f"\n🚀 Starting {scenario.upper()} stress test...")
        
        start_time = datetime.now()
        
        try:
            # Clear existing data
            self._clear_test_data()
            
            # Get scenario config
            config = self.scenarios.get(scenario, self.scenarios['medium'])
            
            # Phase 1: Create test investors
            print(f"📝 Phase 1: Creating {config['investors']} test investors...")
            investors = self._create_test_investors(config['investors'])
            
            # Phase 2: Generate transactions over time
            print(f"💸 Phase 2: Generating transactions...")
            self._generate_test_transactions(investors, config)
            
            # Phase 3: Apply fees multiple times
            print(f"🧮 Phase 3: Applying fees for {config['fee_periods']} periods...")
            self._apply_multiple_fee_periods(config['fee_periods'])
            
            # Phase 4: Generate more transactions after fees
            print(f"💰 Phase 4: Post-fee transactions...")
            self._generate_post_fee_transactions(investors)
            
            # Phase 5: Validate all calculations
            print(f"🔍 Phase 5: Comprehensive validation...")
            validation_results = self._comprehensive_validation()
            
            # Phase 6: Performance analysis
            print(f"📊 Phase 6: Performance analysis...")
            performance_results = self._analyze_performance()
            
            end_time = datetime.now()
            test_duration = (end_time - start_time).total_seconds()
            
            # Compile results
            results = {
                'scenario': scenario,
                'config': config,
                'duration_seconds': test_duration,
                'data_stats': self._get_data_statistics(),
                'validation': validation_results,
                'performance': performance_results,
                'success': len(self.validation_errors) == 0
            }
            
            self.test_results = results
            return results
            
        except Exception as e:
            print(f"❌ Stress test failed: {str(e)}")
            return {
                'scenario': scenario,
                'success': False,
                'error': str(e),
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }
    
    def _clear_test_data(self):
        """Clear existing test data"""
        # Keep only Fund Manager, remove test investors
        self.fund_manager.investors = [
            inv for inv in self.fund_manager.investors 
            if inv.is_fund_manager or not inv.name.startswith('Test_')
        ]
        
        # Clear test tranches and transactions
        test_investor_ids = {
            inv.id for inv in self.fund_manager.investors 
            if inv.name.startswith('Test_')
        }
        
        self.fund_manager.tranches = [
            t for t in self.fund_manager.tranches 
            if t.investor_id not in test_investor_ids
        ]
        
        self.fund_manager.transactions = [
            t for t in self.fund_manager.transactions 
            if t.investor_id not in test_investor_ids and 'Test' not in t.type
        ]
        
        self.fund_manager.fee_records = [
            f for f in self.fund_manager.fee_records 
            if f.investor_id not in test_investor_ids
        ]
        
        self.validation_errors = []
    
    def _create_test_investors(self, count: int) -> List:
        """Create test investors with realistic data"""
        investors = []
        
        # Realistic Vietnamese names and data
        names = [
            "Nguyễn Văn Anh", "Trần Thị Bình", "Lê Văn Cường", "Phạm Thị Dung", "Hoàng Văn Em",
            "Vũ Thị Hoa", "Đỗ Văn Giang", "Bùi Thị Hạnh", "Lý Văn Hùng", "Mai Thị Lan",
            "Phan Văn Long", "Võ Thị Mai", "Đinh Văn Nam", "Chu Thị Oanh", "Tạ Văn Phong",
            "Đặng Thị Quỳnh", "Nghiêm Văn Sơn", "Lê Thị Trang", "Ngô Văn Tuấn", "Hồ Thị Vân"
        ]
        
        for i in range(count):
            # Use realistic names with fallback
            name = f"Test_{names[i % len(names)]}_{i+1}"
            
            success, message = self.fund_manager.add_investor(
                name=name,
                phone=f"09{random.randint(10000000, 99999999)}",
                email=f"test{i+1}@example.com",
                address=f"Test Address {i+1}, District {random.randint(1, 12)}, HCMC"
            )
            
            if success:
                # Find the created investor
                investor = next(
                    (inv for inv in self.fund_manager.investors if inv.name == name), 
                    None
                )
                if investor:
                    investors.append(investor)
            
        print(f"✅ Created {len(investors)} test investors")
        return investors
    
    def _generate_test_transactions(self, investors: List, config: Dict):
        """Generate realistic transaction patterns"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        # Initialize fund with NAV
        initial_nav = 1_000_000_000  # 1B VND
        self.fund_manager.process_nav_update(initial_nav, start_date)
        
        current_nav = initial_nav
        
        # Generate transactions for each investor
        for investor in investors:
            investor_transactions = config['transactions_per_investor']
            
            for trans_num in range(investor_transactions):
                # Generate random date
                days_range = (end_date - start_date).days
                random_days = random.randint(0, days_range)
                trans_date = start_date + timedelta(days=random_days)
                
                # Determine transaction type (80% deposits, 20% withdrawals)
                trans_type = 'Nạp' if random.random() < 0.8 else 'Rút'
                
                # Generate realistic amounts
                if trans_type == 'Nạp':
                    # Deposits: 10M to 500M VND
                    amount = random.randint(10_000_000, 500_000_000)
                    new_nav = current_nav + amount
                else:
                    # Withdrawals: 5M to 100M VND
                    amount = random.randint(5_000_000, 100_000_000)
                    new_nav = max(current_nav - amount, current_nav * 0.8)  # Don't withdraw more than 20%
                
                # NEW: Realistic growth with caps
                growth_factor = random.uniform(1.001, 1.005)  # 0.1% to 0.5% per transaction
                new_nav *= growth_factor
                
                # Add NAV cap to prevent extreme values
                MAX_NAV = 50_000_000_000  # 50 billion VND max
                if new_nav > MAX_NAV:
                    new_nav = MAX_NAV * random.uniform(0.95, 1.0)
                # Process transaction
                try:
                    if trans_type == 'Nạp':
                        success, _ = self.fund_manager.process_deposit(
                            investor.id, amount, new_nav, trans_date
                        )
                    else:
                        success, _ = self.fund_manager.process_withdrawal(
                            investor.id, amount, new_nav, trans_date
                        )
                    
                    if success:
                        current_nav = new_nav
                        
                except Exception as e:
                    self.validation_errors.append(f"Transaction failed: {str(e)}")
        
        # Add NAV updates throughout the period
        nav_update_count = config.get('nav_updates', 20)
        for i in range(nav_update_count):
            random_days = random.randint(0, (end_date - start_date).days)
            update_date = start_date + timedelta(days=random_days)
            
            # Random NAV movement (-5% to +10%)
            change_factor = random.uniform(0.95, 1.10)
            current_nav *= change_factor
            
            try:
                self.fund_manager.process_nav_update(current_nav, update_date)
            except Exception as e:
                self.validation_errors.append(f"NAV update failed: {str(e)}")
        
        print(f"✅ Generated transactions and NAV updates")
    
    def _apply_multiple_fee_periods(self, periods: int):
        """Apply fees for multiple periods"""
        base_year = 2023
        
        for period in range(periods):
            year = base_year + period
            fee_date = date(year, 12, 31)
            
            # Get current NAV
            latest_nav = self.fund_manager.get_latest_total_nav()
            if not latest_nav:
                continue
            
            # NEW: Realistic year-end growth
            year_end_growth = random.uniform(1.0, 1.05)  # 0% to 5% max per year
            fee_nav = min(latest_nav * year_end_growth, 50_000_000_000)  # Cap at 50B
            
            try:
                success, message = self.fund_manager.apply_year_end_fees_enhanced(
                    year, fee_date, fee_nav
                )
                
                if not success:
                    self.validation_errors.append(f"Fee application failed for {year}: {message}")
                else:
                    print(f"✅ Applied fees for year {year}")
                    
            except Exception as e:
                self.validation_errors.append(f"Fee application error for {year}: {str(e)}")
    
    def _generate_post_fee_transactions(self, investors: List):
        """Generate more transactions after fee applications"""
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 6, 30)
        
        current_nav = self.fund_manager.get_latest_total_nav() or 1_000_000_000
        
        # Generate some post-fee transactions
        for investor in investors[:len(investors)//2]:  # Only half of investors
            # Random transaction
            trans_date = start_date + timedelta(
                days=random.randint(0, (end_date - start_date).days)
            )
            
            amount = random.randint(20_000_000, 200_000_000)
            new_nav = current_nav * random.uniform(1.01, 1.05) + amount
            
            try:
                success, _ = self.fund_manager.process_deposit(
                    investor.id, amount, new_nav, trans_date
                )
                if success:
                    current_nav = new_nav
            except Exception as e:
                self.validation_errors.append(f"Post-fee transaction failed: {str(e)}")
        
        print(f"✅ Generated post-fee transactions")
    
    def _comprehensive_validation(self) -> Dict[str, Any]:
        """Comprehensive validation of all calculations"""
        validation_results = {
            'data_consistency': True,
            'balance_consistency': True,
            'fee_calculation': True,
            'unit_price_consistency': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 1. Basic data consistency
            consistency_check = self.fund_manager.validate_data_consistency()
            if not consistency_check['valid']:
                validation_results['data_consistency'] = False
                validation_results['errors'].extend(consistency_check['errors'])
            validation_results['warnings'].extend(consistency_check.get('warnings', []))
            
            # 2. Balance consistency check
            latest_nav = self.fund_manager.get_latest_total_nav()
            if latest_nav:
                total_units = sum(t.units for t in self.fund_manager.tranches)
                if total_units > 0:
                    calculated_price = latest_nav / total_units
                    
                    # Check each investor's balance
                    total_calculated_balance = 0
                    for investor in self.fund_manager.investors:
                        if investor.is_fund_manager:
                            continue
                        
                        balance, _, _ = self.fund_manager.get_investor_balance(investor.id, latest_nav)
                        total_calculated_balance += balance
                    
                    # Add fund manager balance
                    fm = self.fund_manager.get_fund_manager()
                    if fm:
                        fm_balance, _, _ = self.fund_manager.get_investor_balance(fm.id, latest_nav)
                        total_calculated_balance += fm_balance
                    
                    # Check if total balances match NAV (within 1% tolerance)
                    balance_diff_pct = abs(total_calculated_balance - latest_nav) / latest_nav
                    if balance_diff_pct > 0.01:
                        validation_results['balance_consistency'] = False
                        validation_results['errors'].append(
                            f"Balance mismatch: Total calculated {total_calculated_balance:,.0f} vs NAV {latest_nav:,.0f} ({balance_diff_pct*100:.2f}% diff)"
                        )
            
            # 3. Fee calculation validation
            for investor in self.fund_manager.get_regular_investors():
                try:
                    fee_details = self.fund_manager.calculate_investor_fee(
                        investor.id, datetime.now(), latest_nav or 1_000_000_000
                    )
                    
                    # Validate fee components
                    if fee_details['total_fee'] < 0:
                        validation_results['fee_calculation'] = False
                        validation_results['errors'].append(f"Negative fee for {investor.name}")
                    
                    if fee_details['excess_profit'] < 0 and fee_details['total_fee'] > 0:
                        validation_results['fee_calculation'] = False
                        validation_results['errors'].append(f"Fee without excess profit for {investor.name}")
                    
                except Exception as e:
                    validation_results['fee_calculation'] = False
                    validation_results['errors'].append(f"Fee calculation error for {investor.name}: {str(e)}")
            
            # 4. Unit price consistency
            price_checks = []
            nav_transactions = [t for t in self.fund_manager.transactions if t.nav > 0]
            for trans in nav_transactions[-10:]:  # Check last 10 NAV transactions
                trans_units = sum(t.units for t in self.fund_manager.tranches 
                                if t.entry_date <= trans.date)
                if trans_units > 0:
                    calculated_price = trans.nav / trans_units
                    price_checks.append(calculated_price)
            
            if price_checks:
                # Check for unrealistic price jumps
                for i in range(1, len(price_checks)):
                    price_change = abs(price_checks[i] - price_checks[i-1]) / price_checks[i-1]
                    if price_change > 0.5:  # More than 50% price change
                        validation_results['warnings'].append(
                            f"Large price change detected: {price_change*100:.1f}%"
                        )
            
            # 5. Tranche-level validations
            for tranche in self.fund_manager.tranches:
                # HWM should not be less than entry NAV
                if tranche.hwm < tranche.entry_nav:
                    validation_results['warnings'].append(
                        f"HWM < Entry NAV for tranche {tranche.tranche_id[:8]}"
                    )
                
                # Units should be positive
                if tranche.units <= 0:
                    validation_results['errors'].append(
                        f"Non-positive units in tranche {tranche.tranche_id[:8]}"
                    )
                    validation_results['data_consistency'] = False
                
                # Cumulative fees should be non-negative
                if tranche.cumulative_fees_paid < 0:
                    validation_results['errors'].append(
                        f"Negative cumulative fees in tranche {tranche.tranche_id[:8]}"
                    )
            
        except Exception as e:
            validation_results['errors'].append(f"Validation process error: {str(e)}")
        
        # Overall validation status
        validation_results['overall_valid'] = (
            validation_results['data_consistency'] and
            validation_results['balance_consistency'] and
            validation_results['fee_calculation'] and
            len(validation_results['errors']) == 0
        )
        
        return validation_results
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze fund performance metrics"""
        performance = {}
        
        try:
            latest_nav = self.fund_manager.get_latest_total_nav()
            if not latest_nav:
                return {'error': 'No NAV data available'}
            
            # Portfolio composition
            regular_investors = self.fund_manager.get_regular_investors()
            portfolio_data = []
            
            total_original_invested = 0
            total_current_value = 0
            total_fees_paid = 0
            
            for investor in regular_investors:
                if not investor.name.startswith('Test_'):
                    continue
                
                lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor.id, latest_nav)
                balance, profit, profit_perc = self.fund_manager.get_investor_balance(investor.id, latest_nav)
                
                if lifetime_perf['original_invested'] > 0:
                    portfolio_data.append({
                        'name': investor.name,
                        'original_invested': lifetime_perf['original_invested'],
                        'current_value': balance,
                        'profit': profit,
                        'profit_perc': profit_perc,
                        'fees_paid': lifetime_perf['total_fees_paid'],
                        'gross_return': lifetime_perf['gross_return'],
                        'net_return': lifetime_perf['net_return']
                    })
                    
                    total_original_invested += lifetime_perf['original_invested']
                    total_current_value += balance
                    total_fees_paid += lifetime_perf['total_fees_paid']
            
            # Fund-level metrics
            if total_original_invested > 0:
                fund_gross_return = (total_current_value + total_fees_paid - total_original_invested) / total_original_invested
                fund_net_return = (total_current_value - total_original_invested) / total_original_invested
                fee_rate = total_fees_paid / total_original_invested
            else:
                fund_gross_return = fund_net_return = fee_rate = 0
            
            # Fund Manager analysis
            fund_manager = self.fund_manager.get_fund_manager()
            fm_analysis = {}
            if fund_manager:
                fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
                fm_units = sum(t.units for t in fm_tranches)
                fm_value = fm_units * self.fund_manager.calculate_price_per_unit(latest_nav)
                
                fm_analysis = {
                    'units': fm_units,
                    'value': fm_value,
                    'percentage_of_fund': (fm_value / latest_nav * 100) if latest_nav > 0 else 0
                }
            
            performance = {
                'fund_metrics': {
                    'total_nav': latest_nav,
                    'total_original_invested': total_original_invested,
                    'total_current_value': total_current_value,
                    'total_fees_collected': total_fees_paid,
                    'fund_gross_return': fund_gross_return,
                    'fund_net_return': fund_net_return,
                    'cumulative_fee_rate': fee_rate,
                    'price_per_unit': self.fund_manager.calculate_price_per_unit(latest_nav)
                },
                'investor_performance': portfolio_data,
                'fund_manager': fm_analysis,
                'portfolio_stats': {
                    'num_investors': len(portfolio_data),
                    'avg_gross_return': sum(p['gross_return'] for p in portfolio_data) / len(portfolio_data) if portfolio_data else 0,
                    'avg_net_return': sum(p['net_return'] for p in portfolio_data) / len(portfolio_data) if portfolio_data else 0,
                    'max_gross_return': max((p['gross_return'] for p in portfolio_data), default=0),
                    'min_gross_return': min((p['gross_return'] for p in portfolio_data), default=0),
                    'total_profit': sum(p['profit'] for p in portfolio_data),
                    'profitable_investors': len([p for p in portfolio_data if p['profit'] > 0])
                }
            }
            
        except Exception as e:
            performance['error'] = f"Performance analysis failed: {str(e)}"
        
        return performance
    
    def _get_data_statistics(self) -> Dict[str, Any]:
        """Get comprehensive data statistics"""
        try:
            stats = {
                'investors': {
                    'total': len(self.fund_manager.investors),
                    'regular': len(self.fund_manager.get_regular_investors()),
                    'fund_manager': 1 if self.fund_manager.get_fund_manager() else 0,
                    'test_investors': len([inv for inv in self.fund_manager.investors if inv.name.startswith('Test_')])
                },
                'tranches': {
                    'total': len(self.fund_manager.tranches),
                    'total_units': sum(t.units for t in self.fund_manager.tranches),
                    'avg_units_per_tranche': sum(t.units for t in self.fund_manager.tranches) / len(self.fund_manager.tranches) if self.fund_manager.tranches else 0
                },
                'transactions': {
                    'total': len(self.fund_manager.transactions),
                    'deposits': len([t for t in self.fund_manager.transactions if t.type == 'Nạp']),
                    'withdrawals': len([t for t in self.fund_manager.transactions if t.type == 'Rút']),
                    'nav_updates': len([t for t in self.fund_manager.transactions if t.type == 'NAV Update']),
                    'fees': len([t for t in self.fund_manager.transactions if 'Phí' in t.type])
                },
                'fee_records': {
                    'total': len(self.fund_manager.fee_records),
                    'periods': len(set(f.period for f in self.fund_manager.fee_records)),
                    'total_fees': sum(f.fee_amount for f in self.fund_manager.fee_records)
                }
            }
            
            # Latest NAV info
            latest_nav = self.fund_manager.get_latest_total_nav()
            if latest_nav:
                stats['nav'] = {
                    'latest_nav': latest_nav,
                    'price_per_unit': self.fund_manager.calculate_price_per_unit(latest_nav)
                }
            
            return stats
            
        except Exception as e:
            return {'error': f"Statistics calculation failed: {str(e)}"}
    
    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        if not self.test_results:
            return "❌ No test results available. Run test first."
        
        results = self.test_results
        
        report = []
        report.append("=" * 80)
        report.append("🧪 FUND MANAGEMENT SYSTEM - STRESS TEST REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Test Summary
        report.append(f"📋 TEST SUMMARY")
        report.append("-" * 40)
        report.append(f"Scenario: {results['scenario'].upper()}")
        report.append(f"Status: {'✅ PASSED' if results['success'] else '❌ FAILED'}")
        report.append(f"Duration: {results['duration_seconds']:.2f} seconds")
        report.append("")
        
        # Configuration
        if 'config' in results:
            config = results['config']
            report.append(f"⚙️ TEST CONFIGURATION")
            report.append("-" * 40)
            report.append(f"Investors: {config['investors']}")
            report.append(f"Transactions per investor: {config['transactions_per_investor']}")
            report.append(f"Fee periods: {config['fee_periods']}")
            report.append(f"NAV updates: {config['nav_updates']}")
            report.append("")
        
        # Data Statistics
        if 'data_stats' in results:
            stats = results['data_stats']
            report.append(f"📊 DATA STATISTICS")
            report.append("-" * 40)
            
            if 'investors' in stats:
                inv_stats = stats['investors']
                report.append(f"Investors - Total: {inv_stats['total']}, Test: {inv_stats['test_investors']}")
            
            if 'tranches' in stats:
                tr_stats = stats['tranches']
                report.append(f"Tranches - Total: {tr_stats['total']}, Units: {tr_stats['total_units']:,.2f}")
            
            if 'transactions' in stats:
                tx_stats = stats['transactions']
                report.append(f"Transactions - Total: {tx_stats['total']}, Deposits: {tx_stats['deposits']}, Withdrawals: {tx_stats['withdrawals']}")
            
            if 'fee_records' in stats:
                fee_stats = stats['fee_records']
                report.append(f"Fee Records - Total: {fee_stats['total']}, Periods: {fee_stats['periods']}")
            
            if 'nav' in stats:
                nav_stats = stats['nav']
                report.append(f"Latest NAV: {nav_stats['latest_nav']:,.0f} VND")
                report.append(f"Price per Unit: {nav_stats['price_per_unit']:,.0f} VND")
            
            report.append("")
        
        # Validation Results
        if 'validation' in results:
            validation = results['validation']
            report.append(f"🔍 VALIDATION RESULTS")
            report.append("-" * 40)
            report.append(f"Overall Valid: {'✅ YES' if validation.get('overall_valid', False) else '❌ NO'}")
            report.append(f"Data Consistency: {'✅' if validation.get('data_consistency', False) else '❌'}")
            report.append(f"Balance Consistency: {'✅' if validation.get('balance_consistency', False) else '❌'}")
            report.append(f"Fee Calculation: {'✅' if validation.get('fee_calculation', False) else '❌'}")
            
            if validation.get('errors'):
                report.append(f"\n❌ ERRORS ({len(validation['errors'])}):")
                for error in validation['errors'][:10]:  # Show first 10 errors
                    report.append(f"  • {error}")
                if len(validation['errors']) > 10:
                    report.append(f"  ... and {len(validation['errors']) - 10} more errors")
            
            if validation.get('warnings'):
                report.append(f"\n⚠️ WARNINGS ({len(validation['warnings'])}):")
                for warning in validation['warnings'][:5]:  # Show first 5 warnings
                    report.append(f"  • {warning}")
                if len(validation['warnings']) > 5:
                    report.append(f"  ... and {len(validation['warnings']) - 5} more warnings")
            
            report.append("")
        
        # Performance Analysis
        if 'performance' in results and 'fund_metrics' in results['performance']:
            perf = results['performance']
            fund_metrics = perf['fund_metrics']
            
            report.append(f"📈 PERFORMANCE ANALYSIS")
            report.append("-" * 40)
            report.append(f"Total NAV: {fund_metrics['total_nav']:,.0f} VND")
            report.append(f"Total Original Investment: {fund_metrics['total_original_invested']:,.0f} VND")
            report.append(f"Total Current Value: {fund_metrics['total_current_value']:,.0f} VND")
            report.append(f"Total Fees Collected: {fund_metrics['total_fees_collected']:,.0f} VND")
            report.append(f"Fund Gross Return: {fund_metrics['fund_gross_return']*100:.2f}%")
            report.append(f"Fund Net Return: {fund_metrics['fund_net_return']*100:.2f}%")
            report.append(f"Cumulative Fee Rate: {fund_metrics['cumulative_fee_rate']*100:.2f}%")
            
            if 'portfolio_stats' in perf:
                portfolio = perf['portfolio_stats']
                report.append(f"\nPortfolio Statistics:")
                report.append(f"  Active Investors: {portfolio['num_investors']}")
                report.append(f"  Profitable Investors: {portfolio['profitable_investors']}")
                report.append(f"  Average Gross Return: {portfolio['avg_gross_return']*100:.2f}%")
                report.append(f"  Average Net Return: {portfolio['avg_net_return']*100:.2f}%")
                report.append(f"  Total Profit: {portfolio['total_profit']:,.0f} VND")
            
            report.append("")
        
        # Conclusion
        report.append(f"🎯 CONCLUSION")
        report.append("-" * 40)
        if results['success']:
            report.append("✅ The fund management system passed all stress tests!")
            report.append("✅ All calculations appear to be working correctly.")
            report.append("✅ Data consistency is maintained under heavy load.")
        else:
            report.append("❌ The system failed stress testing.")
            report.append("❌ Issues were found that need to be addressed.")
            report.append("❌ Review the errors above and fix before production use.")
        
        report.append("")
        report.append("=" * 80)
        report.append(f"Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def export_test_results_to_excel(self) -> bytes:
        """Export detailed test results to Excel"""
        import io
        import pandas as pd
        
        buffer = io.BytesIO()
        
        try:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Test Summary
                if self.test_results:
                    summary_data = {
                        'Metric': ['Scenario', 'Success', 'Duration (seconds)', 'Total Investors', 'Total Transactions'],
                        'Value': [
                            self.test_results.get('scenario', 'Unknown'),
                            'PASSED' if self.test_results.get('success', False) else 'FAILED',
                            self.test_results.get('duration_seconds', 0),
                            self.test_results.get('data_stats', {}).get('investors', {}).get('total', 0),
                            self.test_results.get('data_stats', {}).get('transactions', {}).get('total', 0)
                        ]
                    }
                    
                    df_summary = pd.DataFrame(summary_data)
                    df_summary.to_excel(writer, sheet_name='Test Summary', index=False)
                
                # Performance Data
                if 'performance' in self.test_results and 'investor_performance' in self.test_results['performance']:
                    perf_data = self.test_results['performance']['investor_performance']
                    if perf_data:
                        df_performance = pd.DataFrame(perf_data)
                        df_performance.to_excel(writer, sheet_name='Investor Performance', index=False)
                
                # Current Data State
                current_investors = []
                for investor in self.fund_manager.get_regular_investors():
                    if investor.name.startswith('Test_'):
                        current_investors.append({
                            'ID': investor.id,
                            'Name': investor.name,
                            'Phone': investor.phone,
                            'Email': investor.email
                        })
                
                if current_investors:
                    df_investors = pd.DataFrame(current_investors)
                    df_investors.to_excel(writer, sheet_name='Test Investors', index=False)
                
                # Validation Results
                if 'validation' in self.test_results:
                    validation = self.test_results['validation']
                    validation_data = {
                        'Check': ['Data Consistency', 'Balance Consistency', 'Fee Calculation', 'Overall Valid'],
                        'Status': [
                            'PASS' if validation.get('data_consistency', False) else 'FAIL',
                            'PASS' if validation.get('balance_consistency', False) else 'FAIL',
                            'PASS' if validation.get('fee_calculation', False) else 'FAIL',
                            'PASS' if validation.get('overall_valid', False) else 'FAIL'
                        ]
                    }
                    
                    df_validation = pd.DataFrame(validation_data)
                    df_validation.to_excel(writer, sheet_name='Validation Results', index=False)
            
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            print(f"❌ Excel export failed: {str(e)}")
            return b''


def run_stress_test_cli():
    """Command line interface for stress testing"""
    import sys
    import os
    
    # Add current directory to path
    sys.path.append(os.path.dirname(__file__))
    
    try:
        # Import your fund manager
        from services_enhanced import EnhancedFundManager
        from supabase_data_handler import SupabaseDataHandler
        
        print("🚀 Initializing Fund Management System...")
        
        # Initialize
        data_handler = SupabaseDataHandler()
        fund_manager = EnhancedFundManager(data_handler)
        
        # Create tester
        tester = FundStressTester(fund_manager)
        
        # Run test
        scenario = input("Enter test scenario (light/medium/heavy/extreme) [medium]: ").strip().lower()
        if not scenario:
            scenario = 'medium'
        
        if scenario not in tester.scenarios:
            print(f"❌ Invalid scenario. Available: {list(tester.scenarios.keys())}")
            return
        
        # Run the test
        results = tester.run_comprehensive_test(scenario)
        
        # Generate report
        report = tester.generate_test_report()
        print("\n" + report)
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"stress_test_report_{scenario}_{timestamp}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Report saved to: {report_filename}")
        
        # Export Excel if requested
        export_excel = input("\nExport detailed results to Excel? (y/n) [n]: ").strip().lower()
        if export_excel == 'y':
            excel_data = tester.export_test_results_to_excel()
            if excel_data:
                excel_filename = f"stress_test_results_{scenario}_{timestamp}.xlsx"
                with open(excel_filename, 'wb') as f:
                    f.write(excel_data)
                print(f"📊 Excel report saved to: {excel_filename}")
        
    except Exception as e:
        print(f"❌ Stress test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_stress_test_cli()