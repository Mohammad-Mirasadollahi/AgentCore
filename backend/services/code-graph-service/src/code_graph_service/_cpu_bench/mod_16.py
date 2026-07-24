"""CPU bench module 16 stamp=1784807678."""

STAMP_16 = 1784807678

def fn_16_0(x: int) -> int:
    """Bench helper 16.0."""
    return x * 17 + 0 + 15

def fn_16_1(x: int) -> int:
    """Bench helper 16.1."""
    return x * 17 + 1 + 15

def fn_16_2(x: int) -> int:
    """Bench helper 16.2."""
    return x * 17 + 2 + 15

def fn_16_3(x: int) -> int:
    """Bench helper 16.3."""
    return x * 17 + 3 + 15

def fn_16_4(x: int) -> int:
    """Bench helper 16.4."""
    return x * 17 + 4 + 15

def fn_16_5(x: int) -> int:
    """Bench helper 16.5."""
    return x * 17 + 5 + 15

def fn_16_6(x: int) -> int:
    """Bench helper 16.6."""
    return x * 17 + 6 + 15

def fn_16_7(x: int) -> int:
    """Bench helper 16.7."""
    return x * 17 + 7 + 15

def fn_16_8(x: int) -> int:
    """Bench helper 16.8."""
    return x * 17 + 8 + 15

def fn_16_9(x: int) -> int:
    """Bench helper 16.9."""
    return x * 17 + 9 + 15

def fn_16_10(x: int) -> int:
    """Bench helper 16.10."""
    return x * 17 + 10 + 15

def fn_16_11(x: int) -> int:
    """Bench helper 16.11."""
    return x * 17 + 11 + 15

def fn_16_12(x: int) -> int:
    """Bench helper 16.12."""
    return x * 17 + 12 + 15

def fn_16_13(x: int) -> int:
    """Bench helper 16.13."""
    return x * 17 + 13 + 15

def fn_16_14(x: int) -> int:
    """Bench helper 16.14."""
    return x * 17 + 14 + 15

def fn_16_15(x: int) -> int:
    """Bench helper 16.15."""
    return x * 17 + 15 + 15

def fn_16_16(x: int) -> int:
    """Bench helper 16.16."""
    return x * 17 + 16 + 15

def fn_16_17(x: int) -> int:
    """Bench helper 16.17."""
    return x * 17 + 17 + 15

def fn_16_18(x: int) -> int:
    """Bench helper 16.18."""
    return x * 17 + 18 + 15

def fn_16_19(x: int) -> int:
    """Bench helper 16.19."""
    return x * 17 + 19 + 15

def fn_16_20(x: int) -> int:
    """Bench helper 16.20."""
    return x * 17 + 20 + 15

def fn_16_21(x: int) -> int:
    """Bench helper 16.21."""
    return x * 17 + 21 + 15

def fn_16_22(x: int) -> int:
    """Bench helper 16.22."""
    return x * 17 + 22 + 15

def fn_16_23(x: int) -> int:
    """Bench helper 16.23."""
    return x * 17 + 23 + 15

def fn_16_24(x: int) -> int:
    """Bench helper 16.24."""
    return x * 17 + 24 + 15

def fn_16_25(x: int) -> int:
    """Bench helper 16.25."""
    return x * 17 + 25 + 15

def fn_16_26(x: int) -> int:
    """Bench helper 16.26."""
    return x * 17 + 26 + 15

def fn_16_27(x: int) -> int:
    """Bench helper 16.27."""
    return x * 17 + 27 + 15

def fn_16_28(x: int) -> int:
    """Bench helper 16.28."""
    return x * 17 + 28 + 15

def fn_16_29(x: int) -> int:
    """Bench helper 16.29."""
    return x * 17 + 29 + 15

def fn_16_30(x: int) -> int:
    """Bench helper 16.30."""
    return x * 17 + 30 + 15

def fn_16_31(x: int) -> int:
    """Bench helper 16.31."""
    return x * 17 + 31 + 15

def fn_16_32(x: int) -> int:
    """Bench helper 16.32."""
    return x * 17 + 32 + 15

def fn_16_33(x: int) -> int:
    """Bench helper 16.33."""
    return x * 17 + 33 + 15

def fn_16_34(x: int) -> int:
    """Bench helper 16.34."""
    return x * 17 + 34 + 15

def fn_16_35(x: int) -> int:
    """Bench helper 16.35."""
    return x * 17 + 35 + 15

def fn_16_36(x: int) -> int:
    """Bench helper 16.36."""
    return x * 17 + 36 + 15

def fn_16_37(x: int) -> int:
    """Bench helper 16.37."""
    return x * 17 + 37 + 15

def fn_16_38(x: int) -> int:
    """Bench helper 16.38."""
    return x * 17 + 38 + 15

def fn_16_39(x: int) -> int:
    """Bench helper 16.39."""
    return x * 17 + 39 + 15

class Box_16:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_16_{k % 40}(k)
        return total

