"""CPU bench module 17 stamp=1784807678."""

STAMP_17 = 1784807678

def fn_17_0(x: int) -> int:
    """Bench helper 17.0."""
    return x * 18 + 0 + 15

def fn_17_1(x: int) -> int:
    """Bench helper 17.1."""
    return x * 18 + 1 + 15

def fn_17_2(x: int) -> int:
    """Bench helper 17.2."""
    return x * 18 + 2 + 15

def fn_17_3(x: int) -> int:
    """Bench helper 17.3."""
    return x * 18 + 3 + 15

def fn_17_4(x: int) -> int:
    """Bench helper 17.4."""
    return x * 18 + 4 + 15

def fn_17_5(x: int) -> int:
    """Bench helper 17.5."""
    return x * 18 + 5 + 15

def fn_17_6(x: int) -> int:
    """Bench helper 17.6."""
    return x * 18 + 6 + 15

def fn_17_7(x: int) -> int:
    """Bench helper 17.7."""
    return x * 18 + 7 + 15

def fn_17_8(x: int) -> int:
    """Bench helper 17.8."""
    return x * 18 + 8 + 15

def fn_17_9(x: int) -> int:
    """Bench helper 17.9."""
    return x * 18 + 9 + 15

def fn_17_10(x: int) -> int:
    """Bench helper 17.10."""
    return x * 18 + 10 + 15

def fn_17_11(x: int) -> int:
    """Bench helper 17.11."""
    return x * 18 + 11 + 15

def fn_17_12(x: int) -> int:
    """Bench helper 17.12."""
    return x * 18 + 12 + 15

def fn_17_13(x: int) -> int:
    """Bench helper 17.13."""
    return x * 18 + 13 + 15

def fn_17_14(x: int) -> int:
    """Bench helper 17.14."""
    return x * 18 + 14 + 15

def fn_17_15(x: int) -> int:
    """Bench helper 17.15."""
    return x * 18 + 15 + 15

def fn_17_16(x: int) -> int:
    """Bench helper 17.16."""
    return x * 18 + 16 + 15

def fn_17_17(x: int) -> int:
    """Bench helper 17.17."""
    return x * 18 + 17 + 15

def fn_17_18(x: int) -> int:
    """Bench helper 17.18."""
    return x * 18 + 18 + 15

def fn_17_19(x: int) -> int:
    """Bench helper 17.19."""
    return x * 18 + 19 + 15

def fn_17_20(x: int) -> int:
    """Bench helper 17.20."""
    return x * 18 + 20 + 15

def fn_17_21(x: int) -> int:
    """Bench helper 17.21."""
    return x * 18 + 21 + 15

def fn_17_22(x: int) -> int:
    """Bench helper 17.22."""
    return x * 18 + 22 + 15

def fn_17_23(x: int) -> int:
    """Bench helper 17.23."""
    return x * 18 + 23 + 15

def fn_17_24(x: int) -> int:
    """Bench helper 17.24."""
    return x * 18 + 24 + 15

def fn_17_25(x: int) -> int:
    """Bench helper 17.25."""
    return x * 18 + 25 + 15

def fn_17_26(x: int) -> int:
    """Bench helper 17.26."""
    return x * 18 + 26 + 15

def fn_17_27(x: int) -> int:
    """Bench helper 17.27."""
    return x * 18 + 27 + 15

def fn_17_28(x: int) -> int:
    """Bench helper 17.28."""
    return x * 18 + 28 + 15

def fn_17_29(x: int) -> int:
    """Bench helper 17.29."""
    return x * 18 + 29 + 15

def fn_17_30(x: int) -> int:
    """Bench helper 17.30."""
    return x * 18 + 30 + 15

def fn_17_31(x: int) -> int:
    """Bench helper 17.31."""
    return x * 18 + 31 + 15

def fn_17_32(x: int) -> int:
    """Bench helper 17.32."""
    return x * 18 + 32 + 15

def fn_17_33(x: int) -> int:
    """Bench helper 17.33."""
    return x * 18 + 33 + 15

def fn_17_34(x: int) -> int:
    """Bench helper 17.34."""
    return x * 18 + 34 + 15

def fn_17_35(x: int) -> int:
    """Bench helper 17.35."""
    return x * 18 + 35 + 15

def fn_17_36(x: int) -> int:
    """Bench helper 17.36."""
    return x * 18 + 36 + 15

def fn_17_37(x: int) -> int:
    """Bench helper 17.37."""
    return x * 18 + 37 + 15

def fn_17_38(x: int) -> int:
    """Bench helper 17.38."""
    return x * 18 + 38 + 15

def fn_17_39(x: int) -> int:
    """Bench helper 17.39."""
    return x * 18 + 39 + 15

class Box_17:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_17_{k % 40}(k)
        return total

