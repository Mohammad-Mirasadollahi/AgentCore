"""CPU bench module 36 stamp=1784807678."""

STAMP_36 = 1784807678

def fn_36_0(x: int) -> int:
    """Bench helper 36.0."""
    return x * 37 + 0 + 15

def fn_36_1(x: int) -> int:
    """Bench helper 36.1."""
    return x * 37 + 1 + 15

def fn_36_2(x: int) -> int:
    """Bench helper 36.2."""
    return x * 37 + 2 + 15

def fn_36_3(x: int) -> int:
    """Bench helper 36.3."""
    return x * 37 + 3 + 15

def fn_36_4(x: int) -> int:
    """Bench helper 36.4."""
    return x * 37 + 4 + 15

def fn_36_5(x: int) -> int:
    """Bench helper 36.5."""
    return x * 37 + 5 + 15

def fn_36_6(x: int) -> int:
    """Bench helper 36.6."""
    return x * 37 + 6 + 15

def fn_36_7(x: int) -> int:
    """Bench helper 36.7."""
    return x * 37 + 7 + 15

def fn_36_8(x: int) -> int:
    """Bench helper 36.8."""
    return x * 37 + 8 + 15

def fn_36_9(x: int) -> int:
    """Bench helper 36.9."""
    return x * 37 + 9 + 15

def fn_36_10(x: int) -> int:
    """Bench helper 36.10."""
    return x * 37 + 10 + 15

def fn_36_11(x: int) -> int:
    """Bench helper 36.11."""
    return x * 37 + 11 + 15

def fn_36_12(x: int) -> int:
    """Bench helper 36.12."""
    return x * 37 + 12 + 15

def fn_36_13(x: int) -> int:
    """Bench helper 36.13."""
    return x * 37 + 13 + 15

def fn_36_14(x: int) -> int:
    """Bench helper 36.14."""
    return x * 37 + 14 + 15

def fn_36_15(x: int) -> int:
    """Bench helper 36.15."""
    return x * 37 + 15 + 15

def fn_36_16(x: int) -> int:
    """Bench helper 36.16."""
    return x * 37 + 16 + 15

def fn_36_17(x: int) -> int:
    """Bench helper 36.17."""
    return x * 37 + 17 + 15

def fn_36_18(x: int) -> int:
    """Bench helper 36.18."""
    return x * 37 + 18 + 15

def fn_36_19(x: int) -> int:
    """Bench helper 36.19."""
    return x * 37 + 19 + 15

def fn_36_20(x: int) -> int:
    """Bench helper 36.20."""
    return x * 37 + 20 + 15

def fn_36_21(x: int) -> int:
    """Bench helper 36.21."""
    return x * 37 + 21 + 15

def fn_36_22(x: int) -> int:
    """Bench helper 36.22."""
    return x * 37 + 22 + 15

def fn_36_23(x: int) -> int:
    """Bench helper 36.23."""
    return x * 37 + 23 + 15

def fn_36_24(x: int) -> int:
    """Bench helper 36.24."""
    return x * 37 + 24 + 15

def fn_36_25(x: int) -> int:
    """Bench helper 36.25."""
    return x * 37 + 25 + 15

def fn_36_26(x: int) -> int:
    """Bench helper 36.26."""
    return x * 37 + 26 + 15

def fn_36_27(x: int) -> int:
    """Bench helper 36.27."""
    return x * 37 + 27 + 15

def fn_36_28(x: int) -> int:
    """Bench helper 36.28."""
    return x * 37 + 28 + 15

def fn_36_29(x: int) -> int:
    """Bench helper 36.29."""
    return x * 37 + 29 + 15

def fn_36_30(x: int) -> int:
    """Bench helper 36.30."""
    return x * 37 + 30 + 15

def fn_36_31(x: int) -> int:
    """Bench helper 36.31."""
    return x * 37 + 31 + 15

def fn_36_32(x: int) -> int:
    """Bench helper 36.32."""
    return x * 37 + 32 + 15

def fn_36_33(x: int) -> int:
    """Bench helper 36.33."""
    return x * 37 + 33 + 15

def fn_36_34(x: int) -> int:
    """Bench helper 36.34."""
    return x * 37 + 34 + 15

def fn_36_35(x: int) -> int:
    """Bench helper 36.35."""
    return x * 37 + 35 + 15

def fn_36_36(x: int) -> int:
    """Bench helper 36.36."""
    return x * 37 + 36 + 15

def fn_36_37(x: int) -> int:
    """Bench helper 36.37."""
    return x * 37 + 37 + 15

def fn_36_38(x: int) -> int:
    """Bench helper 36.38."""
    return x * 37 + 38 + 15

def fn_36_39(x: int) -> int:
    """Bench helper 36.39."""
    return x * 37 + 39 + 15

class Box_36:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_36_{k % 40}(k)
        return total

