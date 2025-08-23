# performance_analyzer.py - Script phân tích chi tiết tốc độ load app

import streamlit as st
import time
import sys
import os
from pathlib import Path
import importlib
import tracemalloc
from datetime import datetime
import pandas as pd

# Try to import psutil, fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    st.warning("⚠️ psutil not installed. Memory analysis will be limited. Install with: pip install psutil")

class PerformanceAnalyzer:
    """Phân tích chi tiết performance của app"""
    
    def __init__(self):
        self.timings = {}
        self.start_time = time.time()
        self.memory_snapshots = []
        
        # Bắt đầu trace memory
        tracemalloc.start()
        
        # Log process info nếu có psutil
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process(os.getpid())
            self.initial_memory = self.process.memory_info()
        else:
            self.process = None
            self.initial_memory = None
        
        st.markdown("# 🔍 Performance Analysis Dashboard")
        st.markdown("---")
    
    def time_operation(self, name: str, func, *args, **kwargs):
        """Time một operation cụ thể"""
        start = time.time()
        
        if PSUTIL_AVAILABLE and self.process:
            memory_before = self.process.memory_info()
        else:
            memory_before = None
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end = time.time()
        
        if PSUTIL_AVAILABLE and self.process:
            memory_after = self.process.memory_info()
            memory_delta = (memory_after.rss - memory_before.rss) / 1024 / 1024
        else:
            memory_after = None
            memory_delta = 0
        
        self.timings[name] = {
            'duration': end - start,
            'start_time': start - self.start_time,
            'memory_before': memory_before.rss / 1024 / 1024 if memory_before else 0,
            'memory_after': memory_after.rss / 1024 / 1024 if memory_after else 0,
            'memory_delta': memory_delta,
            'success': success,
            'error': error
        }
        
        return result
    
    def analyze_imports(self):
        """Phân tích thời gian import các modules"""
        st.subheader("📦 Import Analysis")
        
        # Test các imports chính
        imports_to_test = [
            ('streamlit', 'import streamlit'),
            ('config', 'from config import PAGE_CONFIG'),
            ('supabase_data_handler', 'from supabase_data_handler import SupabaseDataHandler'),
            ('services_enhanced', 'from services_enhanced import EnhancedFundManager'),
            ('styles', 'from styles import apply_global_styles'),
            ('sidebar_manager', 'from sidebar_manager import SidebarManager'),
            ('data_utils', 'from data_utils import ErrorHandler'),
            ('pages.investor_page', 'from pages.investor_page import InvestorPage'),
            ('pages.transaction_page', 'from pages.transaction_page import EnhancedTransactionPage'),
            ('pages.fee_page_enhanced', 'from pages.fee_page_enhanced import SafeFeePage'),
            ('pages.report_page_enhanced', 'from pages.report_page_enhanced import EnhancedReportPage'),
        ]
        
        import_results = []
        
        for module_name, import_statement in imports_to_test:
            start = time.time()
            
            if PSUTIL_AVAILABLE and self.process:
                memory_before = self.process.memory_info().rss / 1024 / 1024
            else:
                memory_before = 0
            
            try:
                exec(import_statement)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
            
            duration = time.time() - start
            
            if PSUTIL_AVAILABLE and self.process:
                memory_after = self.process.memory_info().rss / 1024 / 1024
                memory_delta = memory_after - memory_before
            else:
                memory_delta = 0
            
            import_results.append({
                'Module': module_name,
                'Duration (s)': f"{duration:.3f}",
                'Memory (MB)': f"{memory_delta:+.1f}",
                'Status': '✅ Success' if success else '❌ Failed',
                'Error': error if error else '-'
            })
        
        # Hiển thị bảng kết quả
        df = pd.DataFrame(import_results)
        st.dataframe(df, use_container_width=True)
        
        # Tổng kết
        successful_results = [r for r in import_results if r['Status'] == '✅ Success']
        total_time = sum(float(r['Duration (s)']) for r in successful_results)
        total_memory = sum(abs(float(r['Memory (MB)'].replace('+', '').replace('-', ''))) for r in successful_results)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Import Time", f"{total_time:.3f}s")
        col2.metric("Total Memory Used", f"{total_memory:.1f}MB")
        col3.metric("Failed Imports", len([r for r in import_results if r['Status'] == '❌ Failed']))
    
    def analyze_database_connection(self):
        """Phân tích database connection"""
        st.subheader("🗄️ Database Connection Analysis")
        
        try:
            # Test connection
            start = time.time()
            from supabase_data_handler import SupabaseDataHandler
            
            connection_time = time.time() - start
            st.metric("Import Handler Time", f"{connection_time:.3f}s")
            
            # Test actual connection
            start = time.time()
            handler = SupabaseDataHandler()
            init_time = time.time() - start
            
            st.metric("Connection Init Time", f"{init_time:.3f}s")
            
            if handler.connected:
                st.success("✅ Database Connected Successfully")
                
                # Test data loading
                data_tests = [
                    ('Investors', handler.load_investors),
                    ('Tranches', handler.load_tranches),
                    ('Transactions', handler.load_transactions),
                    ('Fee Records', handler.load_fee_records)
                ]
                
                load_results = []
                for table_name, load_func in data_tests:
                    start = time.time()
                    try:
                        data = load_func()
                        duration = time.time() - start
                        count = len(data)
                        success = True
                        error = None
                    except Exception as e:
                        duration = time.time() - start
                        count = 0
                        success = False
                        error = str(e)
                    
                    load_results.append({
                        'Table': table_name,
                        'Duration (s)': f"{duration:.3f}",
                        'Records': count,
                        'Status': '✅' if success else '❌',
                        'Error': error if error else '-'
                    })
                
                df = pd.DataFrame(load_results)
                st.dataframe(df, use_container_width=True)
                
            else:
                st.error("❌ Database Connection Failed")
                
        except Exception as e:
            st.error(f"❌ Database Analysis Failed: {e}")
    
    def analyze_page_rendering(self):
        """Phân tích page rendering"""
        st.subheader("🎨 Page Rendering Analysis")
        
        # Test CSS loading
        start = time.time()
        try:
            from styles import apply_global_styles
            apply_global_styles()
            css_time = time.time() - start
            st.metric("CSS Load Time", f"{css_time:.3f}s")
            st.success("✅ CSS Loaded Successfully")
        except Exception as e:
            st.error(f"❌ CSS Load Failed: {e}")
        
        # Test component rendering
        rendering_tests = [
            ('Sidebar Manager', self._test_sidebar_manager),
            ('Page Components', self._test_page_components),
            ('Form Elements', self._test_form_elements)
        ]
        
        render_results = []
        for test_name, test_func in rendering_tests:
            start = time.time()
            try:
                test_func()
                duration = time.time() - start
                success = True
                error = None
            except Exception as e:
                duration = time.time() - start
                success = False
                error = str(e)
            
            render_results.append({
                'Component': test_name,
                'Duration (s)': f"{duration:.3f}",
                'Status': '✅' if success else '❌',
                'Error': error if error else '-'
            })
        
        df = pd.DataFrame(render_results)
        st.dataframe(df, use_container_width=True)
    
    def _test_sidebar_manager(self):
        """Test sidebar manager creation"""
        from sidebar_manager import SidebarManager
        from supabase_data_handler import SupabaseDataHandler
        from services_enhanced import EnhancedFundManager
        
        # Mock objects
        data_handler = SupabaseDataHandler()
        if data_handler.connected:
            fund_manager = EnhancedFundManager(data_handler)
            sidebar = SidebarManager(fund_manager, data_handler, ['Test'])
    
    def _test_page_components(self):
        """Test page component imports"""
        sys.path.append(str(Path(__file__).parent / "pages"))
        
        from pages.investor_page import InvestorPage
        from pages.transaction_page import EnhancedTransactionPage
        from pages.fee_page_enhanced import SafeFeePage
        from pages.report_page_enhanced import EnhancedReportPage
    
    def _test_form_elements(self):
        """Test basic form elements"""
        test_container = st.container()
        with test_container:
            st.text_input("Test Input", key="perf_test_input")
            st.selectbox("Test Select", ["Option 1"], key="perf_test_select")
            st.button("Test Button", key="perf_test_button")
        
        # Clear test elements
        test_container.empty()
    
    def analyze_memory_usage(self):
        """Phân tích memory usage"""
        st.subheader("💾 Memory Usage Analysis")
        
        if PSUTIL_AVAILABLE and self.process and self.initial_memory:
            current_memory = self.process.memory_info()
            memory_delta = (current_memory.rss - self.initial_memory.rss) / 1024 / 1024
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Initial Memory", f"{self.initial_memory.rss / 1024 / 1024:.1f}MB")
            col2.metric("Current Memory", f"{current_memory.rss / 1024 / 1024:.1f}MB")
            col3.metric("Memory Growth", f"{memory_delta:+.1f}MB")
        else:
            st.warning("⚠️ psutil not available - cannot show process memory info")
        
        # Top memory consumers từ tracemalloc
        try:
            current, peak = tracemalloc.get_traced_memory()
            st.metric("Traced Memory", f"{current / 1024 / 1024:.1f}MB")
            st.metric("Peak Memory", f"{peak / 1024 / 1024:.1f}MB")
            
            # Memory timeline
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            if top_stats:
                st.subheader("Top Memory Consumers")
                memory_data = []
                for index, stat in enumerate(top_stats[:10]):
                    try:
                        filename = str(stat.traceback.format()[-1]).split('/')[-1][:50]
                    except:
                        filename = "Unknown"
                    
                    memory_data.append({
                        'File': filename,
                        'Memory (MB)': f"{stat.size / 1024 / 1024:.2f}",
                        'Count': stat.count
                    })
                
                df = pd.DataFrame(memory_data)
                st.dataframe(df, use_container_width=True)
                
        except Exception as e:
            st.warning(f"Memory tracing error: {e}")
    
    def analyze_session_state(self):
        """Phân tích session state"""
        st.subheader("🔄 Session State Analysis")
        
        if st.session_state:
            session_data = []
            total_size = 0
            
            for key, value in st.session_state.items():
                try:
                    size = sys.getsizeof(value)
                    total_size += size
                    
                    session_data.append({
                        'Key': key,
                        'Type': type(value).__name__,
                        'Size (bytes)': size,
                        'Size (KB)': f"{size / 1024:.1f}"
                    })
                except:
                    session_data.append({
                        'Key': key,
                        'Type': type(value).__name__,
                        'Size (bytes)': 0,
                        'Size (KB)': "N/A"
                    })
            
            st.metric("Total Session State Size", f"{total_size / 1024:.1f} KB")
            
            df = pd.DataFrame(session_data)
            df = df.sort_values('Size (bytes)', ascending=False)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No session state data found")
    
    def generate_performance_report(self):
        """Tạo báo cáo tổng hợp"""
        st.subheader("📊 Performance Summary Report")
        
        total_time = time.time() - self.start_time
        
        # Tổng quan
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Analysis Time", f"{total_time:.2f}s")
        col2.metric("Number of Tests", len(self.timings))
        
        if PSUTIL_AVAILABLE and self.process:
            current_memory_mb = self.process.memory_info().rss / 1024 / 1024
            col3.metric("Current Memory", f"{current_memory_mb:.1f}MB")
        else:
            col3.metric("Current Memory", "N/A")
        
        # Recommendations
        st.subheader("💡 Performance Recommendations")
        
        recommendations = []
        
        if total_time > 5:
            recommendations.append("⚠️ Overall analysis took >5s - consider optimization")
        
        # Check memory usage
        if PSUTIL_AVAILABLE and self.process:
            current_memory = self.process.memory_info().rss / 1024 / 1024
            if current_memory > 200:
                recommendations.append(f"⚠️ High memory usage ({current_memory:.1f}MB) - check for memory leaks")
        
        # Check failed operations
        failed_ops = sum(1 for timing in self.timings.values() if not timing.get('success', True))
        if failed_ops > 0:
            recommendations.append(f"❌ {failed_ops} operations failed - check error logs")
        
        if not recommendations:
            recommendations.append("✅ No major performance issues detected")
        
        for rec in recommendations:
            st.write(rec)
    
    def run_full_analysis(self):
        """Chạy phân tích đầy đủ"""
        st.info("🔍 Bắt đầu phân tích performance...")
        
        # Tạo tabs cho các phần phân tích
        tabs = st.tabs([
            "📦 Imports", 
            "🗄️ Database", 
            "🎨 Rendering", 
            "💾 Memory", 
            "🔄 Session State", 
            "📊 Summary"
        ])
        
        with tabs[0]:
            self.analyze_imports()
        
        with tabs[1]:
            self.analyze_database_connection()
        
        with tabs[2]:
            self.analyze_page_rendering()
        
        with tabs[3]:
            self.analyze_memory_usage()
        
        with tabs[4]:
            self.analyze_session_state()
        
        with tabs[5]:
            self.generate_performance_report()

# === MAIN EXECUTION ===
if __name__ == "__main__":
    st.set_page_config(
        page_title="Performance Analyzer",
        page_icon="🔍",
        layout="wide"
    )
    
    analyzer = PerformanceAnalyzer()
    analyzer.run_full_analysis()
    
    st.markdown("---")
    st.caption("Performance Analyzer v1.0 - Fund Management System")