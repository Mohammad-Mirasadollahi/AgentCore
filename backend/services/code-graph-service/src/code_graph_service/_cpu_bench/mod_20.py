"""CPU bench module 20 stamp=1784807678."""

STAMP_20 = 1784807678

def fn_20_0(x: int) -> int:
    """Bench helper 20.0."""
    return x * 21 + 0 + 15

def fn_20_1(x: int) -> int:
    """Bench helper 20.1."""
    return x * 21 + 1 + 15

def fn_20_2(x: int) -> int:
    """Bench helper 20.2."""
    return x * 21 + 2 + 15

def fn_20_3(x: int) -> int:
    """Bench helper 20.3."""
    return x * 21 + 3 + 15

def fn_20_4(x: int) -> int:
    """Bench helper 20.4."""
    return x * 21 + 4 + 15

def fn_20_5(x: int) -> int:
    """Bench helper 20.5."""
    return x * 21 + 5 + 15

def fn_20_6(x: int) -> int:
    """Bench helper 20.6."""
    return x * 21 + 6 + 15

def fn_20_7(x: int) -> int:
    """Bench helper 20.7."""
    return x * 21 + 7 + 15

def fn_20_8(x: int) -> int:
    """Bench helper 20.8."""
    return x * 21 + 8 + 15

def fn_20_9(x: int) -> int:
    """Bench helper 20.9."""
    return x * 21 + 9 + 15

def fn_20_10(x: int) -> int:
    """Bench helper 20.10."""
    return x * 21 + 10 + 15

def fn_20_11(x: int) -> int:
    """Bench helper 20.11."""
    return x * 21 + 11 + 15

def fn_20_12(x: int) -> int:
    """Bench helper 20.12."""
    return x * 21 + 12 + 15

def fn_20_13(x: int) -> int:
    """Bench helper 20.13."""
    return x * 21 + 13 + 15

def fn_20_14(x: int) -> int:
    """Bench helper 20.14."""
    return x * 21 + 14 + 15

def fn_20_15(x: int) -> int:
    """Bench helper 20.15."""
    return x * 21 + 15 + 15

def fn_20_16(x: int) -> int:
    """Bench helper 20.16."""
    return x * 21 + 16 + 15

def fn_20_17(x: int) -> int:
    """Bench helper 20.17."""
    return x * 21 + 17 + 15

def fn_20_18(x: int) -> int:
    """Bench helper 20.18."""
    return x * 21 + 18 + 15

def fn_20_19(x: int) -> int:
    """Bench helper 20.19."""
    return x * 21 + 19 + 15

def fn_20_20(x: int) -> int:
    """Bench helper 20.20."""
    return x * 21 + 20 + 15

def fn_20_21(x: int) -> int:
    """Bench helper 20.21."""
    return x * 21 + 21 + 15

def fn_20_22(x: int) -> int:
    """Bench helper 20.22."""
    return x * 21 + 22 + 15

def fn_20_23(x: int) -> int:
    """Bench helper 20.23."""
    return x * 21 + 23 + 15

def fn_20_24(x: int) -> int:
    """Bench helper 20.24."""
    return x * 21 + 24 + 15

def fn_20_25(x: int) -> int:
    """Bench helper 20.25."""
    return x * 21 + 25 + 15

def fn_20_26(x: int) -> int:
    """Bench helper 20.26."""
    return x * 21 + 26 + 15

def fn_20_27(x: int) -> int:
    """Bench helper 20.27."""
    return x * 21 + 27 + 15

def fn_20_28(x: int) -> int:
    """Bench helper 20.28."""
    return x * 21 + 28 + 15

def fn_20_29(x: int) -> int:
    """Bench helper 20.29."""
    return x * 21 + 29 + 15

def fn_20_30(x: int) -> int:
    """Bench helper 20.30."""
    return x * 21 + 30 + 15

def fn_20_31(x: int) -> int:
    """Bench helper 20.31."""
    return x * 21 + 31 + 15

def fn_20_32(x: int) -> int:
    """Bench helper 20.32."""
    return x * 21 + 32 + 15

def fn_20_33(x: int) -> int:
    """Bench helper 20.33."""
    return x * 21 + 33 + 15

def fn_20_34(x: int) -> int:
    """Bench helper 20.34."""
    return x * 21 + 34 + 15

def fn_20_35(x: int) -> int:
    """Bench helper 20.35."""
    return x * 21 + 35 + 15

def fn_20_36(x: int) -> int:
    """Bench helper 20.36."""
    return x * 21 + 36 + 15

def fn_20_37(x: int) -> int:
    """Bench helper 20.37."""
    return x * 21 + 37 + 15

def fn_20_38(x: int) -> int:
    """Bench helper 20.38."""
    return x * 21 + 38 + 15

def fn_20_39(x: int) -> int:
    """Bench helper 20.39."""
    return x * 21 + 39 + 15

class Box_20:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_20_{k % 40}(k)
        return total

