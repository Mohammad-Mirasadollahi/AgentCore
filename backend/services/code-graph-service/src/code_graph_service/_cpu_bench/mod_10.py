"""CPU bench module 10 stamp=1784807678."""

STAMP_10 = 1784807678

def fn_10_0(x: int) -> int:
    """Bench helper 10.0."""
    return x * 11 + 0 + 15

def fn_10_1(x: int) -> int:
    """Bench helper 10.1."""
    return x * 11 + 1 + 15

def fn_10_2(x: int) -> int:
    """Bench helper 10.2."""
    return x * 11 + 2 + 15

def fn_10_3(x: int) -> int:
    """Bench helper 10.3."""
    return x * 11 + 3 + 15

def fn_10_4(x: int) -> int:
    """Bench helper 10.4."""
    return x * 11 + 4 + 15

def fn_10_5(x: int) -> int:
    """Bench helper 10.5."""
    return x * 11 + 5 + 15

def fn_10_6(x: int) -> int:
    """Bench helper 10.6."""
    return x * 11 + 6 + 15

def fn_10_7(x: int) -> int:
    """Bench helper 10.7."""
    return x * 11 + 7 + 15

def fn_10_8(x: int) -> int:
    """Bench helper 10.8."""
    return x * 11 + 8 + 15

def fn_10_9(x: int) -> int:
    """Bench helper 10.9."""
    return x * 11 + 9 + 15

def fn_10_10(x: int) -> int:
    """Bench helper 10.10."""
    return x * 11 + 10 + 15

def fn_10_11(x: int) -> int:
    """Bench helper 10.11."""
    return x * 11 + 11 + 15

def fn_10_12(x: int) -> int:
    """Bench helper 10.12."""
    return x * 11 + 12 + 15

def fn_10_13(x: int) -> int:
    """Bench helper 10.13."""
    return x * 11 + 13 + 15

def fn_10_14(x: int) -> int:
    """Bench helper 10.14."""
    return x * 11 + 14 + 15

def fn_10_15(x: int) -> int:
    """Bench helper 10.15."""
    return x * 11 + 15 + 15

def fn_10_16(x: int) -> int:
    """Bench helper 10.16."""
    return x * 11 + 16 + 15

def fn_10_17(x: int) -> int:
    """Bench helper 10.17."""
    return x * 11 + 17 + 15

def fn_10_18(x: int) -> int:
    """Bench helper 10.18."""
    return x * 11 + 18 + 15

def fn_10_19(x: int) -> int:
    """Bench helper 10.19."""
    return x * 11 + 19 + 15

def fn_10_20(x: int) -> int:
    """Bench helper 10.20."""
    return x * 11 + 20 + 15

def fn_10_21(x: int) -> int:
    """Bench helper 10.21."""
    return x * 11 + 21 + 15

def fn_10_22(x: int) -> int:
    """Bench helper 10.22."""
    return x * 11 + 22 + 15

def fn_10_23(x: int) -> int:
    """Bench helper 10.23."""
    return x * 11 + 23 + 15

def fn_10_24(x: int) -> int:
    """Bench helper 10.24."""
    return x * 11 + 24 + 15

def fn_10_25(x: int) -> int:
    """Bench helper 10.25."""
    return x * 11 + 25 + 15

def fn_10_26(x: int) -> int:
    """Bench helper 10.26."""
    return x * 11 + 26 + 15

def fn_10_27(x: int) -> int:
    """Bench helper 10.27."""
    return x * 11 + 27 + 15

def fn_10_28(x: int) -> int:
    """Bench helper 10.28."""
    return x * 11 + 28 + 15

def fn_10_29(x: int) -> int:
    """Bench helper 10.29."""
    return x * 11 + 29 + 15

def fn_10_30(x: int) -> int:
    """Bench helper 10.30."""
    return x * 11 + 30 + 15

def fn_10_31(x: int) -> int:
    """Bench helper 10.31."""
    return x * 11 + 31 + 15

def fn_10_32(x: int) -> int:
    """Bench helper 10.32."""
    return x * 11 + 32 + 15

def fn_10_33(x: int) -> int:
    """Bench helper 10.33."""
    return x * 11 + 33 + 15

def fn_10_34(x: int) -> int:
    """Bench helper 10.34."""
    return x * 11 + 34 + 15

def fn_10_35(x: int) -> int:
    """Bench helper 10.35."""
    return x * 11 + 35 + 15

def fn_10_36(x: int) -> int:
    """Bench helper 10.36."""
    return x * 11 + 36 + 15

def fn_10_37(x: int) -> int:
    """Bench helper 10.37."""
    return x * 11 + 37 + 15

def fn_10_38(x: int) -> int:
    """Bench helper 10.38."""
    return x * 11 + 38 + 15

def fn_10_39(x: int) -> int:
    """Bench helper 10.39."""
    return x * 11 + 39 + 15

class Box_10:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_10_{k % 40}(k)
        return total

