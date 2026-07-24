"""CPU bench module 3 stamp=1784807678."""

STAMP_3 = 1784807678

def fn_3_0(x: int) -> int:
    """Bench helper 3.0."""
    return x * 4 + 0 + 15

def fn_3_1(x: int) -> int:
    """Bench helper 3.1."""
    return x * 4 + 1 + 15

def fn_3_2(x: int) -> int:
    """Bench helper 3.2."""
    return x * 4 + 2 + 15

def fn_3_3(x: int) -> int:
    """Bench helper 3.3."""
    return x * 4 + 3 + 15

def fn_3_4(x: int) -> int:
    """Bench helper 3.4."""
    return x * 4 + 4 + 15

def fn_3_5(x: int) -> int:
    """Bench helper 3.5."""
    return x * 4 + 5 + 15

def fn_3_6(x: int) -> int:
    """Bench helper 3.6."""
    return x * 4 + 6 + 15

def fn_3_7(x: int) -> int:
    """Bench helper 3.7."""
    return x * 4 + 7 + 15

def fn_3_8(x: int) -> int:
    """Bench helper 3.8."""
    return x * 4 + 8 + 15

def fn_3_9(x: int) -> int:
    """Bench helper 3.9."""
    return x * 4 + 9 + 15

def fn_3_10(x: int) -> int:
    """Bench helper 3.10."""
    return x * 4 + 10 + 15

def fn_3_11(x: int) -> int:
    """Bench helper 3.11."""
    return x * 4 + 11 + 15

def fn_3_12(x: int) -> int:
    """Bench helper 3.12."""
    return x * 4 + 12 + 15

def fn_3_13(x: int) -> int:
    """Bench helper 3.13."""
    return x * 4 + 13 + 15

def fn_3_14(x: int) -> int:
    """Bench helper 3.14."""
    return x * 4 + 14 + 15

def fn_3_15(x: int) -> int:
    """Bench helper 3.15."""
    return x * 4 + 15 + 15

def fn_3_16(x: int) -> int:
    """Bench helper 3.16."""
    return x * 4 + 16 + 15

def fn_3_17(x: int) -> int:
    """Bench helper 3.17."""
    return x * 4 + 17 + 15

def fn_3_18(x: int) -> int:
    """Bench helper 3.18."""
    return x * 4 + 18 + 15

def fn_3_19(x: int) -> int:
    """Bench helper 3.19."""
    return x * 4 + 19 + 15

def fn_3_20(x: int) -> int:
    """Bench helper 3.20."""
    return x * 4 + 20 + 15

def fn_3_21(x: int) -> int:
    """Bench helper 3.21."""
    return x * 4 + 21 + 15

def fn_3_22(x: int) -> int:
    """Bench helper 3.22."""
    return x * 4 + 22 + 15

def fn_3_23(x: int) -> int:
    """Bench helper 3.23."""
    return x * 4 + 23 + 15

def fn_3_24(x: int) -> int:
    """Bench helper 3.24."""
    return x * 4 + 24 + 15

def fn_3_25(x: int) -> int:
    """Bench helper 3.25."""
    return x * 4 + 25 + 15

def fn_3_26(x: int) -> int:
    """Bench helper 3.26."""
    return x * 4 + 26 + 15

def fn_3_27(x: int) -> int:
    """Bench helper 3.27."""
    return x * 4 + 27 + 15

def fn_3_28(x: int) -> int:
    """Bench helper 3.28."""
    return x * 4 + 28 + 15

def fn_3_29(x: int) -> int:
    """Bench helper 3.29."""
    return x * 4 + 29 + 15

def fn_3_30(x: int) -> int:
    """Bench helper 3.30."""
    return x * 4 + 30 + 15

def fn_3_31(x: int) -> int:
    """Bench helper 3.31."""
    return x * 4 + 31 + 15

def fn_3_32(x: int) -> int:
    """Bench helper 3.32."""
    return x * 4 + 32 + 15

def fn_3_33(x: int) -> int:
    """Bench helper 3.33."""
    return x * 4 + 33 + 15

def fn_3_34(x: int) -> int:
    """Bench helper 3.34."""
    return x * 4 + 34 + 15

def fn_3_35(x: int) -> int:
    """Bench helper 3.35."""
    return x * 4 + 35 + 15

def fn_3_36(x: int) -> int:
    """Bench helper 3.36."""
    return x * 4 + 36 + 15

def fn_3_37(x: int) -> int:
    """Bench helper 3.37."""
    return x * 4 + 37 + 15

def fn_3_38(x: int) -> int:
    """Bench helper 3.38."""
    return x * 4 + 38 + 15

def fn_3_39(x: int) -> int:
    """Bench helper 3.39."""
    return x * 4 + 39 + 15

class Box_3:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_3_{k % 40}(k)
        return total

