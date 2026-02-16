#!/usr/bin/env python3
"""
Chart Utilities - Safe chart rendering with parameter validation
Defensive wrapper to prevent chart parameter errors
"""

import streamlit as st
import altair as alt
import plotly.graph_objects as go
from typing import Any, Dict, Optional

def safe_altair_chart(chart: alt.Chart, **kwargs) -> None:
    """
    Safe wrapper for st.altair_chart that filters out invalid parameters
    
    Args:
        chart: Altair chart object
        **kwargs: Parameters to pass to st.altair_chart
    """
    # Simple parameter filtering - remove problematic parameters
    safe_params = {}
    
    # Only include known safe parameters
    if 'use_container_width' in kwargs:
        safe_params['use_container_width'] = kwargs['use_container_width']
    else:
        safe_params['use_container_width'] = True
        
    if 'theme' in kwargs:
        safe_params['theme'] = kwargs['theme']
        
    if 'key' in kwargs:
        safe_params['key'] = kwargs['key']
    
    # Warn about filtered parameters
    filtered_out = [k for k in kwargs.keys() if k not in safe_params and k not in ['use_container_width', 'theme', 'key']]
    if filtered_out:
        print(f"⚠️ WARNING: Filtered out chart parameters: {filtered_out}")
    
    try:
        st.altair_chart(chart, **safe_params)
    except Exception as e:
        print(f"Chart error: {str(e)}")
        # Simple fallback
        try:
            st.altair_chart(chart, use_container_width=True)
        except Exception as e2:
            print(f"Fallback chart error: {str(e2)}")
            st.error("❌ Không thể hiển thị biểu đồ")

def safe_plotly_chart(figure: go.Figure, **kwargs) -> None:
    """
    Safe wrapper for st.plotly_chart that validates parameters
    
    Args:
        figure: Plotly figure object
        **kwargs: Parameters to pass to st.plotly_chart
    """
    # Valid parameters for st.plotly_chart
    valid_params = {
        'use_container_width': kwargs.get('use_container_width', True),
        'theme': kwargs.get('theme', 'streamlit'),
        'key': kwargs.get('key'),
        'on_select': kwargs.get('on_select', 'ignore'),
        'selection_mode': kwargs.get('selection_mode', ('points', 'box', 'lasso'))
    }
    
    # Remove None values
    filtered_params = {k: v for k, v in valid_params.items() if v is not None}
    
    # st.plotly_chart accepts **kwargs, but let's be defensive
    if 'width' in kwargs:
        print(f"⚠️ WARNING: 'width' parameter passed to plotly_chart")
    
    try:
        st.plotly_chart(figure, **filtered_params)
    except Exception as e:
        st.error(f"❌ Hiển thị biểu đồ thất bại: {str(e)}")
        print(f"Chart error details: {str(e)}")

def validate_chart_environment() -> Dict[str, Any]:
    """
    Validate the chart rendering environment and return diagnostics
    
    Returns:
        Dictionary with environment information
    """
    import altair as alt
    import plotly
    
    diagnostics = {
        'streamlit_version': st.__version__,
        'altair_version': alt.__version__,
        'plotly_version': plotly.__version__,
        'chart_compatibility': True
    }
    
    try:
        # Test basic chart creation
        test_data = {'x': [1, 2, 3], 'y': [1, 4, 2]}
        test_chart = alt.Chart(test_data).mark_bar()
        diagnostics['altair_creation'] = True
    except Exception as e:
        diagnostics['altair_creation'] = False
        diagnostics['altair_error'] = str(e)
    
    try:
        # Test basic plotly creation
        import pandas as pd
        test_fig = go.Figure()
        diagnostics['plotly_creation'] = True
    except Exception as e:
        diagnostics['plotly_creation'] = False
        diagnostics['plotly_error'] = str(e)
    
    return diagnostics

def initialize_chart_environment() -> None:
    """
    Initialize chart environment and clear any problematic state
    Call this at the start of pages that use charts
    """
    # Clear chart-related session state
    if hasattr(st, 'session_state'):
        chart_keys_to_clear = []
        for key in st.session_state.keys():
            if any(term in key.lower() for term in ['chart', 'vega', 'altair']) and 'width' in str(st.session_state[key]).lower():
                chart_keys_to_clear.append(key)
        
        for key in chart_keys_to_clear:
            try:
                del st.session_state[key]
                print(f"Cleared potentially problematic session state: {key}")
            except KeyError:
                pass
    
    # Set safe chart defaults
    if not hasattr(st, '_chart_defaults_set'):
        st._chart_defaults_set = True
        print("Chart environment initialized with safe defaults")

# Alias functions for backward compatibility
def render_altair_chart(chart: alt.Chart, **kwargs) -> None:
    """Alias for safe_altair_chart"""
    safe_altair_chart(chart, **kwargs)

def render_plotly_chart(figure: go.Figure, **kwargs) -> None:
    """Alias for safe_plotly_chart"""
    safe_plotly_chart(figure, **kwargs)
