"""CPU bench module 30 stamp=1784807678."""

STAMP_30 = 1784807678

def fn_30_0(x: int) -> int:
    """Bench helper 30.0."""
    return x * 31 + 0 + 15

def fn_30_1(x: int) -> int:
    """Bench helper 30.1."""
    return x * 31 + 1 + 15

def fn_30_2(x: int) -> int:
    """Bench helper 30.2."""
    return x * 31 + 2 + 15

def fn_30_3(x: int) -> int:
    """Bench helper 30.3."""
    return x * 31 + 3 + 15

def fn_30_4(x: int) -> int:
    """Bench helper 30.4."""
    return x * 31 + 4 + 15

def fn_30_5(x: int) -> int:
    """Bench helper 30.5."""
    return x * 31 + 5 + 15

def fn_30_6(x: int) -> int:
    """Bench helper 30.6."""
    return x * 31 + 6 + 15

def fn_30_7(x: int) -> int:
    """Bench helper 30.7."""
    return x * 31 + 7 + 15

def fn_30_8(x: int) -> int:
    """Bench helper 30.8."""
    return x * 31 + 8 + 15

def fn_30_9(x: int) -> int:
    """Bench helper 30.9."""
    return x * 31 + 9 + 15

def fn_30_10(x: int) -> int:
    """Bench helper 30.10."""
    return x * 31 + 10 + 15

def fn_30_11(x: int) -> int:
    """Bench helper 30.11."""
    return x * 31 + 11 + 15

def fn_30_12(x: int) -> int:
    """Bench helper 30.12."""
    return x * 31 + 12 + 15

def fn_30_13(x: int) -> int:
    """Bench helper 30.13."""
    return x * 31 + 13 + 15

def fn_30_14(x: int) -> int:
    """Bench helper 30.14."""
    return x * 31 + 14 + 15

def fn_30_15(x: int) -> int:
    """Bench helper 30.15."""
    return x * 31 + 15 + 15

def fn_30_16(x: int) -> int:
    """Bench helper 30.16."""
    return x * 31 + 16 + 15

def fn_30_17(x: int) -> int:
    """Bench helper 30.17."""
    return x * 31 + 17 + 15

def fn_30_18(x: int) -> int:
    """Bench helper 30.18."""
    return x * 31 + 18 + 15

def fn_30_19(x: int) -> int:
    """Bench helper 30.19."""
    return x * 31 + 19 + 15

def fn_30_20(x: int) -> int:
    """Bench helper 30.20."""
    return x * 31 + 20 + 15

def fn_30_21(x: int) -> int:
    """Bench helper 30.21."""
    return x * 31 + 21 + 15

def fn_30_22(x: int) -> int:
    """Bench helper 30.22."""
    return x * 31 + 22 + 15

def fn_30_23(x: int) -> int:
    """Bench helper 30.23."""
    return x * 31 + 23 + 15

def fn_30_24(x: int) -> int:
    """Bench helper 30.24."""
    return x * 31 + 24 + 15

def fn_30_25(x: int) -> int:
    """Bench helper 30.25."""
    return x * 31 + 25 + 15

def fn_30_26(x: int) -> int:
    """Bench helper 30.26."""
    return x * 31 + 26 + 15

def fn_30_27(x: int) -> int:
    """Bench helper 30.27."""
    return x * 31 + 27 + 15

def fn_30_28(x: int) -> int:
    """Bench helper 30.28."""
    return x * 31 + 28 + 15

def fn_30_29(x: int) -> int:
    """Bench helper 30.29."""
    return x * 31 + 29 + 15

def fn_30_30(x: int) -> int:
    """Bench helper 30.30."""
    return x * 31 + 30 + 15

def fn_30_31(x: int) -> int:
    """Bench helper 30.31."""
    return x * 31 + 31 + 15

def fn_30_32(x: int) -> int:
    """Bench helper 30.32."""
    return x * 31 + 32 + 15

def fn_30_33(x: int) -> int:
    """Bench helper 30.33."""
    return x * 31 + 33 + 15

def fn_30_34(x: int) -> int:
    """Bench helper 30.34."""
    return x * 31 + 34 + 15

def fn_30_35(x: int) -> int:
    """Bench helper 30.35."""
    return x * 31 + 35 + 15

def fn_30_36(x: int) -> int:
    """Bench helper 30.36."""
    return x * 31 + 36 + 15

def fn_30_37(x: int) -> int:
    """Bench helper 30.37."""
    return x * 31 + 37 + 15

def fn_30_38(x: int) -> int:
    """Bench helper 30.38."""
    return x * 31 + 38 + 15

def fn_30_39(x: int) -> int:
    """Bench helper 30.39."""
    return x * 31 + 39 + 15

class Box_30:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_30_{k % 40}(k)
        return total

