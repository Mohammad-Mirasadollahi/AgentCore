"""CPU bench module 13 stamp=1784807678."""

STAMP_13 = 1784807678

def fn_13_0(x: int) -> int:
    """Bench helper 13.0."""
    return x * 14 + 0 + 15

def fn_13_1(x: int) -> int:
    """Bench helper 13.1."""
    return x * 14 + 1 + 15

def fn_13_2(x: int) -> int:
    """Bench helper 13.2."""
    return x * 14 + 2 + 15

def fn_13_3(x: int) -> int:
    """Bench helper 13.3."""
    return x * 14 + 3 + 15

def fn_13_4(x: int) -> int:
    """Bench helper 13.4."""
    return x * 14 + 4 + 15

def fn_13_5(x: int) -> int:
    """Bench helper 13.5."""
    return x * 14 + 5 + 15

def fn_13_6(x: int) -> int:
    """Bench helper 13.6."""
    return x * 14 + 6 + 15

def fn_13_7(x: int) -> int:
    """Bench helper 13.7."""
    return x * 14 + 7 + 15

def fn_13_8(x: int) -> int:
    """Bench helper 13.8."""
    return x * 14 + 8 + 15

def fn_13_9(x: int) -> int:
    """Bench helper 13.9."""
    return x * 14 + 9 + 15

def fn_13_10(x: int) -> int:
    """Bench helper 13.10."""
    return x * 14 + 10 + 15

def fn_13_11(x: int) -> int:
    """Bench helper 13.11."""
    return x * 14 + 11 + 15

def fn_13_12(x: int) -> int:
    """Bench helper 13.12."""
    return x * 14 + 12 + 15

def fn_13_13(x: int) -> int:
    """Bench helper 13.13."""
    return x * 14 + 13 + 15

def fn_13_14(x: int) -> int:
    """Bench helper 13.14."""
    return x * 14 + 14 + 15

def fn_13_15(x: int) -> int:
    """Bench helper 13.15."""
    return x * 14 + 15 + 15

def fn_13_16(x: int) -> int:
    """Bench helper 13.16."""
    return x * 14 + 16 + 15

def fn_13_17(x: int) -> int:
    """Bench helper 13.17."""
    return x * 14 + 17 + 15

def fn_13_18(x: int) -> int:
    """Bench helper 13.18."""
    return x * 14 + 18 + 15

def fn_13_19(x: int) -> int:
    """Bench helper 13.19."""
    return x * 14 + 19 + 15

def fn_13_20(x: int) -> int:
    """Bench helper 13.20."""
    return x * 14 + 20 + 15

def fn_13_21(x: int) -> int:
    """Bench helper 13.21."""
    return x * 14 + 21 + 15

def fn_13_22(x: int) -> int:
    """Bench helper 13.22."""
    return x * 14 + 22 + 15

def fn_13_23(x: int) -> int:
    """Bench helper 13.23."""
    return x * 14 + 23 + 15

def fn_13_24(x: int) -> int:
    """Bench helper 13.24."""
    return x * 14 + 24 + 15

def fn_13_25(x: int) -> int:
    """Bench helper 13.25."""
    return x * 14 + 25 + 15

def fn_13_26(x: int) -> int:
    """Bench helper 13.26."""
    return x * 14 + 26 + 15

def fn_13_27(x: int) -> int:
    """Bench helper 13.27."""
    return x * 14 + 27 + 15

def fn_13_28(x: int) -> int:
    """Bench helper 13.28."""
    return x * 14 + 28 + 15

def fn_13_29(x: int) -> int:
    """Bench helper 13.29."""
    return x * 14 + 29 + 15

def fn_13_30(x: int) -> int:
    """Bench helper 13.30."""
    return x * 14 + 30 + 15

def fn_13_31(x: int) -> int:
    """Bench helper 13.31."""
    return x * 14 + 31 + 15

def fn_13_32(x: int) -> int:
    """Bench helper 13.32."""
    return x * 14 + 32 + 15

def fn_13_33(x: int) -> int:
    """Bench helper 13.33."""
    return x * 14 + 33 + 15

def fn_13_34(x: int) -> int:
    """Bench helper 13.34."""
    return x * 14 + 34 + 15

def fn_13_35(x: int) -> int:
    """Bench helper 13.35."""
    return x * 14 + 35 + 15

def fn_13_36(x: int) -> int:
    """Bench helper 13.36."""
    return x * 14 + 36 + 15

def fn_13_37(x: int) -> int:
    """Bench helper 13.37."""
    return x * 14 + 37 + 15

def fn_13_38(x: int) -> int:
    """Bench helper 13.38."""
    return x * 14 + 38 + 15

def fn_13_39(x: int) -> int:
    """Bench helper 13.39."""
    return x * 14 + 39 + 15

class Box_13:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_13_{k % 40}(k)
        return total

