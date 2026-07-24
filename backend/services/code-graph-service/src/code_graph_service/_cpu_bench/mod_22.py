"""CPU bench module 22 stamp=1784807678."""

STAMP_22 = 1784807678

def fn_22_0(x: int) -> int:
    """Bench helper 22.0."""
    return x * 23 + 0 + 15

def fn_22_1(x: int) -> int:
    """Bench helper 22.1."""
    return x * 23 + 1 + 15

def fn_22_2(x: int) -> int:
    """Bench helper 22.2."""
    return x * 23 + 2 + 15

def fn_22_3(x: int) -> int:
    """Bench helper 22.3."""
    return x * 23 + 3 + 15

def fn_22_4(x: int) -> int:
    """Bench helper 22.4."""
    return x * 23 + 4 + 15

def fn_22_5(x: int) -> int:
    """Bench helper 22.5."""
    return x * 23 + 5 + 15

def fn_22_6(x: int) -> int:
    """Bench helper 22.6."""
    return x * 23 + 6 + 15

def fn_22_7(x: int) -> int:
    """Bench helper 22.7."""
    return x * 23 + 7 + 15

def fn_22_8(x: int) -> int:
    """Bench helper 22.8."""
    return x * 23 + 8 + 15

def fn_22_9(x: int) -> int:
    """Bench helper 22.9."""
    return x * 23 + 9 + 15

def fn_22_10(x: int) -> int:
    """Bench helper 22.10."""
    return x * 23 + 10 + 15

def fn_22_11(x: int) -> int:
    """Bench helper 22.11."""
    return x * 23 + 11 + 15

def fn_22_12(x: int) -> int:
    """Bench helper 22.12."""
    return x * 23 + 12 + 15

def fn_22_13(x: int) -> int:
    """Bench helper 22.13."""
    return x * 23 + 13 + 15

def fn_22_14(x: int) -> int:
    """Bench helper 22.14."""
    return x * 23 + 14 + 15

def fn_22_15(x: int) -> int:
    """Bench helper 22.15."""
    return x * 23 + 15 + 15

def fn_22_16(x: int) -> int:
    """Bench helper 22.16."""
    return x * 23 + 16 + 15

def fn_22_17(x: int) -> int:
    """Bench helper 22.17."""
    return x * 23 + 17 + 15

def fn_22_18(x: int) -> int:
    """Bench helper 22.18."""
    return x * 23 + 18 + 15

def fn_22_19(x: int) -> int:
    """Bench helper 22.19."""
    return x * 23 + 19 + 15

def fn_22_20(x: int) -> int:
    """Bench helper 22.20."""
    return x * 23 + 20 + 15

def fn_22_21(x: int) -> int:
    """Bench helper 22.21."""
    return x * 23 + 21 + 15

def fn_22_22(x: int) -> int:
    """Bench helper 22.22."""
    return x * 23 + 22 + 15

def fn_22_23(x: int) -> int:
    """Bench helper 22.23."""
    return x * 23 + 23 + 15

def fn_22_24(x: int) -> int:
    """Bench helper 22.24."""
    return x * 23 + 24 + 15

def fn_22_25(x: int) -> int:
    """Bench helper 22.25."""
    return x * 23 + 25 + 15

def fn_22_26(x: int) -> int:
    """Bench helper 22.26."""
    return x * 23 + 26 + 15

def fn_22_27(x: int) -> int:
    """Bench helper 22.27."""
    return x * 23 + 27 + 15

def fn_22_28(x: int) -> int:
    """Bench helper 22.28."""
    return x * 23 + 28 + 15

def fn_22_29(x: int) -> int:
    """Bench helper 22.29."""
    return x * 23 + 29 + 15

def fn_22_30(x: int) -> int:
    """Bench helper 22.30."""
    return x * 23 + 30 + 15

def fn_22_31(x: int) -> int:
    """Bench helper 22.31."""
    return x * 23 + 31 + 15

def fn_22_32(x: int) -> int:
    """Bench helper 22.32."""
    return x * 23 + 32 + 15

def fn_22_33(x: int) -> int:
    """Bench helper 22.33."""
    return x * 23 + 33 + 15

def fn_22_34(x: int) -> int:
    """Bench helper 22.34."""
    return x * 23 + 34 + 15

def fn_22_35(x: int) -> int:
    """Bench helper 22.35."""
    return x * 23 + 35 + 15

def fn_22_36(x: int) -> int:
    """Bench helper 22.36."""
    return x * 23 + 36 + 15

def fn_22_37(x: int) -> int:
    """Bench helper 22.37."""
    return x * 23 + 37 + 15

def fn_22_38(x: int) -> int:
    """Bench helper 22.38."""
    return x * 23 + 38 + 15

def fn_22_39(x: int) -> int:
    """Bench helper 22.39."""
    return x * 23 + 39 + 15

class Box_22:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_22_{k % 40}(k)
        return total

