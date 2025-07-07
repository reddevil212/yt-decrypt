import ctypes
from typing import Optional, Tuple
from sig import extract_tce_func, extract_decipher_func, extract_n_transform_func

def extract_decode_script(input_str: str) -> Tuple[bool, str]:
    """
    Python equivalent of the C FFI function extract_decode_script.
    Returns (success: bool, result_or_error: str)
    """
    
    def return_error(msg: str) -> Tuple[bool, str]:
        """Helper function to return error consistently"""
        return False, msg
    
    if input_str is None:
        return return_error("Input string is null")
    
    if not isinstance(input_str, str):
        return return_error("Invalid Input string")
    
    body = input_str
    
    try:
        # Extract TCE function
        etf = extract_tce_func(body)
        name = etf.name
        code = etf.code
    except (ValueError, Exception) as e:
        return return_error(str(e))
    
    try:
        # Extract decipher script
        decipher_script = extract_decipher_func(body, code)
    except (ValueError, Exception) as e:
        return return_error(str(e))
    
    try:
        # Extract n-transform script
        n_transform_script = extract_n_transform_func(body, name, code)
    except (ValueError, Exception) as e:
        return return_error(str(e))
    
    # Combine results
    result = decipher_script + n_transform_script
    
    return True, result

# Optional: Create a C-compatible wrapper using ctypes if needed
class ExtractDecodeScriptWrapper:
    """
    Wrapper class that provides C-compatible interface for the extract_decode_script function.
    This can be used to create a shared library that matches the original C interface.
    """
    
    @staticmethod
    def create_c_string(s: str) -> ctypes.c_char_p:
        """Create C string from Python string"""
        return ctypes.c_char_p(s.encode('utf-8'))
    
    @staticmethod
    def extract_decode_script_c_compat(input_ptr: ctypes.c_char_p) -> Tuple[bool, ctypes.c_char_p]:
        """
        C-compatible version that works with ctypes pointers
        """
        if not input_ptr:
            return False, ExtractDecodeScriptWrapper.create_c_string("Input string is null")
        
        try:
            input_str = input_ptr.decode('utf-8')
        except UnicodeDecodeError:
            return False, ExtractDecodeScriptWrapper.create_c_string("Invalid Input string")
        
        success, result = extract_decode_script(input_str)
        return success, ExtractDecodeScriptWrapper.create_c_string(result)

# For direct usage without C compatibility
def extract_decode_script_simple(javascript_code: str) -> str:
    """
    Simplified version that just returns the result or raises an exception
    """
    success, result = extract_decode_script(javascript_code)
    if not success:
        raise ValueError(result)
    return result

# Example usage
if __name__ == "__main__":
    # Example usage of the Python version
    sample_js = """
    // Sample JavaScript code would go here
    // This is just a placeholder
    """
    
    try:
        success, result = extract_decode_script(sample_js)
        if success:
            print("Success:", result)
        else:
            print("Error:", result)
    except Exception as e:
        print("Exception:", str(e))