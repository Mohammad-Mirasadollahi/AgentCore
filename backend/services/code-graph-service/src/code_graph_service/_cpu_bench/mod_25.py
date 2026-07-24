"""CPU bench module 25 stamp=1784807678."""

STAMP_25 = 1784807678

def fn_25_0(x: int) -> int:
    """Bench helper 25.0."""
    return x * 26 + 0 + 15

def fn_25_1(x: int) -> int:
    """Bench helper 25.1."""
    return x * 26 + 1 + 15

def fn_25_2(x: int) -> int:
    """Bench helper 25.2."""
    return x * 26 + 2 + 15

def fn_25_3(x: int) -> int:
    """Bench helper 25.3."""
    return x * 26 + 3 + 15

def fn_25_4(x: int) -> int:
    """Bench helper 25.4."""
    return x * 26 + 4 + 15

def fn_25_5(x: int) -> int:
    """Bench helper 25.5."""
    return x * 26 + 5 + 15

def fn_25_6(x: int) -> int:
    """Bench helper 25.6."""
    return x * 26 + 6 + 15

def fn_25_7(x: int) -> int:
    """Bench helper 25.7."""
    return x * 26 + 7 + 15

def fn_25_8(x: int) -> int:
    """Bench helper 25.8."""
    return x * 26 + 8 + 15

def fn_25_9(x: int) -> int:
    """Bench helper 25.9."""
    return x * 26 + 9 + 15

def fn_25_10(x: int) -> int:
    """Bench helper 25.10."""
    return x * 26 + 10 + 15

def fn_25_11(x: int) -> int:
    """Bench helper 25.11."""
    return x * 26 + 11 + 15

def fn_25_12(x: int) -> int:
    """Bench helper 25.12."""
    return x * 26 + 12 + 15

def fn_25_13(x: int) -> int:
    """Bench helper 25.13."""
    return x * 26 + 13 + 15

def fn_25_14(x: int) -> int:
    """Bench helper 25.14."""
    return x * 26 + 14 + 15

def fn_25_15(x: int) -> int:
    """Bench helper 25.15."""
    return x * 26 + 15 + 15

def fn_25_16(x: int) -> int:
    """Bench helper 25.16."""
    return x * 26 + 16 + 15

def fn_25_17(x: int) -> int:
    """Bench helper 25.17."""
    return x * 26 + 17 + 15

def fn_25_18(x: int) -> int:
    """Bench helper 25.18."""
    return x * 26 + 18 + 15

def fn_25_19(x: int) -> int:
    """Bench helper 25.19."""
    return x * 26 + 19 + 15

def fn_25_20(x: int) -> int:
    """Bench helper 25.20."""
    return x * 26 + 20 + 15

def fn_25_21(x: int) -> int:
    """Bench helper 25.21."""
    return x * 26 + 21 + 15

def fn_25_22(x: int) -> int:
    """Bench helper 25.22."""
    return x * 26 + 22 + 15

def fn_25_23(x: int) -> int:
    """Bench helper 25.23."""
    return x * 26 + 23 + 15

def fn_25_24(x: int) -> int:
    """Bench helper 25.24."""
    return x * 26 + 24 + 15

def fn_25_25(x: int) -> int:
    """Bench helper 25.25."""
    return x * 26 + 25 + 15

def fn_25_26(x: int) -> int:
    """Bench helper 25.26."""
    return x * 26 + 26 + 15

def fn_25_27(x: int) -> int:
    """Bench helper 25.27."""
    return x * 26 + 27 + 15

def fn_25_28(x: int) -> int:
    """Bench helper 25.28."""
    return x * 26 + 28 + 15

def fn_25_29(x: int) -> int:
    """Bench helper 25.29."""
    return x * 26 + 29 + 15

def fn_25_30(x: int) -> int:
    """Bench helper 25.30."""
    return x * 26 + 30 + 15

def fn_25_31(x: int) -> int:
    """Bench helper 25.31."""
    return x * 26 + 31 + 15

def fn_25_32(x: int) -> int:
    """Bench helper 25.32."""
    return x * 26 + 32 + 15

def fn_25_33(x: int) -> int:
    """Bench helper 25.33."""
    return x * 26 + 33 + 15

def fn_25_34(x: int) -> int:
    """Bench helper 25.34."""
    return x * 26 + 34 + 15

def fn_25_35(x: int) -> int:
    """Bench helper 25.35."""
    return x * 26 + 35 + 15

def fn_25_36(x: int) -> int:
    """Bench helper 25.36."""
    return x * 26 + 36 + 15

def fn_25_37(x: int) -> int:
    """Bench helper 25.37."""
    return x * 26 + 37 + 15

def fn_25_38(x: int) -> int:
    """Bench helper 25.38."""
    return x * 26 + 38 + 15

def fn_25_39(x: int) -> int:
    """Bench helper 25.39."""
    return x * 26 + 39 + 15

class Box_25:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_25_{k % 40}(k)
        return total

