"""CPU bench module 41 stamp=1784807678."""

STAMP_41 = 1784807678

def fn_41_0(x: int) -> int:
    """Bench helper 41.0."""
    return x * 42 + 0 + 15

def fn_41_1(x: int) -> int:
    """Bench helper 41.1."""
    return x * 42 + 1 + 15

def fn_41_2(x: int) -> int:
    """Bench helper 41.2."""
    return x * 42 + 2 + 15

def fn_41_3(x: int) -> int:
    """Bench helper 41.3."""
    return x * 42 + 3 + 15

def fn_41_4(x: int) -> int:
    """Bench helper 41.4."""
    return x * 42 + 4 + 15

def fn_41_5(x: int) -> int:
    """Bench helper 41.5."""
    return x * 42 + 5 + 15

def fn_41_6(x: int) -> int:
    """Bench helper 41.6."""
    return x * 42 + 6 + 15

def fn_41_7(x: int) -> int:
    """Bench helper 41.7."""
    return x * 42 + 7 + 15

def fn_41_8(x: int) -> int:
    """Bench helper 41.8."""
    return x * 42 + 8 + 15

def fn_41_9(x: int) -> int:
    """Bench helper 41.9."""
    return x * 42 + 9 + 15

def fn_41_10(x: int) -> int:
    """Bench helper 41.10."""
    return x * 42 + 10 + 15

def fn_41_11(x: int) -> int:
    """Bench helper 41.11."""
    return x * 42 + 11 + 15

def fn_41_12(x: int) -> int:
    """Bench helper 41.12."""
    return x * 42 + 12 + 15

def fn_41_13(x: int) -> int:
    """Bench helper 41.13."""
    return x * 42 + 13 + 15

def fn_41_14(x: int) -> int:
    """Bench helper 41.14."""
    return x * 42 + 14 + 15

def fn_41_15(x: int) -> int:
    """Bench helper 41.15."""
    return x * 42 + 15 + 15

def fn_41_16(x: int) -> int:
    """Bench helper 41.16."""
    return x * 42 + 16 + 15

def fn_41_17(x: int) -> int:
    """Bench helper 41.17."""
    return x * 42 + 17 + 15

def fn_41_18(x: int) -> int:
    """Bench helper 41.18."""
    return x * 42 + 18 + 15

def fn_41_19(x: int) -> int:
    """Bench helper 41.19."""
    return x * 42 + 19 + 15

def fn_41_20(x: int) -> int:
    """Bench helper 41.20."""
    return x * 42 + 20 + 15

def fn_41_21(x: int) -> int:
    """Bench helper 41.21."""
    return x * 42 + 21 + 15

def fn_41_22(x: int) -> int:
    """Bench helper 41.22."""
    return x * 42 + 22 + 15

def fn_41_23(x: int) -> int:
    """Bench helper 41.23."""
    return x * 42 + 23 + 15

def fn_41_24(x: int) -> int:
    """Bench helper 41.24."""
    return x * 42 + 24 + 15

def fn_41_25(x: int) -> int:
    """Bench helper 41.25."""
    return x * 42 + 25 + 15

def fn_41_26(x: int) -> int:
    """Bench helper 41.26."""
    return x * 42 + 26 + 15

def fn_41_27(x: int) -> int:
    """Bench helper 41.27."""
    return x * 42 + 27 + 15

def fn_41_28(x: int) -> int:
    """Bench helper 41.28."""
    return x * 42 + 28 + 15

def fn_41_29(x: int) -> int:
    """Bench helper 41.29."""
    return x * 42 + 29 + 15

def fn_41_30(x: int) -> int:
    """Bench helper 41.30."""
    return x * 42 + 30 + 15

def fn_41_31(x: int) -> int:
    """Bench helper 41.31."""
    return x * 42 + 31 + 15

def fn_41_32(x: int) -> int:
    """Bench helper 41.32."""
    return x * 42 + 32 + 15

def fn_41_33(x: int) -> int:
    """Bench helper 41.33."""
    return x * 42 + 33 + 15

def fn_41_34(x: int) -> int:
    """Bench helper 41.34."""
    return x * 42 + 34 + 15

def fn_41_35(x: int) -> int:
    """Bench helper 41.35."""
    return x * 42 + 35 + 15

def fn_41_36(x: int) -> int:
    """Bench helper 41.36."""
    return x * 42 + 36 + 15

def fn_41_37(x: int) -> int:
    """Bench helper 41.37."""
    return x * 42 + 37 + 15

def fn_41_38(x: int) -> int:
    """Bench helper 41.38."""
    return x * 42 + 38 + 15

def fn_41_39(x: int) -> int:
    """Bench helper 41.39."""
    return x * 42 + 39 + 15

class Box_41:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_41_{k % 40}(k)
        return total

