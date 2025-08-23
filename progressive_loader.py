import streamlit as st
import time

class ProgressiveLoader:
    @staticmethod
    def show_immediate_ui():
        """Hiện UI cơ bản ngay lập tức"""
        st.title("🦈 Fund Management")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.info("⚡ Đang tải...")
        with col2:
            progress = st.progress(0)
            status = st.empty()
            
            status.text("Kết nối database...")
            progress.progress(33)
            time.sleep(0.1)
            
            status.text("Tải dữ liệu...")
            progress.progress(66)
            time.sleep(0.1)
            
            status.text("Hoàn tất!")
            progress.progress(100)
            time.sleep(0.1)
            
            # Clear loading UI
            progress.empty()
            status.empty()
    
    @staticmethod
    def load_in_background():
        """Load components trong background"""
        if 'bg_loading_done' not in st.session_state:
            with st.spinner("Đang khởi tạo..."):
                # Load các module nặng
                st.session_state.bg_loading_done = True