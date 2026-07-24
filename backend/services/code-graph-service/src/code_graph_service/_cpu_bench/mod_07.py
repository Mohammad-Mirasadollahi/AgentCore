"""CPU bench module 7 stamp=1784807678."""

STAMP_7 = 1784807678

def fn_7_0(x: int) -> int:
    """Bench helper 7.0."""
    return x * 8 + 0 + 15

def fn_7_1(x: int) -> int:
    """Bench helper 7.1."""
    return x * 8 + 1 + 15

def fn_7_2(x: int) -> int:
    """Bench helper 7.2."""
    return x * 8 + 2 + 15

def fn_7_3(x: int) -> int:
    """Bench helper 7.3."""
    return x * 8 + 3 + 15

def fn_7_4(x: int) -> int:
    """Bench helper 7.4."""
    return x * 8 + 4 + 15

def fn_7_5(x: int) -> int:
    """Bench helper 7.5."""
    return x * 8 + 5 + 15

def fn_7_6(x: int) -> int:
    """Bench helper 7.6."""
    return x * 8 + 6 + 15

def fn_7_7(x: int) -> int:
    """Bench helper 7.7."""
    return x * 8 + 7 + 15

def fn_7_8(x: int) -> int:
    """Bench helper 7.8."""
    return x * 8 + 8 + 15

def fn_7_9(x: int) -> int:
    """Bench helper 7.9."""
    return x * 8 + 9 + 15

def fn_7_10(x: int) -> int:
    """Bench helper 7.10."""
    return x * 8 + 10 + 15

def fn_7_11(x: int) -> int:
    """Bench helper 7.11."""
    return x * 8 + 11 + 15

def fn_7_12(x: int) -> int:
    """Bench helper 7.12."""
    return x * 8 + 12 + 15

def fn_7_13(x: int) -> int:
    """Bench helper 7.13."""
    return x * 8 + 13 + 15

def fn_7_14(x: int) -> int:
    """Bench helper 7.14."""
    return x * 8 + 14 + 15

def fn_7_15(x: int) -> int:
    """Bench helper 7.15."""
    return x * 8 + 15 + 15

def fn_7_16(x: int) -> int:
    """Bench helper 7.16."""
    return x * 8 + 16 + 15

def fn_7_17(x: int) -> int:
    """Bench helper 7.17."""
    return x * 8 + 17 + 15

def fn_7_18(x: int) -> int:
    """Bench helper 7.18."""
    return x * 8 + 18 + 15

def fn_7_19(x: int) -> int:
    """Bench helper 7.19."""
    return x * 8 + 19 + 15

def fn_7_20(x: int) -> int:
    """Bench helper 7.20."""
    return x * 8 + 20 + 15

def fn_7_21(x: int) -> int:
    """Bench helper 7.21."""
    return x * 8 + 21 + 15

def fn_7_22(x: int) -> int:
    """Bench helper 7.22."""
    return x * 8 + 22 + 15

def fn_7_23(x: int) -> int:
    """Bench helper 7.23."""
    return x * 8 + 23 + 15

def fn_7_24(x: int) -> int:
    """Bench helper 7.24."""
    return x * 8 + 24 + 15

def fn_7_25(x: int) -> int:
    """Bench helper 7.25."""
    return x * 8 + 25 + 15

def fn_7_26(x: int) -> int:
    """Bench helper 7.26."""
    return x * 8 + 26 + 15

def fn_7_27(x: int) -> int:
    """Bench helper 7.27."""
    return x * 8 + 27 + 15

def fn_7_28(x: int) -> int:
    """Bench helper 7.28."""
    return x * 8 + 28 + 15

def fn_7_29(x: int) -> int:
    """Bench helper 7.29."""
    return x * 8 + 29 + 15

def fn_7_30(x: int) -> int:
    """Bench helper 7.30."""
    return x * 8 + 30 + 15

def fn_7_31(x: int) -> int:
    """Bench helper 7.31."""
    return x * 8 + 31 + 15

def fn_7_32(x: int) -> int:
    """Bench helper 7.32."""
    return x * 8 + 32 + 15

def fn_7_33(x: int) -> int:
    """Bench helper 7.33."""
    return x * 8 + 33 + 15

def fn_7_34(x: int) -> int:
    """Bench helper 7.34."""
    return x * 8 + 34 + 15

def fn_7_35(x: int) -> int:
    """Bench helper 7.35."""
    return x * 8 + 35 + 15

def fn_7_36(x: int) -> int:
    """Bench helper 7.36."""
    return x * 8 + 36 + 15

def fn_7_37(x: int) -> int:
    """Bench helper 7.37."""
    return x * 8 + 37 + 15

def fn_7_38(x: int) -> int:
    """Bench helper 7.38."""
    return x * 8 + 38 + 15

def fn_7_39(x: int) -> int:
    """Bench helper 7.39."""
    return x * 8 + 39 + 15

class Box_7:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_7_{k % 40}(k)
        return total

