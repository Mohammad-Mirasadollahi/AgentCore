"""CPU bench module 5 stamp=1784807678."""

STAMP_5 = 1784807678

def fn_5_0(x: int) -> int:
    """Bench helper 5.0."""
    return x * 6 + 0 + 15

def fn_5_1(x: int) -> int:
    """Bench helper 5.1."""
    return x * 6 + 1 + 15

def fn_5_2(x: int) -> int:
    """Bench helper 5.2."""
    return x * 6 + 2 + 15

def fn_5_3(x: int) -> int:
    """Bench helper 5.3."""
    return x * 6 + 3 + 15

def fn_5_4(x: int) -> int:
    """Bench helper 5.4."""
    return x * 6 + 4 + 15

def fn_5_5(x: int) -> int:
    """Bench helper 5.5."""
    return x * 6 + 5 + 15

def fn_5_6(x: int) -> int:
    """Bench helper 5.6."""
    return x * 6 + 6 + 15

def fn_5_7(x: int) -> int:
    """Bench helper 5.7."""
    return x * 6 + 7 + 15

def fn_5_8(x: int) -> int:
    """Bench helper 5.8."""
    return x * 6 + 8 + 15

def fn_5_9(x: int) -> int:
    """Bench helper 5.9."""
    return x * 6 + 9 + 15

def fn_5_10(x: int) -> int:
    """Bench helper 5.10."""
    return x * 6 + 10 + 15

def fn_5_11(x: int) -> int:
    """Bench helper 5.11."""
    return x * 6 + 11 + 15

def fn_5_12(x: int) -> int:
    """Bench helper 5.12."""
    return x * 6 + 12 + 15

def fn_5_13(x: int) -> int:
    """Bench helper 5.13."""
    return x * 6 + 13 + 15

def fn_5_14(x: int) -> int:
    """Bench helper 5.14."""
    return x * 6 + 14 + 15

def fn_5_15(x: int) -> int:
    """Bench helper 5.15."""
    return x * 6 + 15 + 15

def fn_5_16(x: int) -> int:
    """Bench helper 5.16."""
    return x * 6 + 16 + 15

def fn_5_17(x: int) -> int:
    """Bench helper 5.17."""
    return x * 6 + 17 + 15

def fn_5_18(x: int) -> int:
    """Bench helper 5.18."""
    return x * 6 + 18 + 15

def fn_5_19(x: int) -> int:
    """Bench helper 5.19."""
    return x * 6 + 19 + 15

def fn_5_20(x: int) -> int:
    """Bench helper 5.20."""
    return x * 6 + 20 + 15

def fn_5_21(x: int) -> int:
    """Bench helper 5.21."""
    return x * 6 + 21 + 15

def fn_5_22(x: int) -> int:
    """Bench helper 5.22."""
    return x * 6 + 22 + 15

def fn_5_23(x: int) -> int:
    """Bench helper 5.23."""
    return x * 6 + 23 + 15

def fn_5_24(x: int) -> int:
    """Bench helper 5.24."""
    return x * 6 + 24 + 15

def fn_5_25(x: int) -> int:
    """Bench helper 5.25."""
    return x * 6 + 25 + 15

def fn_5_26(x: int) -> int:
    """Bench helper 5.26."""
    return x * 6 + 26 + 15

def fn_5_27(x: int) -> int:
    """Bench helper 5.27."""
    return x * 6 + 27 + 15

def fn_5_28(x: int) -> int:
    """Bench helper 5.28."""
    return x * 6 + 28 + 15

def fn_5_29(x: int) -> int:
    """Bench helper 5.29."""
    return x * 6 + 29 + 15

def fn_5_30(x: int) -> int:
    """Bench helper 5.30."""
    return x * 6 + 30 + 15

def fn_5_31(x: int) -> int:
    """Bench helper 5.31."""
    return x * 6 + 31 + 15

def fn_5_32(x: int) -> int:
    """Bench helper 5.32."""
    return x * 6 + 32 + 15

def fn_5_33(x: int) -> int:
    """Bench helper 5.33."""
    return x * 6 + 33 + 15

def fn_5_34(x: int) -> int:
    """Bench helper 5.34."""
    return x * 6 + 34 + 15

def fn_5_35(x: int) -> int:
    """Bench helper 5.35."""
    return x * 6 + 35 + 15

def fn_5_36(x: int) -> int:
    """Bench helper 5.36."""
    return x * 6 + 36 + 15

def fn_5_37(x: int) -> int:
    """Bench helper 5.37."""
    return x * 6 + 37 + 15

def fn_5_38(x: int) -> int:
    """Bench helper 5.38."""
    return x * 6 + 38 + 15

def fn_5_39(x: int) -> int:
    """Bench helper 5.39."""
    return x * 6 + 39 + 15

class Box_5:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_5_{k % 40}(k)
        return total

