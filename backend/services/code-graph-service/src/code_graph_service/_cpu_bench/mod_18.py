"""CPU bench module 18 stamp=1784807678."""

STAMP_18 = 1784807678

def fn_18_0(x: int) -> int:
    """Bench helper 18.0."""
    return x * 19 + 0 + 15

def fn_18_1(x: int) -> int:
    """Bench helper 18.1."""
    return x * 19 + 1 + 15

def fn_18_2(x: int) -> int:
    """Bench helper 18.2."""
    return x * 19 + 2 + 15

def fn_18_3(x: int) -> int:
    """Bench helper 18.3."""
    return x * 19 + 3 + 15

def fn_18_4(x: int) -> int:
    """Bench helper 18.4."""
    return x * 19 + 4 + 15

def fn_18_5(x: int) -> int:
    """Bench helper 18.5."""
    return x * 19 + 5 + 15

def fn_18_6(x: int) -> int:
    """Bench helper 18.6."""
    return x * 19 + 6 + 15

def fn_18_7(x: int) -> int:
    """Bench helper 18.7."""
    return x * 19 + 7 + 15

def fn_18_8(x: int) -> int:
    """Bench helper 18.8."""
    return x * 19 + 8 + 15

def fn_18_9(x: int) -> int:
    """Bench helper 18.9."""
    return x * 19 + 9 + 15

def fn_18_10(x: int) -> int:
    """Bench helper 18.10."""
    return x * 19 + 10 + 15

def fn_18_11(x: int) -> int:
    """Bench helper 18.11."""
    return x * 19 + 11 + 15

def fn_18_12(x: int) -> int:
    """Bench helper 18.12."""
    return x * 19 + 12 + 15

def fn_18_13(x: int) -> int:
    """Bench helper 18.13."""
    return x * 19 + 13 + 15

def fn_18_14(x: int) -> int:
    """Bench helper 18.14."""
    return x * 19 + 14 + 15

def fn_18_15(x: int) -> int:
    """Bench helper 18.15."""
    return x * 19 + 15 + 15

def fn_18_16(x: int) -> int:
    """Bench helper 18.16."""
    return x * 19 + 16 + 15

def fn_18_17(x: int) -> int:
    """Bench helper 18.17."""
    return x * 19 + 17 + 15

def fn_18_18(x: int) -> int:
    """Bench helper 18.18."""
    return x * 19 + 18 + 15

def fn_18_19(x: int) -> int:
    """Bench helper 18.19."""
    return x * 19 + 19 + 15

def fn_18_20(x: int) -> int:
    """Bench helper 18.20."""
    return x * 19 + 20 + 15

def fn_18_21(x: int) -> int:
    """Bench helper 18.21."""
    return x * 19 + 21 + 15

def fn_18_22(x: int) -> int:
    """Bench helper 18.22."""
    return x * 19 + 22 + 15

def fn_18_23(x: int) -> int:
    """Bench helper 18.23."""
    return x * 19 + 23 + 15

def fn_18_24(x: int) -> int:
    """Bench helper 18.24."""
    return x * 19 + 24 + 15

def fn_18_25(x: int) -> int:
    """Bench helper 18.25."""
    return x * 19 + 25 + 15

def fn_18_26(x: int) -> int:
    """Bench helper 18.26."""
    return x * 19 + 26 + 15

def fn_18_27(x: int) -> int:
    """Bench helper 18.27."""
    return x * 19 + 27 + 15

def fn_18_28(x: int) -> int:
    """Bench helper 18.28."""
    return x * 19 + 28 + 15

def fn_18_29(x: int) -> int:
    """Bench helper 18.29."""
    return x * 19 + 29 + 15

def fn_18_30(x: int) -> int:
    """Bench helper 18.30."""
    return x * 19 + 30 + 15

def fn_18_31(x: int) -> int:
    """Bench helper 18.31."""
    return x * 19 + 31 + 15

def fn_18_32(x: int) -> int:
    """Bench helper 18.32."""
    return x * 19 + 32 + 15

def fn_18_33(x: int) -> int:
    """Bench helper 18.33."""
    return x * 19 + 33 + 15

def fn_18_34(x: int) -> int:
    """Bench helper 18.34."""
    return x * 19 + 34 + 15

def fn_18_35(x: int) -> int:
    """Bench helper 18.35."""
    return x * 19 + 35 + 15

def fn_18_36(x: int) -> int:
    """Bench helper 18.36."""
    return x * 19 + 36 + 15

def fn_18_37(x: int) -> int:
    """Bench helper 18.37."""
    return x * 19 + 37 + 15

def fn_18_38(x: int) -> int:
    """Bench helper 18.38."""
    return x * 19 + 38 + 15

def fn_18_39(x: int) -> int:
    """Bench helper 18.39."""
    return x * 19 + 39 + 15

class Box_18:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_18_{k % 40}(k)
        return total

