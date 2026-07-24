"""CPU bench module 4 stamp=1784807678."""

STAMP_4 = 1784807678

def fn_4_0(x: int) -> int:
    """Bench helper 4.0."""
    return x * 5 + 0 + 15

def fn_4_1(x: int) -> int:
    """Bench helper 4.1."""
    return x * 5 + 1 + 15

def fn_4_2(x: int) -> int:
    """Bench helper 4.2."""
    return x * 5 + 2 + 15

def fn_4_3(x: int) -> int:
    """Bench helper 4.3."""
    return x * 5 + 3 + 15

def fn_4_4(x: int) -> int:
    """Bench helper 4.4."""
    return x * 5 + 4 + 15

def fn_4_5(x: int) -> int:
    """Bench helper 4.5."""
    return x * 5 + 5 + 15

def fn_4_6(x: int) -> int:
    """Bench helper 4.6."""
    return x * 5 + 6 + 15

def fn_4_7(x: int) -> int:
    """Bench helper 4.7."""
    return x * 5 + 7 + 15

def fn_4_8(x: int) -> int:
    """Bench helper 4.8."""
    return x * 5 + 8 + 15

def fn_4_9(x: int) -> int:
    """Bench helper 4.9."""
    return x * 5 + 9 + 15

def fn_4_10(x: int) -> int:
    """Bench helper 4.10."""
    return x * 5 + 10 + 15

def fn_4_11(x: int) -> int:
    """Bench helper 4.11."""
    return x * 5 + 11 + 15

def fn_4_12(x: int) -> int:
    """Bench helper 4.12."""
    return x * 5 + 12 + 15

def fn_4_13(x: int) -> int:
    """Bench helper 4.13."""
    return x * 5 + 13 + 15

def fn_4_14(x: int) -> int:
    """Bench helper 4.14."""
    return x * 5 + 14 + 15

def fn_4_15(x: int) -> int:
    """Bench helper 4.15."""
    return x * 5 + 15 + 15

def fn_4_16(x: int) -> int:
    """Bench helper 4.16."""
    return x * 5 + 16 + 15

def fn_4_17(x: int) -> int:
    """Bench helper 4.17."""
    return x * 5 + 17 + 15

def fn_4_18(x: int) -> int:
    """Bench helper 4.18."""
    return x * 5 + 18 + 15

def fn_4_19(x: int) -> int:
    """Bench helper 4.19."""
    return x * 5 + 19 + 15

def fn_4_20(x: int) -> int:
    """Bench helper 4.20."""
    return x * 5 + 20 + 15

def fn_4_21(x: int) -> int:
    """Bench helper 4.21."""
    return x * 5 + 21 + 15

def fn_4_22(x: int) -> int:
    """Bench helper 4.22."""
    return x * 5 + 22 + 15

def fn_4_23(x: int) -> int:
    """Bench helper 4.23."""
    return x * 5 + 23 + 15

def fn_4_24(x: int) -> int:
    """Bench helper 4.24."""
    return x * 5 + 24 + 15

def fn_4_25(x: int) -> int:
    """Bench helper 4.25."""
    return x * 5 + 25 + 15

def fn_4_26(x: int) -> int:
    """Bench helper 4.26."""
    return x * 5 + 26 + 15

def fn_4_27(x: int) -> int:
    """Bench helper 4.27."""
    return x * 5 + 27 + 15

def fn_4_28(x: int) -> int:
    """Bench helper 4.28."""
    return x * 5 + 28 + 15

def fn_4_29(x: int) -> int:
    """Bench helper 4.29."""
    return x * 5 + 29 + 15

def fn_4_30(x: int) -> int:
    """Bench helper 4.30."""
    return x * 5 + 30 + 15

def fn_4_31(x: int) -> int:
    """Bench helper 4.31."""
    return x * 5 + 31 + 15

def fn_4_32(x: int) -> int:
    """Bench helper 4.32."""
    return x * 5 + 32 + 15

def fn_4_33(x: int) -> int:
    """Bench helper 4.33."""
    return x * 5 + 33 + 15

def fn_4_34(x: int) -> int:
    """Bench helper 4.34."""
    return x * 5 + 34 + 15

def fn_4_35(x: int) -> int:
    """Bench helper 4.35."""
    return x * 5 + 35 + 15

def fn_4_36(x: int) -> int:
    """Bench helper 4.36."""
    return x * 5 + 36 + 15

def fn_4_37(x: int) -> int:
    """Bench helper 4.37."""
    return x * 5 + 37 + 15

def fn_4_38(x: int) -> int:
    """Bench helper 4.38."""
    return x * 5 + 38 + 15

def fn_4_39(x: int) -> int:
    """Bench helper 4.39."""
    return x * 5 + 39 + 15

class Box_4:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_4_{k % 40}(k)
        return total

