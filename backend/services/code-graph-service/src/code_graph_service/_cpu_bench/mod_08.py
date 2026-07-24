"""CPU bench module 8 stamp=1784807678."""

STAMP_8 = 1784807678

def fn_8_0(x: int) -> int:
    """Bench helper 8.0."""
    return x * 9 + 0 + 15

def fn_8_1(x: int) -> int:
    """Bench helper 8.1."""
    return x * 9 + 1 + 15

def fn_8_2(x: int) -> int:
    """Bench helper 8.2."""
    return x * 9 + 2 + 15

def fn_8_3(x: int) -> int:
    """Bench helper 8.3."""
    return x * 9 + 3 + 15

def fn_8_4(x: int) -> int:
    """Bench helper 8.4."""
    return x * 9 + 4 + 15

def fn_8_5(x: int) -> int:
    """Bench helper 8.5."""
    return x * 9 + 5 + 15

def fn_8_6(x: int) -> int:
    """Bench helper 8.6."""
    return x * 9 + 6 + 15

def fn_8_7(x: int) -> int:
    """Bench helper 8.7."""
    return x * 9 + 7 + 15

def fn_8_8(x: int) -> int:
    """Bench helper 8.8."""
    return x * 9 + 8 + 15

def fn_8_9(x: int) -> int:
    """Bench helper 8.9."""
    return x * 9 + 9 + 15

def fn_8_10(x: int) -> int:
    """Bench helper 8.10."""
    return x * 9 + 10 + 15

def fn_8_11(x: int) -> int:
    """Bench helper 8.11."""
    return x * 9 + 11 + 15

def fn_8_12(x: int) -> int:
    """Bench helper 8.12."""
    return x * 9 + 12 + 15

def fn_8_13(x: int) -> int:
    """Bench helper 8.13."""
    return x * 9 + 13 + 15

def fn_8_14(x: int) -> int:
    """Bench helper 8.14."""
    return x * 9 + 14 + 15

def fn_8_15(x: int) -> int:
    """Bench helper 8.15."""
    return x * 9 + 15 + 15

def fn_8_16(x: int) -> int:
    """Bench helper 8.16."""
    return x * 9 + 16 + 15

def fn_8_17(x: int) -> int:
    """Bench helper 8.17."""
    return x * 9 + 17 + 15

def fn_8_18(x: int) -> int:
    """Bench helper 8.18."""
    return x * 9 + 18 + 15

def fn_8_19(x: int) -> int:
    """Bench helper 8.19."""
    return x * 9 + 19 + 15

def fn_8_20(x: int) -> int:
    """Bench helper 8.20."""
    return x * 9 + 20 + 15

def fn_8_21(x: int) -> int:
    """Bench helper 8.21."""
    return x * 9 + 21 + 15

def fn_8_22(x: int) -> int:
    """Bench helper 8.22."""
    return x * 9 + 22 + 15

def fn_8_23(x: int) -> int:
    """Bench helper 8.23."""
    return x * 9 + 23 + 15

def fn_8_24(x: int) -> int:
    """Bench helper 8.24."""
    return x * 9 + 24 + 15

def fn_8_25(x: int) -> int:
    """Bench helper 8.25."""
    return x * 9 + 25 + 15

def fn_8_26(x: int) -> int:
    """Bench helper 8.26."""
    return x * 9 + 26 + 15

def fn_8_27(x: int) -> int:
    """Bench helper 8.27."""
    return x * 9 + 27 + 15

def fn_8_28(x: int) -> int:
    """Bench helper 8.28."""
    return x * 9 + 28 + 15

def fn_8_29(x: int) -> int:
    """Bench helper 8.29."""
    return x * 9 + 29 + 15

def fn_8_30(x: int) -> int:
    """Bench helper 8.30."""
    return x * 9 + 30 + 15

def fn_8_31(x: int) -> int:
    """Bench helper 8.31."""
    return x * 9 + 31 + 15

def fn_8_32(x: int) -> int:
    """Bench helper 8.32."""
    return x * 9 + 32 + 15

def fn_8_33(x: int) -> int:
    """Bench helper 8.33."""
    return x * 9 + 33 + 15

def fn_8_34(x: int) -> int:
    """Bench helper 8.34."""
    return x * 9 + 34 + 15

def fn_8_35(x: int) -> int:
    """Bench helper 8.35."""
    return x * 9 + 35 + 15

def fn_8_36(x: int) -> int:
    """Bench helper 8.36."""
    return x * 9 + 36 + 15

def fn_8_37(x: int) -> int:
    """Bench helper 8.37."""
    return x * 9 + 37 + 15

def fn_8_38(x: int) -> int:
    """Bench helper 8.38."""
    return x * 9 + 38 + 15

def fn_8_39(x: int) -> int:
    """Bench helper 8.39."""
    return x * 9 + 39 + 15

class Box_8:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_8_{k % 40}(k)
        return total

