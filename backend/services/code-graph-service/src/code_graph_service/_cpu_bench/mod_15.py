"""CPU bench module 15 stamp=1784807678."""

STAMP_15 = 1784807678

def fn_15_0(x: int) -> int:
    """Bench helper 15.0."""
    return x * 16 + 0 + 15

def fn_15_1(x: int) -> int:
    """Bench helper 15.1."""
    return x * 16 + 1 + 15

def fn_15_2(x: int) -> int:
    """Bench helper 15.2."""
    return x * 16 + 2 + 15

def fn_15_3(x: int) -> int:
    """Bench helper 15.3."""
    return x * 16 + 3 + 15

def fn_15_4(x: int) -> int:
    """Bench helper 15.4."""
    return x * 16 + 4 + 15

def fn_15_5(x: int) -> int:
    """Bench helper 15.5."""
    return x * 16 + 5 + 15

def fn_15_6(x: int) -> int:
    """Bench helper 15.6."""
    return x * 16 + 6 + 15

def fn_15_7(x: int) -> int:
    """Bench helper 15.7."""
    return x * 16 + 7 + 15

def fn_15_8(x: int) -> int:
    """Bench helper 15.8."""
    return x * 16 + 8 + 15

def fn_15_9(x: int) -> int:
    """Bench helper 15.9."""
    return x * 16 + 9 + 15

def fn_15_10(x: int) -> int:
    """Bench helper 15.10."""
    return x * 16 + 10 + 15

def fn_15_11(x: int) -> int:
    """Bench helper 15.11."""
    return x * 16 + 11 + 15

def fn_15_12(x: int) -> int:
    """Bench helper 15.12."""
    return x * 16 + 12 + 15

def fn_15_13(x: int) -> int:
    """Bench helper 15.13."""
    return x * 16 + 13 + 15

def fn_15_14(x: int) -> int:
    """Bench helper 15.14."""
    return x * 16 + 14 + 15

def fn_15_15(x: int) -> int:
    """Bench helper 15.15."""
    return x * 16 + 15 + 15

def fn_15_16(x: int) -> int:
    """Bench helper 15.16."""
    return x * 16 + 16 + 15

def fn_15_17(x: int) -> int:
    """Bench helper 15.17."""
    return x * 16 + 17 + 15

def fn_15_18(x: int) -> int:
    """Bench helper 15.18."""
    return x * 16 + 18 + 15

def fn_15_19(x: int) -> int:
    """Bench helper 15.19."""
    return x * 16 + 19 + 15

def fn_15_20(x: int) -> int:
    """Bench helper 15.20."""
    return x * 16 + 20 + 15

def fn_15_21(x: int) -> int:
    """Bench helper 15.21."""
    return x * 16 + 21 + 15

def fn_15_22(x: int) -> int:
    """Bench helper 15.22."""
    return x * 16 + 22 + 15

def fn_15_23(x: int) -> int:
    """Bench helper 15.23."""
    return x * 16 + 23 + 15

def fn_15_24(x: int) -> int:
    """Bench helper 15.24."""
    return x * 16 + 24 + 15

def fn_15_25(x: int) -> int:
    """Bench helper 15.25."""
    return x * 16 + 25 + 15

def fn_15_26(x: int) -> int:
    """Bench helper 15.26."""
    return x * 16 + 26 + 15

def fn_15_27(x: int) -> int:
    """Bench helper 15.27."""
    return x * 16 + 27 + 15

def fn_15_28(x: int) -> int:
    """Bench helper 15.28."""
    return x * 16 + 28 + 15

def fn_15_29(x: int) -> int:
    """Bench helper 15.29."""
    return x * 16 + 29 + 15

def fn_15_30(x: int) -> int:
    """Bench helper 15.30."""
    return x * 16 + 30 + 15

def fn_15_31(x: int) -> int:
    """Bench helper 15.31."""
    return x * 16 + 31 + 15

def fn_15_32(x: int) -> int:
    """Bench helper 15.32."""
    return x * 16 + 32 + 15

def fn_15_33(x: int) -> int:
    """Bench helper 15.33."""
    return x * 16 + 33 + 15

def fn_15_34(x: int) -> int:
    """Bench helper 15.34."""
    return x * 16 + 34 + 15

def fn_15_35(x: int) -> int:
    """Bench helper 15.35."""
    return x * 16 + 35 + 15

def fn_15_36(x: int) -> int:
    """Bench helper 15.36."""
    return x * 16 + 36 + 15

def fn_15_37(x: int) -> int:
    """Bench helper 15.37."""
    return x * 16 + 37 + 15

def fn_15_38(x: int) -> int:
    """Bench helper 15.38."""
    return x * 16 + 38 + 15

def fn_15_39(x: int) -> int:
    """Bench helper 15.39."""
    return x * 16 + 39 + 15

class Box_15:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_15_{k % 40}(k)
        return total

