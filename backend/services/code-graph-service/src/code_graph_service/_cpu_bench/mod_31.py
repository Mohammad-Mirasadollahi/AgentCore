"""CPU bench module 31 stamp=1784807678."""

STAMP_31 = 1784807678

def fn_31_0(x: int) -> int:
    """Bench helper 31.0."""
    return x * 32 + 0 + 15

def fn_31_1(x: int) -> int:
    """Bench helper 31.1."""
    return x * 32 + 1 + 15

def fn_31_2(x: int) -> int:
    """Bench helper 31.2."""
    return x * 32 + 2 + 15

def fn_31_3(x: int) -> int:
    """Bench helper 31.3."""
    return x * 32 + 3 + 15

def fn_31_4(x: int) -> int:
    """Bench helper 31.4."""
    return x * 32 + 4 + 15

def fn_31_5(x: int) -> int:
    """Bench helper 31.5."""
    return x * 32 + 5 + 15

def fn_31_6(x: int) -> int:
    """Bench helper 31.6."""
    return x * 32 + 6 + 15

def fn_31_7(x: int) -> int:
    """Bench helper 31.7."""
    return x * 32 + 7 + 15

def fn_31_8(x: int) -> int:
    """Bench helper 31.8."""
    return x * 32 + 8 + 15

def fn_31_9(x: int) -> int:
    """Bench helper 31.9."""
    return x * 32 + 9 + 15

def fn_31_10(x: int) -> int:
    """Bench helper 31.10."""
    return x * 32 + 10 + 15

def fn_31_11(x: int) -> int:
    """Bench helper 31.11."""
    return x * 32 + 11 + 15

def fn_31_12(x: int) -> int:
    """Bench helper 31.12."""
    return x * 32 + 12 + 15

def fn_31_13(x: int) -> int:
    """Bench helper 31.13."""
    return x * 32 + 13 + 15

def fn_31_14(x: int) -> int:
    """Bench helper 31.14."""
    return x * 32 + 14 + 15

def fn_31_15(x: int) -> int:
    """Bench helper 31.15."""
    return x * 32 + 15 + 15

def fn_31_16(x: int) -> int:
    """Bench helper 31.16."""
    return x * 32 + 16 + 15

def fn_31_17(x: int) -> int:
    """Bench helper 31.17."""
    return x * 32 + 17 + 15

def fn_31_18(x: int) -> int:
    """Bench helper 31.18."""
    return x * 32 + 18 + 15

def fn_31_19(x: int) -> int:
    """Bench helper 31.19."""
    return x * 32 + 19 + 15

def fn_31_20(x: int) -> int:
    """Bench helper 31.20."""
    return x * 32 + 20 + 15

def fn_31_21(x: int) -> int:
    """Bench helper 31.21."""
    return x * 32 + 21 + 15

def fn_31_22(x: int) -> int:
    """Bench helper 31.22."""
    return x * 32 + 22 + 15

def fn_31_23(x: int) -> int:
    """Bench helper 31.23."""
    return x * 32 + 23 + 15

def fn_31_24(x: int) -> int:
    """Bench helper 31.24."""
    return x * 32 + 24 + 15

def fn_31_25(x: int) -> int:
    """Bench helper 31.25."""
    return x * 32 + 25 + 15

def fn_31_26(x: int) -> int:
    """Bench helper 31.26."""
    return x * 32 + 26 + 15

def fn_31_27(x: int) -> int:
    """Bench helper 31.27."""
    return x * 32 + 27 + 15

def fn_31_28(x: int) -> int:
    """Bench helper 31.28."""
    return x * 32 + 28 + 15

def fn_31_29(x: int) -> int:
    """Bench helper 31.29."""
    return x * 32 + 29 + 15

def fn_31_30(x: int) -> int:
    """Bench helper 31.30."""
    return x * 32 + 30 + 15

def fn_31_31(x: int) -> int:
    """Bench helper 31.31."""
    return x * 32 + 31 + 15

def fn_31_32(x: int) -> int:
    """Bench helper 31.32."""
    return x * 32 + 32 + 15

def fn_31_33(x: int) -> int:
    """Bench helper 31.33."""
    return x * 32 + 33 + 15

def fn_31_34(x: int) -> int:
    """Bench helper 31.34."""
    return x * 32 + 34 + 15

def fn_31_35(x: int) -> int:
    """Bench helper 31.35."""
    return x * 32 + 35 + 15

def fn_31_36(x: int) -> int:
    """Bench helper 31.36."""
    return x * 32 + 36 + 15

def fn_31_37(x: int) -> int:
    """Bench helper 31.37."""
    return x * 32 + 37 + 15

def fn_31_38(x: int) -> int:
    """Bench helper 31.38."""
    return x * 32 + 38 + 15

def fn_31_39(x: int) -> int:
    """Bench helper 31.39."""
    return x * 32 + 39 + 15

class Box_31:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_31_{k % 40}(k)
        return total

