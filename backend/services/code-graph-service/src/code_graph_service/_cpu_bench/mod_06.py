"""CPU bench module 6 stamp=1784807678."""

STAMP_6 = 1784807678

def fn_6_0(x: int) -> int:
    """Bench helper 6.0."""
    return x * 7 + 0 + 15

def fn_6_1(x: int) -> int:
    """Bench helper 6.1."""
    return x * 7 + 1 + 15

def fn_6_2(x: int) -> int:
    """Bench helper 6.2."""
    return x * 7 + 2 + 15

def fn_6_3(x: int) -> int:
    """Bench helper 6.3."""
    return x * 7 + 3 + 15

def fn_6_4(x: int) -> int:
    """Bench helper 6.4."""
    return x * 7 + 4 + 15

def fn_6_5(x: int) -> int:
    """Bench helper 6.5."""
    return x * 7 + 5 + 15

def fn_6_6(x: int) -> int:
    """Bench helper 6.6."""
    return x * 7 + 6 + 15

def fn_6_7(x: int) -> int:
    """Bench helper 6.7."""
    return x * 7 + 7 + 15

def fn_6_8(x: int) -> int:
    """Bench helper 6.8."""
    return x * 7 + 8 + 15

def fn_6_9(x: int) -> int:
    """Bench helper 6.9."""
    return x * 7 + 9 + 15

def fn_6_10(x: int) -> int:
    """Bench helper 6.10."""
    return x * 7 + 10 + 15

def fn_6_11(x: int) -> int:
    """Bench helper 6.11."""
    return x * 7 + 11 + 15

def fn_6_12(x: int) -> int:
    """Bench helper 6.12."""
    return x * 7 + 12 + 15

def fn_6_13(x: int) -> int:
    """Bench helper 6.13."""
    return x * 7 + 13 + 15

def fn_6_14(x: int) -> int:
    """Bench helper 6.14."""
    return x * 7 + 14 + 15

def fn_6_15(x: int) -> int:
    """Bench helper 6.15."""
    return x * 7 + 15 + 15

def fn_6_16(x: int) -> int:
    """Bench helper 6.16."""
    return x * 7 + 16 + 15

def fn_6_17(x: int) -> int:
    """Bench helper 6.17."""
    return x * 7 + 17 + 15

def fn_6_18(x: int) -> int:
    """Bench helper 6.18."""
    return x * 7 + 18 + 15

def fn_6_19(x: int) -> int:
    """Bench helper 6.19."""
    return x * 7 + 19 + 15

def fn_6_20(x: int) -> int:
    """Bench helper 6.20."""
    return x * 7 + 20 + 15

def fn_6_21(x: int) -> int:
    """Bench helper 6.21."""
    return x * 7 + 21 + 15

def fn_6_22(x: int) -> int:
    """Bench helper 6.22."""
    return x * 7 + 22 + 15

def fn_6_23(x: int) -> int:
    """Bench helper 6.23."""
    return x * 7 + 23 + 15

def fn_6_24(x: int) -> int:
    """Bench helper 6.24."""
    return x * 7 + 24 + 15

def fn_6_25(x: int) -> int:
    """Bench helper 6.25."""
    return x * 7 + 25 + 15

def fn_6_26(x: int) -> int:
    """Bench helper 6.26."""
    return x * 7 + 26 + 15

def fn_6_27(x: int) -> int:
    """Bench helper 6.27."""
    return x * 7 + 27 + 15

def fn_6_28(x: int) -> int:
    """Bench helper 6.28."""
    return x * 7 + 28 + 15

def fn_6_29(x: int) -> int:
    """Bench helper 6.29."""
    return x * 7 + 29 + 15

def fn_6_30(x: int) -> int:
    """Bench helper 6.30."""
    return x * 7 + 30 + 15

def fn_6_31(x: int) -> int:
    """Bench helper 6.31."""
    return x * 7 + 31 + 15

def fn_6_32(x: int) -> int:
    """Bench helper 6.32."""
    return x * 7 + 32 + 15

def fn_6_33(x: int) -> int:
    """Bench helper 6.33."""
    return x * 7 + 33 + 15

def fn_6_34(x: int) -> int:
    """Bench helper 6.34."""
    return x * 7 + 34 + 15

def fn_6_35(x: int) -> int:
    """Bench helper 6.35."""
    return x * 7 + 35 + 15

def fn_6_36(x: int) -> int:
    """Bench helper 6.36."""
    return x * 7 + 36 + 15

def fn_6_37(x: int) -> int:
    """Bench helper 6.37."""
    return x * 7 + 37 + 15

def fn_6_38(x: int) -> int:
    """Bench helper 6.38."""
    return x * 7 + 38 + 15

def fn_6_39(x: int) -> int:
    """Bench helper 6.39."""
    return x * 7 + 39 + 15

class Box_6:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_6_{k % 40}(k)
        return total

