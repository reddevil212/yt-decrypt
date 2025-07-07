import re
from typing import Tuple, Union, NamedTuple
from dataclasses import dataclass

# Type alias for Result
Result = Union[str, Exception]

# Constants - equivalent to Rust constants
VARIABLE_PART = r"[a-zA-Z_\$][a-zA-Z_0-9\$]*"
VARIABLE_PART_DEFINE = rf'\"?{VARIABLE_PART}\"?'
BEFORE_ACCESS = r"(?:\[\"|\\.)"
AFTER_ACCESS = r"(?:\"\]|)"
VARIABLE_PART_ACCESS = rf"{BEFORE_ACCESS}{VARIABLE_PART}{AFTER_ACCESS}"
REVERSE_PART = r":function\(\w\)\{(?:return )?\w\.reverse\(\)\}"
SLICE_PART = r":function\(\w,\w\)\{return \w\.slice\(\w\)\}"
SPLICE_PART = r":function\(\w,\w\)\{\w\.splice\(0,\w\)\}"
SWAP_PART = (
    r":function\(\w,\w\)\{"
    r"var \w=\w\[0\];\w\[0\]=\w\[\w%\w\.length\];\w\[\w(?:%\w\.length|)\]=\w(?:;return \w)?\}"
)

DECIPHER_REGEXP = (
    rf"function(?: {VARIABLE_PART})?\(([a-zA-Z])\)\{{"
    rf"\1=\1\.split\(\"\"\);\s*"
    rf"((?:(?:\1=)?{VARIABLE_PART}{VARIABLE_PART_ACCESS}\(\1,\d+\);)+)"
    rf"return \1\.join\(\"\"\)"
    rf"\}}"
)

HELPER_REGEXP = (
    rf"var ({VARIABLE_PART})=\{{((?:(?:{VARIABLE_PART_DEFINE}{REVERSE_PART}|"
    rf"{VARIABLE_PART_DEFINE}{SLICE_PART}|{VARIABLE_PART_DEFINE}{SPLICE_PART}|"
    rf"{VARIABLE_PART_DEFINE}{SWAP_PART}),?\n?)+)\}};"
)

FUNCTION_TCE_REGEXP = (
    r"function(?:\s+[a-zA-Z_\$][a-zA-Z0-9_\$]*)?\(\w\)\{"
    r"\w=\w\.split\((?:\"\"|[a-zA-Z0-9_$]*\[\d+\])\);"
    r"\s*((?:(?:\w=)?[a-zA-Z_\$][a-zA-Z0-9_\$]*(?:\[\"|\\.)[a-zA-Z_\$][a-zA-Z0-9_\$]*(?:\"\]|)\(\w,\d+\);)+)"
    r"return \w\.join\((?:\"\"|[a-zA-Z0-9_$]*\[\d+\])\)}"
)

N_TRANSFORM_REGEXP = (
    r"function\(\s*(\w+)\s*\)\s*\{"
    r"var\s*(\w+)=(?:\1\.split\(.*?\)|String\.prototype\.split\.call\(\1,.*?\)),"
    r"\s*(\w+)=(\[.*?\]);\s*\3\[\d+\]"
    r"(.*?try)(\{.*?\})catch\(\s*(\w+)\s*\)\s*\{"
    r"\s*return\"[\w-]+([A-z0-9-]+)\"\s*\+\s*\1\s*}"
    r"\s*return\s*(\2\.join\(\"\")|Array\.prototype\.join\.call\(\2,.*?\))};"
)

N_TRANSFORM_TCE_REGEXP = (
    r"function\(\s*(\w+)\s*\)\s*\{"
    r"\s*var\s*(\w+)=\1\.split\(\1\.slice\(0,0\)\),\s*(\w+)=\[.*?\];"
    r".*?catch\(\s*(\w+)\s*\)\s*\{"
    r"\s*return(?:\"[^\"]+\"|\s*[a-zA-Z_0-9$]*\[\d+\])\s*\+\s*\1\s*}"
    r"\s*return\s*\2\.join\((?:\"\"|[a-zA-Z_0-9$]*\[\d+\])\)};"
)

TCE_GLOBAL_VARS_REGEXP = (
    r"(?:^|[;,])\s*(var\s+([\w$]+)\s*=\s*"
    r"(?:([\"'])(?:\\.|[^\\])*?\3\s*\.\s*split\(([\"'])(?:\\.|[^\\])*?\5\)"
    r"|\[\s*(?:([\"'])(?:\\.|[^\\])*?\6\s*,?\s*)+\]))(?=\s*[,;])"
)

NEW_TCE_GLOBAL_VARS_REGEXP = (
    r"('use\s*strict';)?"
    r"(?P<code>var\s*"
    r"(?P<varname>[a-zA-Z0-9_$]+)\s*=\s*"
    r"(?P<value>"
    r"(?:\"[^\"\\]*(?:\\.[^\"\\]*)*\"|'[^'\\]*(?:\\.[^'\\]*)*')"
    r"\.split\("
    r"(?:\"[^\"\\]*(?:\\.[^\"\\]*)*\"|'[^'\\]*(?:\\.[^'\\]*)*')"
    r"\)"
    r"|\["
    r"(?:(?:\"[^\"\\]*(?:\\.[^\"\\]*)*\"|'[^'\\]*(?:\\.[^'\\]*)*')\s*,?\s*)*"
    r"\]"
    r"|\"[^\"]*\"\.split\(\"[^\"]*\"\)"
    r")"
    r")"
)

