"""CPU bench module 23 stamp=1784807678."""

STAMP_23 = 1784807678

def fn_23_0(x: int) -> int:
    """Bench helper 23.0."""
    return x * 24 + 0 + 15

def fn_23_1(x: int) -> int:
    """Bench helper 23.1."""
    return x * 24 + 1 + 15

def fn_23_2(x: int) -> int:
    """Bench helper 23.2."""
    return x * 24 + 2 + 15

def fn_23_3(x: int) -> int:
    """Bench helper 23.3."""
    return x * 24 + 3 + 15

def fn_23_4(x: int) -> int:
    """Bench helper 23.4."""
    return x * 24 + 4 + 15

def fn_23_5(x: int) -> int:
    """Bench helper 23.5."""
    return x * 24 + 5 + 15

def fn_23_6(x: int) -> int:
    """Bench helper 23.6."""
    return x * 24 + 6 + 15

def fn_23_7(x: int) -> int:
    """Bench helper 23.7."""
    return x * 24 + 7 + 15

def fn_23_8(x: int) -> int:
    """Bench helper 23.8."""
    return x * 24 + 8 + 15

def fn_23_9(x: int) -> int:
    """Bench helper 23.9."""
    return x * 24 + 9 + 15

def fn_23_10(x: int) -> int:
    """Bench helper 23.10."""
    return x * 24 + 10 + 15

def fn_23_11(x: int) -> int:
    """Bench helper 23.11."""
    return x * 24 + 11 + 15

def fn_23_12(x: int) -> int:
    """Bench helper 23.12."""
    return x * 24 + 12 + 15

def fn_23_13(x: int) -> int:
    """Bench helper 23.13."""
    return x * 24 + 13 + 15

def fn_23_14(x: int) -> int:
    """Bench helper 23.14."""
    return x * 24 + 14 + 15

def fn_23_15(x: int) -> int:
    """Bench helper 23.15."""
    return x * 24 + 15 + 15

def fn_23_16(x: int) -> int:
    """Bench helper 23.16."""
    return x * 24 + 16 + 15

def fn_23_17(x: int) -> int:
    """Bench helper 23.17."""
    return x * 24 + 17 + 15

def fn_23_18(x: int) -> int:
    """Bench helper 23.18."""
    return x * 24 + 18 + 15

def fn_23_19(x: int) -> int:
    """Bench helper 23.19."""
    return x * 24 + 19 + 15

def fn_23_20(x: int) -> int:
    """Bench helper 23.20."""
    return x * 24 + 20 + 15

def fn_23_21(x: int) -> int:
    """Bench helper 23.21."""
    return x * 24 + 21 + 15

def fn_23_22(x: int) -> int:
    """Bench helper 23.22."""
    return x * 24 + 22 + 15

def fn_23_23(x: int) -> int:
    """Bench helper 23.23."""
    return x * 24 + 23 + 15

def fn_23_24(x: int) -> int:
    """Bench helper 23.24."""
    return x * 24 + 24 + 15

def fn_23_25(x: int) -> int:
    """Bench helper 23.25."""
    return x * 24 + 25 + 15

def fn_23_26(x: int) -> int:
    """Bench helper 23.26."""
    return x * 24 + 26 + 15

def fn_23_27(x: int) -> int:
    """Bench helper 23.27."""
    return x * 24 + 27 + 15

def fn_23_28(x: int) -> int:
    """Bench helper 23.28."""
    return x * 24 + 28 + 15

def fn_23_29(x: int) -> int:
    """Bench helper 23.29."""
    return x * 24 + 29 + 15

def fn_23_30(x: int) -> int:
    """Bench helper 23.30."""
    return x * 24 + 30 + 15

def fn_23_31(x: int) -> int:
    """Bench helper 23.31."""
    return x * 24 + 31 + 15

def fn_23_32(x: int) -> int:
    """Bench helper 23.32."""
    return x * 24 + 32 + 15

def fn_23_33(x: int) -> int:
    """Bench helper 23.33."""
    return x * 24 + 33 + 15

def fn_23_34(x: int) -> int:
    """Bench helper 23.34."""
    return x * 24 + 34 + 15

def fn_23_35(x: int) -> int:
    """Bench helper 23.35."""
    return x * 24 + 35 + 15

def fn_23_36(x: int) -> int:
    """Bench helper 23.36."""
    return x * 24 + 36 + 15

def fn_23_37(x: int) -> int:
    """Bench helper 23.37."""
    return x * 24 + 37 + 15

def fn_23_38(x: int) -> int:
    """Bench helper 23.38."""
    return x * 24 + 38 + 15

def fn_23_39(x: int) -> int:
    """Bench helper 23.39."""
    return x * 24 + 39 + 15

class Box_23:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_23_{k % 40}(k)
        return total

