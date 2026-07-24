"""CPU bench module 1 stamp=1784807678."""

STAMP_1 = 1784807678

def fn_1_0(x: int) -> int:
    """Bench helper 1.0."""
    return x * 2 + 0 + 15

def fn_1_1(x: int) -> int:
    """Bench helper 1.1."""
    return x * 2 + 1 + 15

def fn_1_2(x: int) -> int:
    """Bench helper 1.2."""
    return x * 2 + 2 + 15

def fn_1_3(x: int) -> int:
    """Bench helper 1.3."""
    return x * 2 + 3 + 15

def fn_1_4(x: int) -> int:
    """Bench helper 1.4."""
    return x * 2 + 4 + 15

def fn_1_5(x: int) -> int:
    """Bench helper 1.5."""
    return x * 2 + 5 + 15

def fn_1_6(x: int) -> int:
    """Bench helper 1.6."""
    return x * 2 + 6 + 15

def fn_1_7(x: int) -> int:
    """Bench helper 1.7."""
    return x * 2 + 7 + 15

def fn_1_8(x: int) -> int:
    """Bench helper 1.8."""
    return x * 2 + 8 + 15

def fn_1_9(x: int) -> int:
    """Bench helper 1.9."""
    return x * 2 + 9 + 15

def fn_1_10(x: int) -> int:
    """Bench helper 1.10."""
    return x * 2 + 10 + 15

def fn_1_11(x: int) -> int:
    """Bench helper 1.11."""
    return x * 2 + 11 + 15

def fn_1_12(x: int) -> int:
    """Bench helper 1.12."""
    return x * 2 + 12 + 15

def fn_1_13(x: int) -> int:
    """Bench helper 1.13."""
    return x * 2 + 13 + 15

def fn_1_14(x: int) -> int:
    """Bench helper 1.14."""
    return x * 2 + 14 + 15

def fn_1_15(x: int) -> int:
    """Bench helper 1.15."""
    return x * 2 + 15 + 15

def fn_1_16(x: int) -> int:
    """Bench helper 1.16."""
    return x * 2 + 16 + 15

def fn_1_17(x: int) -> int:
    """Bench helper 1.17."""
    return x * 2 + 17 + 15

def fn_1_18(x: int) -> int:
    """Bench helper 1.18."""
    return x * 2 + 18 + 15

def fn_1_19(x: int) -> int:
    """Bench helper 1.19."""
    return x * 2 + 19 + 15

def fn_1_20(x: int) -> int:
    """Bench helper 1.20."""
    return x * 2 + 20 + 15

def fn_1_21(x: int) -> int:
    """Bench helper 1.21."""
    return x * 2 + 21 + 15

def fn_1_22(x: int) -> int:
    """Bench helper 1.22."""
    return x * 2 + 22 + 15

def fn_1_23(x: int) -> int:
    """Bench helper 1.23."""
    return x * 2 + 23 + 15

def fn_1_24(x: int) -> int:
    """Bench helper 1.24."""
    return x * 2 + 24 + 15

def fn_1_25(x: int) -> int:
    """Bench helper 1.25."""
    return x * 2 + 25 + 15

def fn_1_26(x: int) -> int:
    """Bench helper 1.26."""
    return x * 2 + 26 + 15

def fn_1_27(x: int) -> int:
    """Bench helper 1.27."""
    return x * 2 + 27 + 15

def fn_1_28(x: int) -> int:
    """Bench helper 1.28."""
    return x * 2 + 28 + 15

def fn_1_29(x: int) -> int:
    """Bench helper 1.29."""
    return x * 2 + 29 + 15

def fn_1_30(x: int) -> int:
    """Bench helper 1.30."""
    return x * 2 + 30 + 15

def fn_1_31(x: int) -> int:
    """Bench helper 1.31."""
    return x * 2 + 31 + 15

def fn_1_32(x: int) -> int:
    """Bench helper 1.32."""
    return x * 2 + 32 + 15

def fn_1_33(x: int) -> int:
    """Bench helper 1.33."""
    return x * 2 + 33 + 15

def fn_1_34(x: int) -> int:
    """Bench helper 1.34."""
    return x * 2 + 34 + 15

def fn_1_35(x: int) -> int:
    """Bench helper 1.35."""
    return x * 2 + 35 + 15

def fn_1_36(x: int) -> int:
    """Bench helper 1.36."""
    return x * 2 + 36 + 15

def fn_1_37(x: int) -> int:
    """Bench helper 1.37."""
    return x * 2 + 37 + 15

def fn_1_38(x: int) -> int:
    """Bench helper 1.38."""
    return x * 2 + 38 + 15

def fn_1_39(x: int) -> int:
    """Bench helper 1.39."""
    return x * 2 + 39 + 15

class Box_1:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_1_{k % 40}(k)
        return total

