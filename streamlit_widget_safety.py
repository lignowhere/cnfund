#!/usr/bin/env python3
"""
Streamlit widget safety utilities to handle browser vs headless mode differences
"""

import streamlit as st
from typing import Any, Dict, Optional
from type_safety_fixes import safe_int_conversion


def safe_selectbox_int_value(options_dict: Dict[str, int], selected_display: str) -> Optional[int]:
    """
    Safely get integer value from selectbox selection
    
    Args:
        options_dict: Dictionary mapping display names to integer values
        selected_display: The display name selected in selectbox
        
    Returns:
        Optional[int]: The integer value, or None if invalid
    """
    if not selected_display or selected_display not in options_dict:
        return None
    
    # Get the value from options dict
    raw_value = options_dict[selected_display]
    
    # In browser mode, even though we store integers in the dict,
    # Streamlit might convert them to strings during serialization
    try:
        return safe_int_conversion(raw_value)
    except Exception as e:
        st.error(f"⚠️ Selectbox value conversion error: {e}")
        st.write(f"Debug: selected_display={repr(selected_display)}, raw_value={repr(raw_value)}")
        return None


def safe_investor_id_from_selectbox(fund_manager, selected_display: str) -> Optional[int]:
    """
    Safely get investor ID from selectbox selection with comprehensive error handling
    
    Args:
        fund_manager: The fund manager instance
        selected_display: The display name selected in selectbox
        
    Returns:
        Optional[int]: The investor ID as integer, or None if invalid
    """
    try:
        # Get options with type safety
        options = fund_manager.get_investor_options()
        
        if not selected_display or selected_display not in options:
            return None
        
        # Get the investor ID
        investor_id = safe_selectbox_int_value(options, selected_display)
        
        if investor_id is None or investor_id < 0:
            st.error(f"❌ Invalid investor ID from selectbox: {repr(investor_id)}")
            return None
            
        return investor_id
        
    except Exception as e:
        st.error(f"🚨 Error getting investor ID from selectbox: {e}")
        st.write("**Debug Information:**")
        st.write(f"  - selected_display: {repr(selected_display)} (type: {type(selected_display).__name__})")
        try:
            options = fund_manager.get_investor_options()
            st.write(f"  - options available: {list(options.keys())[:3]}...")  # Show first 3
            if selected_display in options:
                st.write(f"  - raw value from options: {repr(options[selected_display])} (type: {type(options[selected_display]).__name__})")
        except Exception as debug_e:
            st.write(f"  - Debug error: {debug_e}")
        return None


def validate_session_state_integers():
    """
    Validate and fix integer values in Streamlit session state
    """
    if not hasattr(st, 'session_state'):
        return
    
    # List of session state keys that should be integers
    integer_keys = [
        'selected_investor_id',
        'current_investor_id',
        'investor_id',
        'selected_id'
    ]
    
    for key in integer_keys:
        if key in st.session_state:
            try:
                # Convert to integer if it's not already
                original_value = st.session_state[key]
                converted_value = safe_int_conversion(original_value)
                
                if original_value != converted_value:
                    st.session_state[key] = converted_value
                    print(f"🔧 Fixed session state {key}: {repr(original_value)} -> {repr(converted_value)}")
                    
            except Exception as e:
                print(f"⚠️ Could not fix session state {key}: {e}")


def debug_selectbox_behavior(options_dict: Dict[str, int], selected_display: str):
    """
    Debug selectbox behavior in browser vs headless mode
    """
    st.write("### 🔍 Selectbox Debug Information:")
    st.write(f"**Selected display:** {repr(selected_display)} (type: {type(selected_display).__name__})")
    
    if selected_display in options_dict:
        raw_value = options_dict[selected_display]
        st.write(f"**Raw value from dict:** {repr(raw_value)} (type: {type(raw_value).__name__})")
        
        converted_value = safe_int_conversion(raw_value)
        st.write(f"**Converted value:** {repr(converted_value)} (type: {type(converted_value).__name__})")
        
        # Test comparison operations
        try:
            test_result = converted_value == 1
            st.write(f"**Test comparison (== 1):** {test_result}")
        except Exception as e:
            st.error(f"**Comparison failed:** {e}")
    else:
        st.error(f"Selected display not found in options!")
        st.write(f"Available options: {list(options_dict.keys())}")


def apply_streamlit_widget_fixes():
    """
    Apply all Streamlit widget safety fixes
    """
    # Fix session state integers
    validate_session_state_integers()
    
    # Could add more fixes here in the future
    pass


if __name__ == "__main__":
    # Test the functions
    print("Testing Streamlit widget safety functions...")
    
    # Test safe conversion
    test_options = {"Test User (ID: 1)": 1, "Another User (ID: 2)": "2"}
    
    result1 = safe_selectbox_int_value(test_options, "Test User (ID: 1)")
    assert result1 == 1, f"Expected 1, got {result1}"
    
    result2 = safe_selectbox_int_value(test_options, "Another User (ID: 2)")  
    assert result2 == 2, f"Expected 2, got {result2}"
    
    print("✅ All Streamlit widget safety tests passed")