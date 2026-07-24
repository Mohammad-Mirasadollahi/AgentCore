"""CPU bench module 40 stamp=1784807678."""

STAMP_40 = 1784807678

def fn_40_0(x: int) -> int:
    """Bench helper 40.0."""
    return x * 41 + 0 + 15

def fn_40_1(x: int) -> int:
    """Bench helper 40.1."""
    return x * 41 + 1 + 15

def fn_40_2(x: int) -> int:
    """Bench helper 40.2."""
    return x * 41 + 2 + 15

def fn_40_3(x: int) -> int:
    """Bench helper 40.3."""
    return x * 41 + 3 + 15

def fn_40_4(x: int) -> int:
    """Bench helper 40.4."""
    return x * 41 + 4 + 15

def fn_40_5(x: int) -> int:
    """Bench helper 40.5."""
    return x * 41 + 5 + 15

def fn_40_6(x: int) -> int:
    """Bench helper 40.6."""
    return x * 41 + 6 + 15

def fn_40_7(x: int) -> int:
    """Bench helper 40.7."""
    return x * 41 + 7 + 15

def fn_40_8(x: int) -> int:
    """Bench helper 40.8."""
    return x * 41 + 8 + 15

def fn_40_9(x: int) -> int:
    """Bench helper 40.9."""
    return x * 41 + 9 + 15

def fn_40_10(x: int) -> int:
    """Bench helper 40.10."""
    return x * 41 + 10 + 15

def fn_40_11(x: int) -> int:
    """Bench helper 40.11."""
    return x * 41 + 11 + 15

def fn_40_12(x: int) -> int:
    """Bench helper 40.12."""
    return x * 41 + 12 + 15

def fn_40_13(x: int) -> int:
    """Bench helper 40.13."""
    return x * 41 + 13 + 15

def fn_40_14(x: int) -> int:
    """Bench helper 40.14."""
    return x * 41 + 14 + 15

def fn_40_15(x: int) -> int:
    """Bench helper 40.15."""
    return x * 41 + 15 + 15

def fn_40_16(x: int) -> int:
    """Bench helper 40.16."""
    return x * 41 + 16 + 15

def fn_40_17(x: int) -> int:
    """Bench helper 40.17."""
    return x * 41 + 17 + 15

def fn_40_18(x: int) -> int:
    """Bench helper 40.18."""
    return x * 41 + 18 + 15

def fn_40_19(x: int) -> int:
    """Bench helper 40.19."""
    return x * 41 + 19 + 15

def fn_40_20(x: int) -> int:
    """Bench helper 40.20."""
    return x * 41 + 20 + 15

def fn_40_21(x: int) -> int:
    """Bench helper 40.21."""
    return x * 41 + 21 + 15

def fn_40_22(x: int) -> int:
    """Bench helper 40.22."""
    return x * 41 + 22 + 15

def fn_40_23(x: int) -> int:
    """Bench helper 40.23."""
    return x * 41 + 23 + 15

def fn_40_24(x: int) -> int:
    """Bench helper 40.24."""
    return x * 41 + 24 + 15

def fn_40_25(x: int) -> int:
    """Bench helper 40.25."""
    return x * 41 + 25 + 15

def fn_40_26(x: int) -> int:
    """Bench helper 40.26."""
    return x * 41 + 26 + 15

def fn_40_27(x: int) -> int:
    """Bench helper 40.27."""
    return x * 41 + 27 + 15

def fn_40_28(x: int) -> int:
    """Bench helper 40.28."""
    return x * 41 + 28 + 15

def fn_40_29(x: int) -> int:
    """Bench helper 40.29."""
    return x * 41 + 29 + 15

def fn_40_30(x: int) -> int:
    """Bench helper 40.30."""
    return x * 41 + 30 + 15

def fn_40_31(x: int) -> int:
    """Bench helper 40.31."""
    return x * 41 + 31 + 15

def fn_40_32(x: int) -> int:
    """Bench helper 40.32."""
    return x * 41 + 32 + 15

def fn_40_33(x: int) -> int:
    """Bench helper 40.33."""
    return x * 41 + 33 + 15

def fn_40_34(x: int) -> int:
    """Bench helper 40.34."""
    return x * 41 + 34 + 15

def fn_40_35(x: int) -> int:
    """Bench helper 40.35."""
    return x * 41 + 35 + 15

def fn_40_36(x: int) -> int:
    """Bench helper 40.36."""
    return x * 41 + 36 + 15

def fn_40_37(x: int) -> int:
    """Bench helper 40.37."""
    return x * 41 + 37 + 15

def fn_40_38(x: int) -> int:
    """Bench helper 40.38."""
    return x * 41 + 38 + 15

def fn_40_39(x: int) -> int:
    """Bench helper 40.39."""
    return x * 41 + 39 + 15

class Box_40:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_40_{k % 40}(k)
        return total

