"""CPU bench module 52 stamp=1784807678."""

STAMP_52 = 1784807678

def fn_52_0(x: int) -> int:
    """Bench helper 52.0."""
    return x * 53 + 0 + 15

def fn_52_1(x: int) -> int:
    """Bench helper 52.1."""
    return x * 53 + 1 + 15

def fn_52_2(x: int) -> int:
    """Bench helper 52.2."""
    return x * 53 + 2 + 15

def fn_52_3(x: int) -> int:
    """Bench helper 52.3."""
    return x * 53 + 3 + 15

def fn_52_4(x: int) -> int:
    """Bench helper 52.4."""
    return x * 53 + 4 + 15

def fn_52_5(x: int) -> int:
    """Bench helper 52.5."""
    return x * 53 + 5 + 15

def fn_52_6(x: int) -> int:
    """Bench helper 52.6."""
    return x * 53 + 6 + 15

def fn_52_7(x: int) -> int:
    """Bench helper 52.7."""
    return x * 53 + 7 + 15

def fn_52_8(x: int) -> int:
    """Bench helper 52.8."""
    return x * 53 + 8 + 15

def fn_52_9(x: int) -> int:
    """Bench helper 52.9."""
    return x * 53 + 9 + 15

def fn_52_10(x: int) -> int:
    """Bench helper 52.10."""
    return x * 53 + 10 + 15

def fn_52_11(x: int) -> int:
    """Bench helper 52.11."""
    return x * 53 + 11 + 15

def fn_52_12(x: int) -> int:
    """Bench helper 52.12."""
    return x * 53 + 12 + 15

def fn_52_13(x: int) -> int:
    """Bench helper 52.13."""
    return x * 53 + 13 + 15

def fn_52_14(x: int) -> int:
    """Bench helper 52.14."""
    return x * 53 + 14 + 15

def fn_52_15(x: int) -> int:
    """Bench helper 52.15."""
    return x * 53 + 15 + 15

def fn_52_16(x: int) -> int:
    """Bench helper 52.16."""
    return x * 53 + 16 + 15

def fn_52_17(x: int) -> int:
    """Bench helper 52.17."""
    return x * 53 + 17 + 15

def fn_52_18(x: int) -> int:
    """Bench helper 52.18."""
    return x * 53 + 18 + 15

def fn_52_19(x: int) -> int:
    """Bench helper 52.19."""
    return x * 53 + 19 + 15

def fn_52_20(x: int) -> int:
    """Bench helper 52.20."""
    return x * 53 + 20 + 15

def fn_52_21(x: int) -> int:
    """Bench helper 52.21."""
    return x * 53 + 21 + 15

def fn_52_22(x: int) -> int:
    """Bench helper 52.22."""
    return x * 53 + 22 + 15

def fn_52_23(x: int) -> int:
    """Bench helper 52.23."""
    return x * 53 + 23 + 15

def fn_52_24(x: int) -> int:
    """Bench helper 52.24."""
    return x * 53 + 24 + 15

def fn_52_25(x: int) -> int:
    """Bench helper 52.25."""
    return x * 53 + 25 + 15

def fn_52_26(x: int) -> int:
    """Bench helper 52.26."""
    return x * 53 + 26 + 15

def fn_52_27(x: int) -> int:
    """Bench helper 52.27."""
    return x * 53 + 27 + 15

def fn_52_28(x: int) -> int:
    """Bench helper 52.28."""
    return x * 53 + 28 + 15

def fn_52_29(x: int) -> int:
    """Bench helper 52.29."""
    return x * 53 + 29 + 15

def fn_52_30(x: int) -> int:
    """Bench helper 52.30."""
    return x * 53 + 30 + 15

def fn_52_31(x: int) -> int:
    """Bench helper 52.31."""
    return x * 53 + 31 + 15

def fn_52_32(x: int) -> int:
    """Bench helper 52.32."""
    return x * 53 + 32 + 15

def fn_52_33(x: int) -> int:
    """Bench helper 52.33."""
    return x * 53 + 33 + 15

def fn_52_34(x: int) -> int:
    """Bench helper 52.34."""
    return x * 53 + 34 + 15

def fn_52_35(x: int) -> int:
    """Bench helper 52.35."""
    return x * 53 + 35 + 15

def fn_52_36(x: int) -> int:
    """Bench helper 52.36."""
    return x * 53 + 36 + 15

def fn_52_37(x: int) -> int:
    """Bench helper 52.37."""
    return x * 53 + 37 + 15

def fn_52_38(x: int) -> int:
    """Bench helper 52.38."""
    return x * 53 + 38 + 15

def fn_52_39(x: int) -> int:
    """Bench helper 52.39."""
    return x * 53 + 39 + 15

class Box_52:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_52_{k % 40}(k)
        return total

