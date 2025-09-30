#!/usr/bin/env python3
"""
Error tracking utilities to catch 'str' object cannot be interpreted as an integer errors
"""

import functools
import traceback
import streamlit as st
from typing import Any, Callable

def track_integer_conversion_errors(func: Callable) -> Callable:
    """
    Decorator to track and log integer conversion errors
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TypeError as e:
            if "'str' object cannot be interpreted as an integer" in str(e):
                error_details = {
                    'function': func.__name__,
                    'args_types': [type(arg).__name__ for arg in args],
                    'kwargs_types': {k: type(v).__name__ for k, v in kwargs.items()},
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
                
                print(f"🚨 INTEGER CONVERSION ERROR CAUGHT!")
                print(f"Function: {error_details['function']}")
                print(f"Args types: {error_details['args_types']}")
                print(f"Kwargs types: {error_details['kwargs_types']}")
                print(f"Error: {error_details['error']}")
                print(f"Traceback:\n{error_details['traceback']}")
                
                # Also show in Streamlit if available
                try:
                    st.error(f"🚨 Integer conversion error in {func.__name__}: {str(e)}")
                    with st.expander("Error Details"):
                        st.code(error_details['traceback'])
                except:
                    pass  # Streamlit not available
                
                raise e
            else:
                raise e
        except Exception as e:
            # Re-raise other exceptions unchanged
            raise e
    
    return wrapper


def safe_integer_operation(operation_name: str, operation_func: Callable, *args, **kwargs) -> Any:
    """
    Safely execute an operation that might involve integer conversion
    """
    try:
        return operation_func(*args, **kwargs)
    except TypeError as e:
        if "'str' object cannot be interpreted as an integer" in str(e):
            print(f"🚨 INTEGER CONVERSION ERROR in {operation_name}!")
            print(f"Args: {[type(arg).__name__ + ':' + repr(arg) for arg in args]}")
            print(f"Kwargs: {[(k, type(v).__name__ + ':' + repr(v)) for k, v in kwargs.items()]}")
            
            # Try to identify which argument is the problematic string
            for i, arg in enumerate(args):
                if isinstance(arg, str) and arg.isdigit():
                    print(f"  Potential fix: Convert arg {i} '{arg}' (str) to int")
            
            for k, v in kwargs.items():
                if isinstance(v, str) and v.isdigit():
                    print(f"  Potential fix: Convert kwarg '{k}' '{v}' (str) to int")
            
            # Show in Streamlit if available
            try:
                st.error(f"🚨 Integer conversion error in {operation_name}")
                st.write("**Arguments causing error:**")
                for i, arg in enumerate(args):
                    if isinstance(arg, str):
                        st.write(f"  - Arg {i}: '{arg}' (type: string)")
            except:
                pass
                
            raise e
        else:
            raise e


# Monkey patch common functions that might cause integer errors
original_range = range
def safe_range(*args, **kwargs):
    """Safe version of range() that converts string arguments"""
    converted_args = []
    for arg in args:
        if isinstance(arg, str) and arg.isdigit():
            print(f"⚠️ Converting string '{arg}' to int in range()")
            converted_args.append(int(arg))
        else:
            converted_args.append(arg)
    
    return safe_integer_operation("range", original_range, *converted_args, **kwargs)


# Apply monkey patches
range = safe_range

# Note: Cannot monkey patch built-in immutable types like list
# Instead, we provide safe wrapper functions for problematic operations
def safe_list_access(lst, index):
    """Safe list access with automatic type conversion"""
    try:
        # If index is string that looks like a number, convert it
        if isinstance(index, str) and index.isdigit():
            print(f"⚠️ Converting string '{index}' to int in list access")
            index = int(index)
        return lst[index]
    except Exception as e:
        print(f"🚨 List access error: {e}")
        print(f"  List length: {len(lst)}, Index: {repr(index)} (type: {type(index).__name__})")
        raise e


def log_data_types(data_dict: dict, context: str):
    """
    Log all data types in a dictionary for debugging
    """
    print(f"\n🔍 DATA TYPES DEBUG - {context}:")
    for key, value in data_dict.items():
        print(f"  {key}: {type(value).__name__} = {repr(value)[:50]}")
    print()


def validate_integer_fields(obj: Any, field_names: list) -> dict:
    """
    Validate that specified fields of an object are integers
    """
    results = {}
    for field_name in field_names:
        try:
            value = getattr(obj, field_name)
            if not isinstance(value, int):
                results[field_name] = {
                    'valid': False,
                    'current_type': type(value).__name__,
                    'current_value': repr(value),
                    'message': f"Field '{field_name}' should be int but is {type(value).__name__}"
                }
            else:
                results[field_name] = {'valid': True}
        except AttributeError:
            results[field_name] = {
                'valid': False,
                'message': f"Field '{field_name}' does not exist"
            }
    
    return results