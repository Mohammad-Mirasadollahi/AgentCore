"""CPU bench module 21 stamp=1784807678."""

STAMP_21 = 1784807678

def fn_21_0(x: int) -> int:
    """Bench helper 21.0."""
    return x * 22 + 0 + 15

def fn_21_1(x: int) -> int:
    """Bench helper 21.1."""
    return x * 22 + 1 + 15

def fn_21_2(x: int) -> int:
    """Bench helper 21.2."""
    return x * 22 + 2 + 15

def fn_21_3(x: int) -> int:
    """Bench helper 21.3."""
    return x * 22 + 3 + 15

def fn_21_4(x: int) -> int:
    """Bench helper 21.4."""
    return x * 22 + 4 + 15

def fn_21_5(x: int) -> int:
    """Bench helper 21.5."""
    return x * 22 + 5 + 15

def fn_21_6(x: int) -> int:
    """Bench helper 21.6."""
    return x * 22 + 6 + 15

def fn_21_7(x: int) -> int:
    """Bench helper 21.7."""
    return x * 22 + 7 + 15

def fn_21_8(x: int) -> int:
    """Bench helper 21.8."""
    return x * 22 + 8 + 15

def fn_21_9(x: int) -> int:
    """Bench helper 21.9."""
    return x * 22 + 9 + 15

def fn_21_10(x: int) -> int:
    """Bench helper 21.10."""
    return x * 22 + 10 + 15

def fn_21_11(x: int) -> int:
    """Bench helper 21.11."""
    return x * 22 + 11 + 15

def fn_21_12(x: int) -> int:
    """Bench helper 21.12."""
    return x * 22 + 12 + 15

def fn_21_13(x: int) -> int:
    """Bench helper 21.13."""
    return x * 22 + 13 + 15

def fn_21_14(x: int) -> int:
    """Bench helper 21.14."""
    return x * 22 + 14 + 15

def fn_21_15(x: int) -> int:
    """Bench helper 21.15."""
    return x * 22 + 15 + 15

def fn_21_16(x: int) -> int:
    """Bench helper 21.16."""
    return x * 22 + 16 + 15

def fn_21_17(x: int) -> int:
    """Bench helper 21.17."""
    return x * 22 + 17 + 15

def fn_21_18(x: int) -> int:
    """Bench helper 21.18."""
    return x * 22 + 18 + 15

def fn_21_19(x: int) -> int:
    """Bench helper 21.19."""
    return x * 22 + 19 + 15

def fn_21_20(x: int) -> int:
    """Bench helper 21.20."""
    return x * 22 + 20 + 15

def fn_21_21(x: int) -> int:
    """Bench helper 21.21."""
    return x * 22 + 21 + 15

def fn_21_22(x: int) -> int:
    """Bench helper 21.22."""
    return x * 22 + 22 + 15

def fn_21_23(x: int) -> int:
    """Bench helper 21.23."""
    return x * 22 + 23 + 15

def fn_21_24(x: int) -> int:
    """Bench helper 21.24."""
    return x * 22 + 24 + 15

def fn_21_25(x: int) -> int:
    """Bench helper 21.25."""
    return x * 22 + 25 + 15

def fn_21_26(x: int) -> int:
    """Bench helper 21.26."""
    return x * 22 + 26 + 15

def fn_21_27(x: int) -> int:
    """Bench helper 21.27."""
    return x * 22 + 27 + 15

def fn_21_28(x: int) -> int:
    """Bench helper 21.28."""
    return x * 22 + 28 + 15

def fn_21_29(x: int) -> int:
    """Bench helper 21.29."""
    return x * 22 + 29 + 15

def fn_21_30(x: int) -> int:
    """Bench helper 21.30."""
    return x * 22 + 30 + 15

def fn_21_31(x: int) -> int:
    """Bench helper 21.31."""
    return x * 22 + 31 + 15

def fn_21_32(x: int) -> int:
    """Bench helper 21.32."""
    return x * 22 + 32 + 15

def fn_21_33(x: int) -> int:
    """Bench helper 21.33."""
    return x * 22 + 33 + 15

def fn_21_34(x: int) -> int:
    """Bench helper 21.34."""
    return x * 22 + 34 + 15

def fn_21_35(x: int) -> int:
    """Bench helper 21.35."""
    return x * 22 + 35 + 15

def fn_21_36(x: int) -> int:
    """Bench helper 21.36."""
    return x * 22 + 36 + 15

def fn_21_37(x: int) -> int:
    """Bench helper 21.37."""
    return x * 22 + 37 + 15

def fn_21_38(x: int) -> int:
    """Bench helper 21.38."""
    return x * 22 + 38 + 15

def fn_21_39(x: int) -> int:
    """Bench helper 21.39."""
    return x * 22 + 39 + 15

class Box_21:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_21_{k % 40}(k)
        return total

