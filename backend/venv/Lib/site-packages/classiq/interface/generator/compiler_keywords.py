EXPANDED_KEYWORD = "expanded__"
CAPTURE_SUFFIX = "_captured__"
LAMBDA_KEYWORD = "lambda__"
INPLACE_ARITH_AUX_VAR_PREFIX = "_tmp"
THEN_KEYWORD = "then"
ELSE_KEYWORD = "else"


def generate_original_function_name(name: str) -> str:
    return name.split(f"_{LAMBDA_KEYWORD}")[0].split(f"_{EXPANDED_KEYWORD}")[0]
