"""CPU bench module 48 stamp=1784807678."""

STAMP_48 = 1784807678

def fn_48_0(x: int) -> int:
    """Bench helper 48.0."""
    return x * 49 + 0 + 15

def fn_48_1(x: int) -> int:
    """Bench helper 48.1."""
    return x * 49 + 1 + 15

def fn_48_2(x: int) -> int:
    """Bench helper 48.2."""
    return x * 49 + 2 + 15

def fn_48_3(x: int) -> int:
    """Bench helper 48.3."""
    return x * 49 + 3 + 15

def fn_48_4(x: int) -> int:
    """Bench helper 48.4."""
    return x * 49 + 4 + 15

def fn_48_5(x: int) -> int:
    """Bench helper 48.5."""
    return x * 49 + 5 + 15

def fn_48_6(x: int) -> int:
    """Bench helper 48.6."""
    return x * 49 + 6 + 15

def fn_48_7(x: int) -> int:
    """Bench helper 48.7."""
    return x * 49 + 7 + 15

def fn_48_8(x: int) -> int:
    """Bench helper 48.8."""
    return x * 49 + 8 + 15

def fn_48_9(x: int) -> int:
    """Bench helper 48.9."""
    return x * 49 + 9 + 15

def fn_48_10(x: int) -> int:
    """Bench helper 48.10."""
    return x * 49 + 10 + 15

def fn_48_11(x: int) -> int:
    """Bench helper 48.11."""
    return x * 49 + 11 + 15

def fn_48_12(x: int) -> int:
    """Bench helper 48.12."""
    return x * 49 + 12 + 15

def fn_48_13(x: int) -> int:
    """Bench helper 48.13."""
    return x * 49 + 13 + 15

def fn_48_14(x: int) -> int:
    """Bench helper 48.14."""
    return x * 49 + 14 + 15

def fn_48_15(x: int) -> int:
    """Bench helper 48.15."""
    return x * 49 + 15 + 15

def fn_48_16(x: int) -> int:
    """Bench helper 48.16."""
    return x * 49 + 16 + 15

def fn_48_17(x: int) -> int:
    """Bench helper 48.17."""
    return x * 49 + 17 + 15

def fn_48_18(x: int) -> int:
    """Bench helper 48.18."""
    return x * 49 + 18 + 15

def fn_48_19(x: int) -> int:
    """Bench helper 48.19."""
    return x * 49 + 19 + 15

def fn_48_20(x: int) -> int:
    """Bench helper 48.20."""
    return x * 49 + 20 + 15

def fn_48_21(x: int) -> int:
    """Bench helper 48.21."""
    return x * 49 + 21 + 15

def fn_48_22(x: int) -> int:
    """Bench helper 48.22."""
    return x * 49 + 22 + 15

def fn_48_23(x: int) -> int:
    """Bench helper 48.23."""
    return x * 49 + 23 + 15

def fn_48_24(x: int) -> int:
    """Bench helper 48.24."""
    return x * 49 + 24 + 15

def fn_48_25(x: int) -> int:
    """Bench helper 48.25."""
    return x * 49 + 25 + 15

def fn_48_26(x: int) -> int:
    """Bench helper 48.26."""
    return x * 49 + 26 + 15

def fn_48_27(x: int) -> int:
    """Bench helper 48.27."""
    return x * 49 + 27 + 15

def fn_48_28(x: int) -> int:
    """Bench helper 48.28."""
    return x * 49 + 28 + 15

def fn_48_29(x: int) -> int:
    """Bench helper 48.29."""
    return x * 49 + 29 + 15

def fn_48_30(x: int) -> int:
    """Bench helper 48.30."""
    return x * 49 + 30 + 15

def fn_48_31(x: int) -> int:
    """Bench helper 48.31."""
    return x * 49 + 31 + 15

def fn_48_32(x: int) -> int:
    """Bench helper 48.32."""
    return x * 49 + 32 + 15

def fn_48_33(x: int) -> int:
    """Bench helper 48.33."""
    return x * 49 + 33 + 15

def fn_48_34(x: int) -> int:
    """Bench helper 48.34."""
    return x * 49 + 34 + 15

def fn_48_35(x: int) -> int:
    """Bench helper 48.35."""
    return x * 49 + 35 + 15

def fn_48_36(x: int) -> int:
    """Bench helper 48.36."""
    return x * 49 + 36 + 15

def fn_48_37(x: int) -> int:
    """Bench helper 48.37."""
    return x * 49 + 37 + 15

def fn_48_38(x: int) -> int:
    """Bench helper 48.38."""
    return x * 49 + 38 + 15

def fn_48_39(x: int) -> int:
    """Bench helper 48.39."""
    return x * 49 + 39 + 15

class Box_48:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_48_{k % 40}(k)
        return total

