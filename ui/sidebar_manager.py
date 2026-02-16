# sidebar_manager.py - Clean Optimized Sidebar Manager

import streamlit as st
from datetime import datetime
from pathlib import Path
import time

# Auto backup integration
try:
    from integrations.auto_backup_personal import get_auto_backup_manager, manual_backup
    AUTO_BACKUP_AVAILABLE = True
except ImportError:
    AUTO_BACKUP_AVAILABLE = False

class SidebarManager:
    """Professional sidebar manager with clean architecture"""

    def __init__(self, fund_manager, data_handler, menu_options: list):
        self.fund_manager = fund_manager
        self.data_handler = data_handler
        self.menu_options = menu_options
        self._cache = {}

    def _get_nav_data(self):
        """Get NAV data - NO CACHE (always fresh)"""
        try:
            latest_nav = self.fund_manager.get_latest_total_nav()
            fund_manager = self.fund_manager.get_fund_manager()

            fm_info = None
            if fund_manager and latest_nav and latest_nav > 0:
                fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
                if fm_tranches:
                    fm_units = sum(t.units for t in fm_tranches)
                    fm_value = fm_units * self.fund_manager.calculate_price_per_unit(latest_nav)
                    fm_info = {'units': fm_units, 'value': fm_value}

            return {'nav': latest_nav, 'fm_info': fm_info}
        except Exception:
            return {'nav': None, 'fm_info': None}

    def _get_stats_data(self):
        """Get statistics data - NO CACHE (always fresh)"""
        try:
            regular_investors = self.fund_manager.get_regular_investors()
            active_tranches = [t for t in self.fund_manager.tranches if t.units > 0]
            fee_records_count = len(self.fund_manager.fee_records)

            return {
                'investors': len(regular_investors),
                'tranches': len(active_tranches),
                'fees': fee_records_count
            }
        except Exception:
            return {'investors': 0, 'tranches': 0, 'fees': 0}

    def _format_currency(self, value, compact=False):
        """Format currency with error handling"""
        # Direct formatting (data_utils removed during cleanup)
        if value is None:
            return "N/A"
        if compact and value >= 1_000_000_000:
            return f"{value/1_000_000_000:.1f}B"
        elif compact and value >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif compact and value >= 1_000:
            return f"{value/1_000:.1f}K"
        else:
            return f"{value:,.0f}"

    def render_header(self):
        """Render tiêu đề với responsive design"""
        st.sidebar.markdown(
            '<div class="sidebar-section">🦈 QUẢN LÝ QUỸ</div>',
            unsafe_allow_html=True
        )

    def render_nav_card(self):
        """Render card NAV với thông tin Fund Manager - học hỏi layout từ code gốc"""
        nav_data = self._get_nav_data()
        nav_value = nav_data['nav']
        fm_info = nav_data['fm_info']
        
        nav_display = self._format_currency(nav_value) if nav_value else "Đang tải..."
        fm_info_html = ""

        # Thông tin Fund Manager (nếu có) - theo style code gốc
        if fm_info:
            fm_value_display = self._format_currency(fm_info['value'], compact=True)
            fm_value_display = fm_value_display.replace("đ", "")
            # Tạo chuỗi HTML trên MỘT DÒNG DUY NHẤT để tránh lỗi parsing
            fm_info_html = f'<div class="fm-info">FM: {fm_info["units"]:,.1f} units ({fm_value_display})</div>'

        # Card NAV với design responsive - học hỏi structure từ code gốc
        html_content = f"""
            <div class="nav-card">
                <div class="nav-title">TỔNG NAV</div>
                <div class="nav-value">{nav_display}</div>
                {fm_info_html}
            </div>
        """
        st.sidebar.markdown(html_content, unsafe_allow_html=True)

    def render_stats_grid(self):
        """Render lưới thống kê nhanh - học hỏi content từ code gốc"""
        stats = self._get_stats_data()
        
        # Stats data theo style code gốc - NĐT, Giao dịch, Kỳ phí
        stats_data = [
            (stats['investors'], "NĐT", "#0066cc"),
            (len(self.fund_manager.tranches), "Giao dịch", "#28a745"),
            (stats['fees'], "Kỳ phí", "#ffc107")
        ]
        
        stats_items = ""
        for value, label, color in stats_data:
            stats_items += f"""
            <div class="stat-item">
                <div class="stat-value" style="color: {color};">{value}</div>
                <div class="stat-label">{label}</div>
            </div>"""

        html_content = f'<div class="stats-grid">{stats_items}</div>'
        st.sidebar.markdown(html_content, unsafe_allow_html=True)

    def render_navigation_menu(self):
        """Render menu điều hướng - theo style code gốc"""
        st.sidebar.markdown('<div class="sidebar-section">MENU CHÍNH</div>', unsafe_allow_html=True)

        # Đặt giá trị mặc định cho key của radio button nếu chưa tồn tại
        if 'menu_selection' not in st.session_state:
            st.session_state.menu_selection = self.menu_options[0]

        # Tạo radio button và gán cho nó một key duy nhất
        # Streamlit sẽ tự động cập nhật st.session_state.menu_selection khi người dùng nhấp chuột
        current_selection = st.sidebar.radio(
            "Chức năng",
            self.menu_options,
            # Index được xác định bởi giá trị hiện tại của key trong session_state
            index=self.menu_options.index(st.session_state.menu_selection),
            key="menu_selection", # Đây là phần quan trọng nhất
            label_visibility="collapsed"
        )
        
        # Trả về giá trị đã được đồng bộ hóa từ session_state
        # Đây là "nguồn chân lý duy nhất" cho trang hiện tại
        return current_selection

    def render_user_status(self):
        """Render trạng thái người dùng - theo style code gốc"""
        if st.session_state.get('logged_in', False):
            st.sidebar.success("👤 Chế độ quản trị")
            if st.sidebar.button("🚪 Đăng xuất", width="stretch"):
                st.session_state.logged_in = False
                st.rerun()
        else:
            st.sidebar.warning("🔒 Chế độ chỉ xem")

    def render_action_buttons(self):
        """Render các nút thao tác nhanh - theo style code gốc"""
        st.sidebar.markdown('<div class="sidebar-section">Thao tác nhanh</div>', unsafe_allow_html=True)

        col1, col2 = st.sidebar.columns(2)

        if col1.button("📊 Xuất Excel", use_container_width=True,
                      help="Xuất báo cáo tổng hợp ra file Excel"):
            self.handle_excel_export()

        if col2.button("☁️ Kiểm tra Drive", use_container_width=True,
                      help="Kiểm tra kết nối tới Google Drive"):
            self.handle_drive_test()

        # Reload data button (full width)
        if st.sidebar.button("🔄 Tải lại dữ liệu", use_container_width=True,
                            help="Tải lại dữ liệu mới nhất từ Google Drive"):
            self.handle_reload_data()

    def render_connection_status(self):
        """Render thông tin debug - theo style code gốc"""
        st.sidebar.markdown('<div class="sidebar-section">Thông tin hệ thống</div>', unsafe_allow_html=True)

        if self.data_handler and hasattr(self.data_handler, 'connected') and self.data_handler.connected:
            st.sidebar.success("🟢 Supabase đã kết nối")
        else:
            st.sidebar.error("🔴 Supabase mất kết nối")

        

    def render_footer(self):
        """Render thông tin cuối sidebar - theo style code gốc"""
        st.sidebar.markdown('<div class="sidebar-section">Thông tin</div>', unsafe_allow_html=True)
        
        # Last export info - theo code gốc
        export_dir = Path("exports")
        if export_dir.exists():
            excel_files = list(export_dir.glob("*.xlsx"))
            if excel_files:
                latest_file = max(excel_files, key=lambda p: p.stat().st_mtime)
                st.sidebar.caption(f"Lần xuất gần nhất: {datetime.fromtimestamp(latest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")

        # Version info - theo code gốc
        st.sidebar.caption("v3.1 - Kiến trúc gọn nhẹ")

    def show_last_export_info(self):
        """Show information about last export"""
        try:
            export_dir = Path("exports")
            if export_dir.exists():
                excel_files = list(export_dir.glob("*.xlsx"))
                if excel_files:
                    latest_file = max(excel_files, key=lambda p: p.stat().st_mtime)
                    export_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
                    st.sidebar.caption(f"📊 Lần xuất cuối: {export_time.strftime('%d/%m %H:%M')}")
        except Exception:
            pass  # Silently ignore if can't get export info

    def handle_excel_export(self):
        """Handle Excel export operation"""
        try:
            # Lazy import to avoid circular dependencies
            from integrations.google_drive_manager import GoogleDriveManager
            
            with st.spinner("📊 Đang xuất Excel..."):
                gdrive = GoogleDriveManager(self.fund_manager)
                success = gdrive.auto_export_and_upload(trigger="manual")
                
                if success:
                    st.balloons()
                    st.success("✅ Xuất Excel thành công!")
                    st.toast("📊 File đã được tải lên Google Drive", icon="☁️")
                else:
                    st.warning("⚠️ Xuất Excel thành công nhưng tải lên Drive thất bại")
                    
        except ImportError:
            st.error("❌ Chức năng Google Drive không khả dụng")
        except Exception as e:
            st.error(f"❌ Lỗi xuất Excel: {str(e)}")

    def handle_drive_test(self):
        """Handle Google Drive connection test"""
        try:
            from integrations.google_drive_manager import GoogleDriveManager

            with st.spinner("☁️ Kiểm tra Google Drive..."):
                gdrive = GoogleDriveManager(self.fund_manager)

                if gdrive.connected:
                    st.success("✅ Google Drive kết nối thành công!")
                    st.toast("☁️ Kết nối Drive thành công", icon="✅")
                else:
                    st.error("❌ Không thể kết nối Google Drive")
                    st.info("💡 Kiểm tra tệp thông tin xác thực (credentials.json)")

        except ImportError:
            st.error("❌ Trình quản lý Google Drive không khả dụng")
        except Exception as e:
            st.error(f"❌ Lỗi kết nối Drive: {str(e)}")

    def handle_reload_data(self):
        """Handle reload data from Google Drive - NO CACHE, always fresh"""
        try:
            with st.spinner("🔄 Đang tải lại dữ liệu từ Google Drive..."):
                # NO CACHE: Always load fresh data
                print("🔄 Reloading data (no cache)...")

                # Reload from Drive with retry
                import time
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        if attempt > 0:
                            print(f"   Retry {attempt}/{max_attempts-1}...")
                            time.sleep(2)

                        self.data_handler.load_from_drive()
                        self.fund_manager.load_data()
                        print(f"✅ Data reloaded (attempt {attempt+1})")
                        break
                    except Exception as e:
                        if attempt == max_attempts - 1:
                            raise e

                st.success("✅ Đã tải lại dữ liệu mới nhất!")
                st.toast("🔄 Đã tải lại dữ liệu thành công", icon="✅")

                # Rerun to refresh UI
                st.rerun()

        except Exception as e:
            st.error(f"❌ Lỗi tải lại dữ liệu: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def handle_data_refresh(self):
        """Handle data refresh operation"""
        try:
            with st.spinner("🔄 Đang làm mới dữ liệu..."):
                # Clear Streamlit caches
                if hasattr(st, 'cache_data'):
                    st.cache_data.clear()
                if hasattr(st, 'cache_resource'):
                    st.cache_resource.clear()
                
                # Clear method caches
                if hasattr(self._get_nav_data, 'clear'):
                    self._get_nav_data.clear()
                if hasattr(self._get_stats_data, 'clear'):
                    self._get_stats_data.clear()
                
                # Clear session state caches
                cache_keys_to_clear = [
                    key for key in st.session_state.keys() 
                    if any(word in key.lower() for word in ['cache', 'nav', 'balance'])
                ]
                for key in cache_keys_to_clear:
                    del st.session_state[key]
                
                # Reload fund manager data
                self.fund_manager.load_data()
                
                st.success("✅ Dữ liệu đã được làm mới!")
                st.toast("🔄 Đã làm mới dữ liệu thành công", icon="✅")
                
                # Small delay then rerun
                time.sleep(0.5)
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Lỗi làm mới dữ liệu: {str(e)}")


    
    def render(self) -> str:
        """Render toàn bộ sidebar và trả về trang được chọn - theo flow code gốc"""
        # Nút này giờ là một phần của sidebar, sẽ ẩn/hiện cùng với sidebar
        
        
        self.render_header()
        
        # Thứ tự render theo code gốc
        self.render_nav_card()           # NAV display
        self.render_stats_grid()         # Quick stats 
        selected_page = self.render_navigation_menu()  # MENU
        self.render_user_status()        # Viewer/Admin status
        self.render_action_buttons()     # Thao tác nhanh
        self.render_auto_backup_section(self.fund_manager)  # Auto backup system
        
        return selected_page

    def render_mobile_header(self):
        """Optional mobile header for main content area"""
        # Check if we're in mobile viewport (this is approximate)
        st.markdown("""
            <script>
            if (window.innerWidth <= 768) {
                document.body.classList.add('mobile-viewport');
            }
            </script>
            
            <div class="mobile-header" style="
                display: none;
                position: sticky;
                top: 0;
                background: white;
                border-bottom: 1px solid #e9ecef;
                padding: 1rem;
                text-align: center;
                font-weight: 600;
                color: #2c3e50;
                z-index: 100;
            ">
                🦈 QUẢN LÝ QUỸ
            </div>
            
            <style>
            @media (max-width: 768px) {
                .mobile-header {
                    display: block !important;
                }
            }
            </style>
        """, unsafe_allow_html=True)

    def render_auto_backup_section(self, fund_manager):
        """Render auto backup section in sidebar"""
        if not AUTO_BACKUP_AVAILABLE:
            return
            
        with st.sidebar.expander("🚀 Hệ thống sao lưu tự động"):
            try:
                backup_manager = get_auto_backup_manager(fund_manager)
                status = backup_manager.get_backup_status()
                
                # Status indicators
                if status['service_running']:
                    st.success("✅ Dịch vụ đang chạy")
                else:
                    st.warning("⚠️ Dịch vụ đã dừng")
                
                # Last backup info
                if status['last_backup']:
                    from datetime import datetime
                    last_backup = datetime.fromisoformat(status['last_backup'])
                    st.info(f"⏰ Lần gần nhất: {last_backup.strftime('%m-%d %H:%M')}")
                else:
                    st.info("⏰ Chưa có bản sao lưu")
                
                # Backup counts
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Cục bộ", status['local_backups']['count'])
                with col2:
                    cloud_count = status['cloud_backup'].get('files', 0) if status['cloud_backup']['connected'] else 0
                    st.metric("Đám mây", cloud_count)
                
                # Manual backup button
                if st.button("📊 Sao lưu ngay", key="manual_backup_btn", help="Tạo bản sao lưu ngay"):
                    with st.spinner("Đang tạo bản sao lưu..."):
                        success = manual_backup(fund_manager, "sidebar_manual")
                    if success:
                        st.success("✅ Đã tạo bản sao lưu!")
                        st.rerun()
                    else:
                        st.error("❌ Tạo bản sao lưu thất bại")
                
                # Status details (collapsed)
                with st.expander("📊 Chi tiết"):
                    st.json({
                        "Hôm nay": f"{status['backups_today']}/5",
                        "Đám mây": "Đã kết nối" if status['cloud_backup']['connected'] else "Chưa kết nối",
                        "Phương thức": status['cloud_backup'].get('method', 'Không xác định'),
                        "Thống kê": {
                            "Tổng số": status['stats']['total_backups'],
                            "Thất bại": status['stats']['failed_backups']
                        }
                    })
                    
            except Exception as e:
                st.error(f"❌ Lỗi sao lưu tự động: {str(e)}")
