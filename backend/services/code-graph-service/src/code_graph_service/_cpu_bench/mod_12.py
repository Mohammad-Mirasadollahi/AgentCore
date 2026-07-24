"""CPU bench module 12 stamp=1784807678."""

STAMP_12 = 1784807678

def fn_12_0(x: int) -> int:
    """Bench helper 12.0."""
    return x * 13 + 0 + 15

def fn_12_1(x: int) -> int:
    """Bench helper 12.1."""
    return x * 13 + 1 + 15

def fn_12_2(x: int) -> int:
    """Bench helper 12.2."""
    return x * 13 + 2 + 15

def fn_12_3(x: int) -> int:
    """Bench helper 12.3."""
    return x * 13 + 3 + 15

def fn_12_4(x: int) -> int:
    """Bench helper 12.4."""
    return x * 13 + 4 + 15

def fn_12_5(x: int) -> int:
    """Bench helper 12.5."""
    return x * 13 + 5 + 15

def fn_12_6(x: int) -> int:
    """Bench helper 12.6."""
    return x * 13 + 6 + 15

def fn_12_7(x: int) -> int:
    """Bench helper 12.7."""
    return x * 13 + 7 + 15

def fn_12_8(x: int) -> int:
    """Bench helper 12.8."""
    return x * 13 + 8 + 15

def fn_12_9(x: int) -> int:
    """Bench helper 12.9."""
    return x * 13 + 9 + 15

def fn_12_10(x: int) -> int:
    """Bench helper 12.10."""
    return x * 13 + 10 + 15

def fn_12_11(x: int) -> int:
    """Bench helper 12.11."""
    return x * 13 + 11 + 15

def fn_12_12(x: int) -> int:
    """Bench helper 12.12."""
    return x * 13 + 12 + 15

def fn_12_13(x: int) -> int:
    """Bench helper 12.13."""
    return x * 13 + 13 + 15

def fn_12_14(x: int) -> int:
    """Bench helper 12.14."""
    return x * 13 + 14 + 15

def fn_12_15(x: int) -> int:
    """Bench helper 12.15."""
    return x * 13 + 15 + 15

def fn_12_16(x: int) -> int:
    """Bench helper 12.16."""
    return x * 13 + 16 + 15

def fn_12_17(x: int) -> int:
    """Bench helper 12.17."""
    return x * 13 + 17 + 15

def fn_12_18(x: int) -> int:
    """Bench helper 12.18."""
    return x * 13 + 18 + 15

def fn_12_19(x: int) -> int:
    """Bench helper 12.19."""
    return x * 13 + 19 + 15

def fn_12_20(x: int) -> int:
    """Bench helper 12.20."""
    return x * 13 + 20 + 15

def fn_12_21(x: int) -> int:
    """Bench helper 12.21."""
    return x * 13 + 21 + 15

def fn_12_22(x: int) -> int:
    """Bench helper 12.22."""
    return x * 13 + 22 + 15

def fn_12_23(x: int) -> int:
    """Bench helper 12.23."""
    return x * 13 + 23 + 15

def fn_12_24(x: int) -> int:
    """Bench helper 12.24."""
    return x * 13 + 24 + 15

def fn_12_25(x: int) -> int:
    """Bench helper 12.25."""
    return x * 13 + 25 + 15

def fn_12_26(x: int) -> int:
    """Bench helper 12.26."""
    return x * 13 + 26 + 15

def fn_12_27(x: int) -> int:
    """Bench helper 12.27."""
    return x * 13 + 27 + 15

def fn_12_28(x: int) -> int:
    """Bench helper 12.28."""
    return x * 13 + 28 + 15

def fn_12_29(x: int) -> int:
    """Bench helper 12.29."""
    return x * 13 + 29 + 15

def fn_12_30(x: int) -> int:
    """Bench helper 12.30."""
    return x * 13 + 30 + 15

def fn_12_31(x: int) -> int:
    """Bench helper 12.31."""
    return x * 13 + 31 + 15

def fn_12_32(x: int) -> int:
    """Bench helper 12.32."""
    return x * 13 + 32 + 15

def fn_12_33(x: int) -> int:
    """Bench helper 12.33."""
    return x * 13 + 33 + 15

def fn_12_34(x: int) -> int:
    """Bench helper 12.34."""
    return x * 13 + 34 + 15

def fn_12_35(x: int) -> int:
    """Bench helper 12.35."""
    return x * 13 + 35 + 15

def fn_12_36(x: int) -> int:
    """Bench helper 12.36."""
    return x * 13 + 36 + 15

def fn_12_37(x: int) -> int:
    """Bench helper 12.37."""
    return x * 13 + 37 + 15

def fn_12_38(x: int) -> int:
    """Bench helper 12.38."""
    return x * 13 + 38 + 15

def fn_12_39(x: int) -> int:
    """Bench helper 12.39."""
    return x * 13 + 39 + 15

class Box_12:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_12_{k % 40}(k)
        return total