TCE_SIGN_FUNCTION_REGEXP = (
    r"function\(\s*([a-zA-Z0-9$])\s*\)\s*\{"
    r"\s*\1\s*=\s*\1\[(\w+)\[\d+\]\]\(\2\[\d+\]\);"
    r"([a-zA-Z0-9$]+)\[\2\[\d+\]\]\(\s*\1\s*,\s*\d+\s*\);"
    r"\s*\3\[\2\[\d+\]\]\(\s*\1\s*,\s*\d+\s*\);"
    r".*?return\s*\1\[\2\[\d+\]\]\(\2\[\d+\]\)};"
)

TCE_SIGN_FUNCTION_ACTION_REGEXP = (
    r"var\s+([$A-Za-z0-9_]+)\s*=\s*\{\s*[$A-Za-z0-9_]+\s*:\s*function\s*\([^)]*\)\s*\{[^{}]*(?:\{[^{}]*}[^{}]*)*}\s*,\s*"
    r"[$A-Za-z0-9_]+\s*:\s*function\s*\([^)]*\)\s*\{[^{}]*(?:\{[^{}]*}[^{}]*)*}\s*,\s*"
    r"[$A-Za-z0-9_]+\s*:\s*function\s*\([^)]*\)\s*\{[^{}]*(?:\{[^{}]*}[^{}]*)*}\s*};"
)

TCE_N_FUNCTION_REGEXP = (
    r"function\s*\((\w+)\)\s*\{var\s*\w+\s*=\s*\1\[\w+\[\d+\]\]\(\w+\[\d+\]\)\s*,\s*\w+\s*=\s*\[.*?\]\;"
    r".*?catch\s*\(\s*(\w+)\s*\)\s*\{return\s*\w+\[\d+\]\s*\+\s*\1\}\s*return\s*\w+\[\w+\[\d+\]\]\(\w+\[\d+\]\)\}\s*\;"
)

PATTERN_PREFIX = rf"(?:^|,)\"?({VARIABLE_PART})\"?"
REVERSE_PATTERN = rf"(?m){PATTERN_PREFIX}{REVERSE_PART}"
SLICE_PATTERN = rf"(?m){PATTERN_PREFIX}{SLICE_PART}"
SPLICE_PATTERN = rf"(?m){PATTERN_PREFIX}{SPLICE_PART}"
SWAP_PATTERN = rf"(?m){PATTERN_PREFIX}{SWAP_PART}"

FOR_PARAM_MATCHING = r"function\s*\(\s*(\w+)\s*\)"

DECIPHER_FUNC_NAME = "DisTubeDecipherFunc"
N_TRANSFORM_FUNC_NAME = "DisTubeNTransformFunc"

@dataclass
class ExtractTceFunc:
    name: str
    code: str

def build_regex(pattern: str, flags: int = 0) -> re.Pattern:
    """Build regex pattern with error handling"""
    try:
        return re.compile(pattern, flags)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {pattern}") from e

def extract_tce_func(body: str) -> ExtractTceFunc:
    """Extract TCE function from JavaScript body"""
    tce_variable_matcher = build_regex(NEW_TCE_GLOBAL_VARS_REGEXP, re.MULTILINE)
    match = tce_variable_matcher.search(body)
    
    if not match:
        raise ValueError(f"No captures found for input using regex 'NEW_TCE_GLOBAL_VARS_REGEXP'")
    
    code = match.group('code')
    varname = match.group('varname')
    
    if not code:
        raise ValueError(f"No capture group named 'code' found using regex 'NEW_TCE_GLOBAL_VARS_REGEXP'")
    if not varname:
        raise ValueError(f"No capture group named 'varname' found using regex 'NEW_TCE_GLOBAL_VARS_REGEXP'")
    
    return ExtractTceFunc(name=varname, code=code)

