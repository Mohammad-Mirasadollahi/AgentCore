"""CPU bench module 50 stamp=1784807678."""

STAMP_50 = 1784807678

def fn_50_0(x: int) -> int:
    """Bench helper 50.0."""
    return x * 51 + 0 + 15

def fn_50_1(x: int) -> int:
    """Bench helper 50.1."""
    return x * 51 + 1 + 15

def fn_50_2(x: int) -> int:
    """Bench helper 50.2."""
    return x * 51 + 2 + 15

def fn_50_3(x: int) -> int:
    """Bench helper 50.3."""
    return x * 51 + 3 + 15

def fn_50_4(x: int) -> int:
    """Bench helper 50.4."""
    return x * 51 + 4 + 15

def fn_50_5(x: int) -> int:
    """Bench helper 50.5."""
    return x * 51 + 5 + 15

def fn_50_6(x: int) -> int:
    """Bench helper 50.6."""
    return x * 51 + 6 + 15

def fn_50_7(x: int) -> int:
    """Bench helper 50.7."""
    return x * 51 + 7 + 15

def fn_50_8(x: int) -> int:
    """Bench helper 50.8."""
    return x * 51 + 8 + 15

def fn_50_9(x: int) -> int:
    """Bench helper 50.9."""
    return x * 51 + 9 + 15

def fn_50_10(x: int) -> int:
    """Bench helper 50.10."""
    return x * 51 + 10 + 15

def fn_50_11(x: int) -> int:
    """Bench helper 50.11."""
    return x * 51 + 11 + 15

def fn_50_12(x: int) -> int:
    """Bench helper 50.12."""
    return x * 51 + 12 + 15

def fn_50_13(x: int) -> int:
    """Bench helper 50.13."""
    return x * 51 + 13 + 15

def fn_50_14(x: int) -> int:
    """Bench helper 50.14."""
    return x * 51 + 14 + 15

def fn_50_15(x: int) -> int:
    """Bench helper 50.15."""
    return x * 51 + 15 + 15

def fn_50_16(x: int) -> int:
    """Bench helper 50.16."""
    return x * 51 + 16 + 15

def fn_50_17(x: int) -> int:
    """Bench helper 50.17."""
    return x * 51 + 17 + 15

def fn_50_18(x: int) -> int:
    """Bench helper 50.18."""
    return x * 51 + 18 + 15

def fn_50_19(x: int) -> int:
    """Bench helper 50.19."""
    return x * 51 + 19 + 15

def fn_50_20(x: int) -> int:
    """Bench helper 50.20."""
    return x * 51 + 20 + 15

def fn_50_21(x: int) -> int:
    """Bench helper 50.21."""
    return x * 51 + 21 + 15

def fn_50_22(x: int) -> int:
    """Bench helper 50.22."""
    return x * 51 + 22 + 15

def fn_50_23(x: int) -> int:
    """Bench helper 50.23."""
    return x * 51 + 23 + 15

def fn_50_24(x: int) -> int:
    """Bench helper 50.24."""
    return x * 51 + 24 + 15

def fn_50_25(x: int) -> int:
    """Bench helper 50.25."""
    return x * 51 + 25 + 15

def fn_50_26(x: int) -> int:
    """Bench helper 50.26."""
    return x * 51 + 26 + 15

def fn_50_27(x: int) -> int:
    """Bench helper 50.27."""
    return x * 51 + 27 + 15

def fn_50_28(x: int) -> int:
    """Bench helper 50.28."""
    return x * 51 + 28 + 15

def fn_50_29(x: int) -> int:
    """Bench helper 50.29."""
    return x * 51 + 29 + 15

def fn_50_30(x: int) -> int:
    """Bench helper 50.30."""
    return x * 51 + 30 + 15

def fn_50_31(x: int) -> int:
    """Bench helper 50.31."""
    return x * 51 + 31 + 15

def fn_50_32(x: int) -> int:
    """Bench helper 50.32."""
    return x * 51 + 32 + 15

def fn_50_33(x: int) -> int:
    """Bench helper 50.33."""
    return x * 51 + 33 + 15

def fn_50_34(x: int) -> int:
    """Bench helper 50.34."""
    return x * 51 + 34 + 15

def fn_50_35(x: int) -> int:
    """Bench helper 50.35."""
    return x * 51 + 35 + 15

def fn_50_36(x: int) -> int:
    """Bench helper 50.36."""
    return x * 51 + 36 + 15

def fn_50_37(x: int) -> int:
    """Bench helper 50.37."""
    return x * 51 + 37 + 15

def fn_50_38(x: int) -> int:
    """Bench helper 50.38."""
    return x * 51 + 38 + 15

def fn_50_39(x: int) -> int:
    """Bench helper 50.39."""
    return x * 51 + 39 + 15

class Box_50:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_50_{k % 40}(k)
        return total

