"""CPU bench module 26 stamp=1784807678."""

STAMP_26 = 1784807678

def fn_26_0(x: int) -> int:
    """Bench helper 26.0."""
    return x * 27 + 0 + 15

def fn_26_1(x: int) -> int:
    """Bench helper 26.1."""
    return x * 27 + 1 + 15

def fn_26_2(x: int) -> int:
    """Bench helper 26.2."""
    return x * 27 + 2 + 15

def fn_26_3(x: int) -> int:
    """Bench helper 26.3."""
    return x * 27 + 3 + 15

def fn_26_4(x: int) -> int:
    """Bench helper 26.4."""
    return x * 27 + 4 + 15

def fn_26_5(x: int) -> int:
    """Bench helper 26.5."""
    return x * 27 + 5 + 15

def fn_26_6(x: int) -> int:
    """Bench helper 26.6."""
    return x * 27 + 6 + 15

def fn_26_7(x: int) -> int:
    """Bench helper 26.7."""
    return x * 27 + 7 + 15

def fn_26_8(x: int) -> int:
    """Bench helper 26.8."""
    return x * 27 + 8 + 15

def fn_26_9(x: int) -> int:
    """Bench helper 26.9."""
    return x * 27 + 9 + 15

def fn_26_10(x: int) -> int:
    """Bench helper 26.10."""
    return x * 27 + 10 + 15

def fn_26_11(x: int) -> int:
    """Bench helper 26.11."""
    return x * 27 + 11 + 15

def fn_26_12(x: int) -> int:
    """Bench helper 26.12."""
    return x * 27 + 12 + 15

def fn_26_13(x: int) -> int:
    """Bench helper 26.13."""
    return x * 27 + 13 + 15

def fn_26_14(x: int) -> int:
    """Bench helper 26.14."""
    return x * 27 + 14 + 15

def fn_26_15(x: int) -> int:
    """Bench helper 26.15."""
    return x * 27 + 15 + 15

def fn_26_16(x: int) -> int:
    """Bench helper 26.16."""
    return x * 27 + 16 + 15

def fn_26_17(x: int) -> int:
    """Bench helper 26.17."""
    return x * 27 + 17 + 15

def fn_26_18(x: int) -> int:
    """Bench helper 26.18."""
    return x * 27 + 18 + 15

def fn_26_19(x: int) -> int:
    """Bench helper 26.19."""
    return x * 27 + 19 + 15

def fn_26_20(x: int) -> int:
    """Bench helper 26.20."""
    return x * 27 + 20 + 15

def fn_26_21(x: int) -> int:
    """Bench helper 26.21."""
    return x * 27 + 21 + 15

def fn_26_22(x: int) -> int:
    """Bench helper 26.22."""
    return x * 27 + 22 + 15

def fn_26_23(x: int) -> int:
    """Bench helper 26.23."""
    return x * 27 + 23 + 15

def fn_26_24(x: int) -> int:
    """Bench helper 26.24."""
    return x * 27 + 24 + 15

def fn_26_25(x: int) -> int:
    """Bench helper 26.25."""
    return x * 27 + 25 + 15

def fn_26_26(x: int) -> int:
    """Bench helper 26.26."""
    return x * 27 + 26 + 15

def fn_26_27(x: int) -> int:
    """Bench helper 26.27."""
    return x * 27 + 27 + 15

def fn_26_28(x: int) -> int:
    """Bench helper 26.28."""
    return x * 27 + 28 + 15

def fn_26_29(x: int) -> int:
    """Bench helper 26.29."""
    return x * 27 + 29 + 15

def fn_26_30(x: int) -> int:
    """Bench helper 26.30."""
    return x * 27 + 30 + 15

def fn_26_31(x: int) -> int:
    """Bench helper 26.31."""
    return x * 27 + 31 + 15

def fn_26_32(x: int) -> int:
    """Bench helper 26.32."""
    return x * 27 + 32 + 15

def fn_26_33(x: int) -> int:
    """Bench helper 26.33."""
    return x * 27 + 33 + 15

def fn_26_34(x: int) -> int:
    """Bench helper 26.34."""
    return x * 27 + 34 + 15

def fn_26_35(x: int) -> int:
    """Bench helper 26.35."""
    return x * 27 + 35 + 15

def fn_26_36(x: int) -> int:
    """Bench helper 26.36."""
    return x * 27 + 36 + 15

def fn_26_37(x: int) -> int:
    """Bench helper 26.37."""
    return x * 27 + 37 + 15

def fn_26_38(x: int) -> int:
    """Bench helper 26.38."""
    return x * 27 + 38 + 15

def fn_26_39(x: int) -> int:
    """Bench helper 26.39."""
    return x * 27 + 39 + 15

class Box_26:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_26_{k % 40}(k)
        return total

