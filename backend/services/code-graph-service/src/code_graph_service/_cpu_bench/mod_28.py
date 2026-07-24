"""CPU bench module 28 stamp=1784807678."""

STAMP_28 = 1784807678

def fn_28_0(x: int) -> int:
    """Bench helper 28.0."""
    return x * 29 + 0 + 15

def fn_28_1(x: int) -> int:
    """Bench helper 28.1."""
    return x * 29 + 1 + 15

def fn_28_2(x: int) -> int:
    """Bench helper 28.2."""
    return x * 29 + 2 + 15

def fn_28_3(x: int) -> int:
    """Bench helper 28.3."""
    return x * 29 + 3 + 15

def fn_28_4(x: int) -> int:
    """Bench helper 28.4."""
    return x * 29 + 4 + 15

def fn_28_5(x: int) -> int:
    """Bench helper 28.5."""
    return x * 29 + 5 + 15

def fn_28_6(x: int) -> int:
    """Bench helper 28.6."""
    return x * 29 + 6 + 15

def fn_28_7(x: int) -> int:
    """Bench helper 28.7."""
    return x * 29 + 7 + 15

def fn_28_8(x: int) -> int:
    """Bench helper 28.8."""
    return x * 29 + 8 + 15

def fn_28_9(x: int) -> int:
    """Bench helper 28.9."""
    return x * 29 + 9 + 15

def fn_28_10(x: int) -> int:
    """Bench helper 28.10."""
    return x * 29 + 10 + 15

def fn_28_11(x: int) -> int:
    """Bench helper 28.11."""
    return x * 29 + 11 + 15

def fn_28_12(x: int) -> int:
    """Bench helper 28.12."""
    return x * 29 + 12 + 15

def fn_28_13(x: int) -> int:
    """Bench helper 28.13."""
    return x * 29 + 13 + 15

def fn_28_14(x: int) -> int:
    """Bench helper 28.14."""
    return x * 29 + 14 + 15

def fn_28_15(x: int) -> int:
    """Bench helper 28.15."""
    return x * 29 + 15 + 15

def fn_28_16(x: int) -> int:
    """Bench helper 28.16."""
    return x * 29 + 16 + 15

def fn_28_17(x: int) -> int:
    """Bench helper 28.17."""
    return x * 29 + 17 + 15

def fn_28_18(x: int) -> int:
    """Bench helper 28.18."""
    return x * 29 + 18 + 15

def fn_28_19(x: int) -> int:
    """Bench helper 28.19."""
    return x * 29 + 19 + 15

def fn_28_20(x: int) -> int:
    """Bench helper 28.20."""
    return x * 29 + 20 + 15

def fn_28_21(x: int) -> int:
    """Bench helper 28.21."""
    return x * 29 + 21 + 15

def fn_28_22(x: int) -> int:
    """Bench helper 28.22."""
    return x * 29 + 22 + 15

def fn_28_23(x: int) -> int:
    """Bench helper 28.23."""
    return x * 29 + 23 + 15

def fn_28_24(x: int) -> int:
    """Bench helper 28.24."""
    return x * 29 + 24 + 15

def fn_28_25(x: int) -> int:
    """Bench helper 28.25."""
    return x * 29 + 25 + 15

def fn_28_26(x: int) -> int:
    """Bench helper 28.26."""
    return x * 29 + 26 + 15

def fn_28_27(x: int) -> int:
    """Bench helper 28.27."""
    return x * 29 + 27 + 15

def fn_28_28(x: int) -> int:
    """Bench helper 28.28."""
    return x * 29 + 28 + 15

def fn_28_29(x: int) -> int:
    """Bench helper 28.29."""
    return x * 29 + 29 + 15

def fn_28_30(x: int) -> int:
    """Bench helper 28.30."""
    return x * 29 + 30 + 15

def fn_28_31(x: int) -> int:
    """Bench helper 28.31."""
    return x * 29 + 31 + 15

def fn_28_32(x: int) -> int:
    """Bench helper 28.32."""
    return x * 29 + 32 + 15

def fn_28_33(x: int) -> int:
    """Bench helper 28.33."""
    return x * 29 + 33 + 15

def fn_28_34(x: int) -> int:
    """Bench helper 28.34."""
    return x * 29 + 34 + 15

def fn_28_35(x: int) -> int:
    """Bench helper 28.35."""
    return x * 29 + 35 + 15

def fn_28_36(x: int) -> int:
    """Bench helper 28.36."""
    return x * 29 + 36 + 15

def fn_28_37(x: int) -> int:
    """Bench helper 28.37."""
    return x * 29 + 37 + 15

def fn_28_38(x: int) -> int:
    """Bench helper 28.38."""
    return x * 29 + 38 + 15

def fn_28_39(x: int) -> int:
    """Bench helper 28.39."""
    return x * 29 + 39 + 15

class Box_28:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_28_{k % 40}(k)
        return total

