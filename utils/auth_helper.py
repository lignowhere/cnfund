#!/usr/bin/env python3
"""
Authentication Helper for Admin Operations
Provides unified authentication for sensitive operations like backup, restore, etc.
"""

import streamlit as st
import time

def check_admin_authentication():
    """
    Authentication removed - local system doesn't need password protection
    Always returns True for local operations
    """
    # Local system - no authentication required
    st.session_state.logged_in = True
    return True

def show_admin_status():
    """
    Show local system status - no authentication needed
    """
    st.success("🏠 Local System - Full Access Enabled")

def is_admin_authenticated():
    """
    Local system - always authenticated (without UI)
    """
    return True