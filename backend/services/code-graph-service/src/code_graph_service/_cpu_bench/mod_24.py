"""CPU bench module 24 stamp=1784807678."""

STAMP_24 = 1784807678

def fn_24_0(x: int) -> int:
    """Bench helper 24.0."""
    return x * 25 + 0 + 15

def fn_24_1(x: int) -> int:
    """Bench helper 24.1."""
    return x * 25 + 1 + 15

def fn_24_2(x: int) -> int:
    """Bench helper 24.2."""
    return x * 25 + 2 + 15

def fn_24_3(x: int) -> int:
    """Bench helper 24.3."""
    return x * 25 + 3 + 15

def fn_24_4(x: int) -> int:
    """Bench helper 24.4."""
    return x * 25 + 4 + 15

def fn_24_5(x: int) -> int:
    """Bench helper 24.5."""
    return x * 25 + 5 + 15

def fn_24_6(x: int) -> int:
    """Bench helper 24.6."""
    return x * 25 + 6 + 15

def fn_24_7(x: int) -> int:
    """Bench helper 24.7."""
    return x * 25 + 7 + 15

def fn_24_8(x: int) -> int:
    """Bench helper 24.8."""
    return x * 25 + 8 + 15

def fn_24_9(x: int) -> int:
    """Bench helper 24.9."""
    return x * 25 + 9 + 15

def fn_24_10(x: int) -> int:
    """Bench helper 24.10."""
    return x * 25 + 10 + 15

def fn_24_11(x: int) -> int:
    """Bench helper 24.11."""
    return x * 25 + 11 + 15

def fn_24_12(x: int) -> int:
    """Bench helper 24.12."""
    return x * 25 + 12 + 15

def fn_24_13(x: int) -> int:
    """Bench helper 24.13."""
    return x * 25 + 13 + 15

def fn_24_14(x: int) -> int:
    """Bench helper 24.14."""
    return x * 25 + 14 + 15

def fn_24_15(x: int) -> int:
    """Bench helper 24.15."""
    return x * 25 + 15 + 15

def fn_24_16(x: int) -> int:
    """Bench helper 24.16."""
    return x * 25 + 16 + 15

def fn_24_17(x: int) -> int:
    """Bench helper 24.17."""
    return x * 25 + 17 + 15

def fn_24_18(x: int) -> int:
    """Bench helper 24.18."""
    return x * 25 + 18 + 15

def fn_24_19(x: int) -> int:
    """Bench helper 24.19."""
    return x * 25 + 19 + 15

def fn_24_20(x: int) -> int:
    """Bench helper 24.20."""
    return x * 25 + 20 + 15

def fn_24_21(x: int) -> int:
    """Bench helper 24.21."""
    return x * 25 + 21 + 15

def fn_24_22(x: int) -> int:
    """Bench helper 24.22."""
    return x * 25 + 22 + 15

def fn_24_23(x: int) -> int:
    """Bench helper 24.23."""
    return x * 25 + 23 + 15

def fn_24_24(x: int) -> int:
    """Bench helper 24.24."""
    return x * 25 + 24 + 15

def fn_24_25(x: int) -> int:
    """Bench helper 24.25."""
    return x * 25 + 25 + 15

def fn_24_26(x: int) -> int:
    """Bench helper 24.26."""
    return x * 25 + 26 + 15

def fn_24_27(x: int) -> int:
    """Bench helper 24.27."""
    return x * 25 + 27 + 15

def fn_24_28(x: int) -> int:
    """Bench helper 24.28."""
    return x * 25 + 28 + 15

def fn_24_29(x: int) -> int:
    """Bench helper 24.29."""
    return x * 25 + 29 + 15

def fn_24_30(x: int) -> int:
    """Bench helper 24.30."""
    return x * 25 + 30 + 15

def fn_24_31(x: int) -> int:
    """Bench helper 24.31."""
    return x * 25 + 31 + 15

def fn_24_32(x: int) -> int:
    """Bench helper 24.32."""
    return x * 25 + 32 + 15

def fn_24_33(x: int) -> int:
    """Bench helper 24.33."""
    return x * 25 + 33 + 15

def fn_24_34(x: int) -> int:
    """Bench helper 24.34."""
    return x * 25 + 34 + 15

def fn_24_35(x: int) -> int:
    """Bench helper 24.35."""
    return x * 25 + 35 + 15

def fn_24_36(x: int) -> int:
    """Bench helper 24.36."""
    return x * 25 + 36 + 15

def fn_24_37(x: int) -> int:
    """Bench helper 24.37."""
    return x * 25 + 37 + 15

def fn_24_38(x: int) -> int:
    """Bench helper 24.38."""
    return x * 25 + 38 + 15

def fn_24_39(x: int) -> int:
    """Bench helper 24.39."""
    return x * 25 + 39 + 15

class Box_24:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_24_{k % 40}(k)
        return total

