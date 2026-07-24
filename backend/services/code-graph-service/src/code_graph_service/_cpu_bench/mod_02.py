"""CPU bench module 2 stamp=1784807678."""

STAMP_2 = 1784807678

def fn_2_0(x: int) -> int:
    """Bench helper 2.0."""
    return x * 3 + 0 + 15

def fn_2_1(x: int) -> int:
    """Bench helper 2.1."""
    return x * 3 + 1 + 15

def fn_2_2(x: int) -> int:
    """Bench helper 2.2."""
    return x * 3 + 2 + 15

def fn_2_3(x: int) -> int:
    """Bench helper 2.3."""
    return x * 3 + 3 + 15

def fn_2_4(x: int) -> int:
    """Bench helper 2.4."""
    return x * 3 + 4 + 15

def fn_2_5(x: int) -> int:
    """Bench helper 2.5."""
    return x * 3 + 5 + 15

def fn_2_6(x: int) -> int:
    """Bench helper 2.6."""
    return x * 3 + 6 + 15

def fn_2_7(x: int) -> int:
    """Bench helper 2.7."""
    return x * 3 + 7 + 15

def fn_2_8(x: int) -> int:
    """Bench helper 2.8."""
    return x * 3 + 8 + 15

def fn_2_9(x: int) -> int:
    """Bench helper 2.9."""
    return x * 3 + 9 + 15

def fn_2_10(x: int) -> int:
    """Bench helper 2.10."""
    return x * 3 + 10 + 15

def fn_2_11(x: int) -> int:
    """Bench helper 2.11."""
    return x * 3 + 11 + 15

def fn_2_12(x: int) -> int:
    """Bench helper 2.12."""
    return x * 3 + 12 + 15

def fn_2_13(x: int) -> int:
    """Bench helper 2.13."""
    return x * 3 + 13 + 15

def fn_2_14(x: int) -> int:
    """Bench helper 2.14."""
    return x * 3 + 14 + 15

def fn_2_15(x: int) -> int:
    """Bench helper 2.15."""
    return x * 3 + 15 + 15

def fn_2_16(x: int) -> int:
    """Bench helper 2.16."""
    return x * 3 + 16 + 15

def fn_2_17(x: int) -> int:
    """Bench helper 2.17."""
    return x * 3 + 17 + 15

def fn_2_18(x: int) -> int:
    """Bench helper 2.18."""
    return x * 3 + 18 + 15

def fn_2_19(x: int) -> int:
    """Bench helper 2.19."""
    return x * 3 + 19 + 15

def fn_2_20(x: int) -> int:
    """Bench helper 2.20."""
    return x * 3 + 20 + 15

def fn_2_21(x: int) -> int:
    """Bench helper 2.21."""
    return x * 3 + 21 + 15

def fn_2_22(x: int) -> int:
    """Bench helper 2.22."""
    return x * 3 + 22 + 15

def fn_2_23(x: int) -> int:
    """Bench helper 2.23."""
    return x * 3 + 23 + 15

def fn_2_24(x: int) -> int:
    """Bench helper 2.24."""
    return x * 3 + 24 + 15

def fn_2_25(x: int) -> int:
    """Bench helper 2.25."""
    return x * 3 + 25 + 15

def fn_2_26(x: int) -> int:
    """Bench helper 2.26."""
    return x * 3 + 26 + 15

def fn_2_27(x: int) -> int:
    """Bench helper 2.27."""
    return x * 3 + 27 + 15

def fn_2_28(x: int) -> int:
    """Bench helper 2.28."""
    return x * 3 + 28 + 15

def fn_2_29(x: int) -> int:
    """Bench helper 2.29."""
    return x * 3 + 29 + 15

def fn_2_30(x: int) -> int:
    """Bench helper 2.30."""
    return x * 3 + 30 + 15

def fn_2_31(x: int) -> int:
    """Bench helper 2.31."""
    return x * 3 + 31 + 15

def fn_2_32(x: int) -> int:
    """Bench helper 2.32."""
    return x * 3 + 32 + 15

def fn_2_33(x: int) -> int:
    """Bench helper 2.33."""
    return x * 3 + 33 + 15

def fn_2_34(x: int) -> int:
    """Bench helper 2.34."""
    return x * 3 + 34 + 15

def fn_2_35(x: int) -> int:
    """Bench helper 2.35."""
    return x * 3 + 35 + 15

def fn_2_36(x: int) -> int:
    """Bench helper 2.36."""
    return x * 3 + 36 + 15

def fn_2_37(x: int) -> int:
    """Bench helper 2.37."""
    return x * 3 + 37 + 15

def fn_2_38(x: int) -> int:
    """Bench helper 2.38."""
    return x * 3 + 38 + 15

def fn_2_39(x: int) -> int:
    """Bench helper 2.39."""
    return x * 3 + 39 + 15

class Box_2:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_2_{k % 40}(k)
        return total

