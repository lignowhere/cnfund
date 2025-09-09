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
    # Valid parameters for st.altair_chart (Streamlit 1.49.1)
    valid_params = {
        'use_container_width': kwargs.get('use_container_width', True),
        'theme': kwargs.get('theme', 'streamlit'),
        'key': kwargs.get('key'),
        'on_select': kwargs.get('on_select', 'ignore'),
        'selection_mode': kwargs.get('selection_mode')
    }
    
    # Remove None values and invalid parameters
    filtered_params = {k: v for k, v in valid_params.items() if v is not None}
    
    # Remove any invalid parameters that might have been passed
    if 'width' in kwargs:
        print(f"⚠️ WARNING: Removed invalid 'width' parameter from altair_chart call")
    
    try:
        st.altair_chart(chart, **filtered_params)
    except Exception as e:
        st.error(f"❌ Chart rendering failed: {str(e)}")
        print(f"Chart error details: {str(e)}")

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
        st.error(f"❌ Chart rendering failed: {str(e)}")
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

# Alias functions for backward compatibility
def render_altair_chart(chart: alt.Chart, **kwargs) -> None:
    """Alias for safe_altair_chart"""
    safe_altair_chart(chart, **kwargs)

def render_plotly_chart(figure: go.Figure, **kwargs) -> None:
    """Alias for safe_plotly_chart"""
    safe_plotly_chart(figure, **kwargs)