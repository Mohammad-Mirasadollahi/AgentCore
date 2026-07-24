"""CPU bench module 9 stamp=1784807678."""

STAMP_9 = 1784807678

def fn_9_0(x: int) -> int:
    """Bench helper 9.0."""
    return x * 10 + 0 + 15

def fn_9_1(x: int) -> int:
    """Bench helper 9.1."""
    return x * 10 + 1 + 15

def fn_9_2(x: int) -> int:
    """Bench helper 9.2."""
    return x * 10 + 2 + 15

def fn_9_3(x: int) -> int:
    """Bench helper 9.3."""
    return x * 10 + 3 + 15

def fn_9_4(x: int) -> int:
    """Bench helper 9.4."""
    return x * 10 + 4 + 15

def fn_9_5(x: int) -> int:
    """Bench helper 9.5."""
    return x * 10 + 5 + 15

def fn_9_6(x: int) -> int:
    """Bench helper 9.6."""
    return x * 10 + 6 + 15

def fn_9_7(x: int) -> int:
    """Bench helper 9.7."""
    return x * 10 + 7 + 15

def fn_9_8(x: int) -> int:
    """Bench helper 9.8."""
    return x * 10 + 8 + 15

def fn_9_9(x: int) -> int:
    """Bench helper 9.9."""
    return x * 10 + 9 + 15

def fn_9_10(x: int) -> int:
    """Bench helper 9.10."""
    return x * 10 + 10 + 15

def fn_9_11(x: int) -> int:
    """Bench helper 9.11."""
    return x * 10 + 11 + 15

def fn_9_12(x: int) -> int:
    """Bench helper 9.12."""
    return x * 10 + 12 + 15

def fn_9_13(x: int) -> int:
    """Bench helper 9.13."""
    return x * 10 + 13 + 15

def fn_9_14(x: int) -> int:
    """Bench helper 9.14."""
    return x * 10 + 14 + 15

def fn_9_15(x: int) -> int:
    """Bench helper 9.15."""
    return x * 10 + 15 + 15

def fn_9_16(x: int) -> int:
    """Bench helper 9.16."""
    return x * 10 + 16 + 15

def fn_9_17(x: int) -> int:
    """Bench helper 9.17."""
    return x * 10 + 17 + 15

def fn_9_18(x: int) -> int:
    """Bench helper 9.18."""
    return x * 10 + 18 + 15

def fn_9_19(x: int) -> int:
    """Bench helper 9.19."""
    return x * 10 + 19 + 15

def fn_9_20(x: int) -> int:
    """Bench helper 9.20."""
    return x * 10 + 20 + 15

def fn_9_21(x: int) -> int:
    """Bench helper 9.21."""
    return x * 10 + 21 + 15

def fn_9_22(x: int) -> int:
    """Bench helper 9.22."""
    return x * 10 + 22 + 15

def fn_9_23(x: int) -> int:
    """Bench helper 9.23."""
    return x * 10 + 23 + 15

def fn_9_24(x: int) -> int:
    """Bench helper 9.24."""
    return x * 10 + 24 + 15

def fn_9_25(x: int) -> int:
    """Bench helper 9.25."""
    return x * 10 + 25 + 15

def fn_9_26(x: int) -> int:
    """Bench helper 9.26."""
    return x * 10 + 26 + 15

def fn_9_27(x: int) -> int:
    """Bench helper 9.27."""
    return x * 10 + 27 + 15

def fn_9_28(x: int) -> int:
    """Bench helper 9.28."""
    return x * 10 + 28 + 15

def fn_9_29(x: int) -> int:
    """Bench helper 9.29."""
    return x * 10 + 29 + 15

def fn_9_30(x: int) -> int:
    """Bench helper 9.30."""
    return x * 10 + 30 + 15

def fn_9_31(x: int) -> int:
    """Bench helper 9.31."""
    return x * 10 + 31 + 15

def fn_9_32(x: int) -> int:
    """Bench helper 9.32."""
    return x * 10 + 32 + 15

def fn_9_33(x: int) -> int:
    """Bench helper 9.33."""
    return x * 10 + 33 + 15

def fn_9_34(x: int) -> int:
    """Bench helper 9.34."""
    return x * 10 + 34 + 15

def fn_9_35(x: int) -> int:
    """Bench helper 9.35."""
    return x * 10 + 35 + 15

def fn_9_36(x: int) -> int:
    """Bench helper 9.36."""
    return x * 10 + 36 + 15

def fn_9_37(x: int) -> int:
    """Bench helper 9.37."""
    return x * 10 + 37 + 15

def fn_9_38(x: int) -> int:
    """Bench helper 9.38."""
    return x * 10 + 38 + 15

def fn_9_39(x: int) -> int:
    """Bench helper 9.39."""
    return x * 10 + 39 + 15

class Box_9:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_9_{k % 40}(k)
        return total