def extract_decipher_func(body: str, code: str) -> str:
    """Extract decipher function from JavaScript body"""
    sig_function_matcher = build_regex(TCE_SIGN_FUNCTION_REGEXP, re.DOTALL)
    sig_function_match = sig_function_matcher.search(body)
    
    sig_function_actions_matcher = build_regex(TCE_SIGN_FUNCTION_ACTION_REGEXP, re.DOTALL)
    sig_function_actions_match = sig_function_actions_matcher.search(body)
    
    if sig_function_match and sig_function_actions_match:
        return (
            f"var {DECIPHER_FUNC_NAME}={sig_function_match.group(0)}"
            f"{sig_function_actions_match.group(0)}{code};"
        )
    
    helper_matcher = build_regex(HELPER_REGEXP, re.DOTALL)
    helper_match = helper_matcher.search(body)
    
    if not helper_match:
        raise ValueError(f"No captures found for input using regex 'HELPER_REGEXP'")
    
    helper_object = helper_match.group(0)
    
    if not helper_object:
        raise ValueError(f"No first capture group found using regex 'HELPER_REGEXP'")
    
    # Validate action body
    action_body = helper_match.group(2)
    if not action_body:
        raise ValueError(f"No third capture group found using regex 'HELPER_REGEXP'")
    
    pattern_regexes = [
        build_regex(REVERSE_PATTERN),
        build_regex(SLICE_PATTERN),
        build_regex(SPLICE_PATTERN),
        build_regex(SWAP_PATTERN)
    ]
    
    if not any(pattern.search(action_body) for pattern in pattern_regexes):
        raise ValueError(f"No captures found for input using regex 'PATTERN_REGEX_SET'")
    
    func_matcher = build_regex(DECIPHER_REGEXP, re.DOTALL)
    func_match = func_matcher.search(body)
    
    if func_match:
        decipher_func = func_match.group(0)
        is_tce = False
    else:
        tce_func_matcher = build_regex(FUNCTION_TCE_REGEXP, re.DOTALL)
        tce_func_match = tce_func_matcher.search(body)
        
        if not tce_func_match:
            raise ValueError(f"No captures found for input using regex 'FUNCTION_TCE_REGEXP'")
        
        decipher_func = tce_func_match.group(0)
        is_tce = True
    
    tce_vars = ""
    if is_tce:
        tce_vars_matcher = build_regex(TCE_GLOBAL_VARS_REGEXP, re.MULTILINE)
        tce_vars_match = tce_vars_matcher.search(body)
        
        if tce_vars_match:
            tce_vars = tce_vars_match.group(1)
            if not tce_vars:
                raise ValueError(f"No second capture group found using regex 'TCE_GLOBAL_VARS_REGEXP'")
    
    return f"{tce_vars};{helper_object}\nvar {DECIPHER_FUNC_NAME}={decipher_func};"

def extract_n_transform_func(body: str, name: str, code: str) -> str:
    """Extract n-transform function from JavaScript body"""
    n_function_matcher = build_regex(TCE_N_FUNCTION_REGEXP, re.DOTALL)
    n_function_match = n_function_matcher.search(body)
    
    if n_function_match:
        n_function = n_function_match.group(0)
        
        if not n_function:
            raise ValueError(f"No first capture group found using regex 'TCE_N_FUNCTION_REGEXP'")
        
        # Handle short circuit pattern
        tce_escape_name = re.escape(name)
        short_circuit_pattern = build_regex(
            rf";\s*if\s*\(\s*typeof\s+[a-zA-Z0-9_$]+\s*===?\s*(?:\"undefined\"|'undefined'|{tce_escape_name}\[\d+\])\s*\)\s*return\s+\w+;"
        )
        
        short_circuit_match = short_circuit_pattern.search(n_function)
        if short_circuit_match:
            n_function = n_function.replace(short_circuit_match.group(0), ";")
        
        return f"var {N_TRANSFORM_FUNC_NAME}={n_function}{code};"
    
    n_matcher = build_regex(N_TRANSFORM_REGEXP, re.DOTALL)
    n_match = n_matcher.search(body)
    
    if n_match:
        n_function = n_match.group(0)
        is_tce = False
    else:
        n_tce_matcher = build_regex(N_TRANSFORM_TCE_REGEXP, re.DOTALL)
        n_tce_match = n_tce_matcher.search(body)
        
        if not n_tce_match:
            raise ValueError(f"No captures found for input using regex 'N_TRANSFORM_TCE_REGEXP'")
        
        n_function = n_tce_match.group(0)
        if not n_function:
            raise ValueError(f"No first capture group found using regex 'N_TRANSFORM_TCE_REGEXP'")
        
        is_tce = True
    
    param_matcher = build_regex(FOR_PARAM_MATCHING)
    param_match = param_matcher.search(n_function)
    
    if not param_match:
        raise ValueError(f"No captures found for input using regex 'FOR_PARAM_MATCHING'")
    
    param_name = param_match.group(1)
    if not param_name:
        raise ValueError(f"No second capture group found using regex 'FOR_PARAM_MATCHING'")
    
    # Clean function
    cleaned_function_pattern = build_regex(
        rf"if\s*\(typeof\s*[^\s()]+\s*===?.*?\)return {re.escape(param_name)}\s*;?"
    )
    cleaned_function = cleaned_function_pattern.sub("", n_function)
    
    tce_vars = ""
    if is_tce:
        tce_vars_matcher = build_regex(TCE_GLOBAL_VARS_REGEXP, re.MULTILINE)
        tce_vars_match = tce_vars_matcher.search(body)
        
        if tce_vars_match:
            tce_vars = tce_vars_match.group(1)
            if not tce_vars:
                raise ValueError(f"No second capture group found using regex 'TCE_GLOBAL_VARS_REGEXP'")
    
    return f"{tce_vars};var {N_TRANSFORM_FUNC_NAME}={cleaned_function};"