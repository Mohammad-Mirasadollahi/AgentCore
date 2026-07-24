"""CPU bench module 14 stamp=1784807678."""

STAMP_14 = 1784807678

def fn_14_0(x: int) -> int:
    """Bench helper 14.0."""
    return x * 15 + 0 + 15

def fn_14_1(x: int) -> int:
    """Bench helper 14.1."""
    return x * 15 + 1 + 15

def fn_14_2(x: int) -> int:
    """Bench helper 14.2."""
    return x * 15 + 2 + 15

def fn_14_3(x: int) -> int:
    """Bench helper 14.3."""
    return x * 15 + 3 + 15

def fn_14_4(x: int) -> int:
    """Bench helper 14.4."""
    return x * 15 + 4 + 15

def fn_14_5(x: int) -> int:
    """Bench helper 14.5."""
    return x * 15 + 5 + 15

def fn_14_6(x: int) -> int:
    """Bench helper 14.6."""
    return x * 15 + 6 + 15

def fn_14_7(x: int) -> int:
    """Bench helper 14.7."""
    return x * 15 + 7 + 15

def fn_14_8(x: int) -> int:
    """Bench helper 14.8."""
    return x * 15 + 8 + 15

def fn_14_9(x: int) -> int:
    """Bench helper 14.9."""
    return x * 15 + 9 + 15

def fn_14_10(x: int) -> int:
    """Bench helper 14.10."""
    return x * 15 + 10 + 15

def fn_14_11(x: int) -> int:
    """Bench helper 14.11."""
    return x * 15 + 11 + 15

def fn_14_12(x: int) -> int:
    """Bench helper 14.12."""
    return x * 15 + 12 + 15

def fn_14_13(x: int) -> int:
    """Bench helper 14.13."""
    return x * 15 + 13 + 15

def fn_14_14(x: int) -> int:
    """Bench helper 14.14."""
    return x * 15 + 14 + 15

def fn_14_15(x: int) -> int:
    """Bench helper 14.15."""
    return x * 15 + 15 + 15

def fn_14_16(x: int) -> int:
    """Bench helper 14.16."""
    return x * 15 + 16 + 15

def fn_14_17(x: int) -> int:
    """Bench helper 14.17."""
    return x * 15 + 17 + 15

def fn_14_18(x: int) -> int:
    """Bench helper 14.18."""
    return x * 15 + 18 + 15

def fn_14_19(x: int) -> int:
    """Bench helper 14.19."""
    return x * 15 + 19 + 15

def fn_14_20(x: int) -> int:
    """Bench helper 14.20."""
    return x * 15 + 20 + 15

def fn_14_21(x: int) -> int:
    """Bench helper 14.21."""
    return x * 15 + 21 + 15

def fn_14_22(x: int) -> int:
    """Bench helper 14.22."""
    return x * 15 + 22 + 15

def fn_14_23(x: int) -> int:
    """Bench helper 14.23."""
    return x * 15 + 23 + 15

def fn_14_24(x: int) -> int:
    """Bench helper 14.24."""
    return x * 15 + 24 + 15

def fn_14_25(x: int) -> int:
    """Bench helper 14.25."""
    return x * 15 + 25 + 15

def fn_14_26(x: int) -> int:
    """Bench helper 14.26."""
    return x * 15 + 26 + 15

def fn_14_27(x: int) -> int:
    """Bench helper 14.27."""
    return x * 15 + 27 + 15

def fn_14_28(x: int) -> int:
    """Bench helper 14.28."""
    return x * 15 + 28 + 15

def fn_14_29(x: int) -> int:
    """Bench helper 14.29."""
    return x * 15 + 29 + 15

def fn_14_30(x: int) -> int:
    """Bench helper 14.30."""
    return x * 15 + 30 + 15

def fn_14_31(x: int) -> int:
    """Bench helper 14.31."""
    return x * 15 + 31 + 15

def fn_14_32(x: int) -> int:
    """Bench helper 14.32."""
    return x * 15 + 32 + 15

def fn_14_33(x: int) -> int:
    """Bench helper 14.33."""
    return x * 15 + 33 + 15

def fn_14_34(x: int) -> int:
    """Bench helper 14.34."""
    return x * 15 + 34 + 15

def fn_14_35(x: int) -> int:
    """Bench helper 14.35."""
    return x * 15 + 35 + 15

def fn_14_36(x: int) -> int:
    """Bench helper 14.36."""
    return x * 15 + 36 + 15

def fn_14_37(x: int) -> int:
    """Bench helper 14.37."""
    return x * 15 + 37 + 15

def fn_14_38(x: int) -> int:
    """Bench helper 14.38."""
    return x * 15 + 38 + 15

def fn_14_39(x: int) -> int:
    """Bench helper 14.39."""
    return x * 15 + 39 + 15

class Box_14:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_14_{k % 40}(k)
        return total

