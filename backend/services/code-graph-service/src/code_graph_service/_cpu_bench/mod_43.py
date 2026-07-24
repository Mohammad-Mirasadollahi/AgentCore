"""CPU bench module 43 stamp=1784807678."""

STAMP_43 = 1784807678

def fn_43_0(x: int) -> int:
    """Bench helper 43.0."""
    return x * 44 + 0 + 15

def fn_43_1(x: int) -> int:
    """Bench helper 43.1."""
    return x * 44 + 1 + 15

def fn_43_2(x: int) -> int:
    """Bench helper 43.2."""
    return x * 44 + 2 + 15

def fn_43_3(x: int) -> int:
    """Bench helper 43.3."""
    return x * 44 + 3 + 15

def fn_43_4(x: int) -> int:
    """Bench helper 43.4."""
    return x * 44 + 4 + 15

def fn_43_5(x: int) -> int:
    """Bench helper 43.5."""
    return x * 44 + 5 + 15

def fn_43_6(x: int) -> int:
    """Bench helper 43.6."""
    return x * 44 + 6 + 15

def fn_43_7(x: int) -> int:
    """Bench helper 43.7."""
    return x * 44 + 7 + 15

def fn_43_8(x: int) -> int:
    """Bench helper 43.8."""
    return x * 44 + 8 + 15

def fn_43_9(x: int) -> int:
    """Bench helper 43.9."""
    return x * 44 + 9 + 15

def fn_43_10(x: int) -> int:
    """Bench helper 43.10."""
    return x * 44 + 10 + 15

def fn_43_11(x: int) -> int:
    """Bench helper 43.11."""
    return x * 44 + 11 + 15

def fn_43_12(x: int) -> int:
    """Bench helper 43.12."""
    return x * 44 + 12 + 15

def fn_43_13(x: int) -> int:
    """Bench helper 43.13."""
    return x * 44 + 13 + 15

def fn_43_14(x: int) -> int:
    """Bench helper 43.14."""
    return x * 44 + 14 + 15

def fn_43_15(x: int) -> int:
    """Bench helper 43.15."""
    return x * 44 + 15 + 15

def fn_43_16(x: int) -> int:
    """Bench helper 43.16."""
    return x * 44 + 16 + 15

def fn_43_17(x: int) -> int:
    """Bench helper 43.17."""
    return x * 44 + 17 + 15

def fn_43_18(x: int) -> int:
    """Bench helper 43.18."""
    return x * 44 + 18 + 15

def fn_43_19(x: int) -> int:
    """Bench helper 43.19."""
    return x * 44 + 19 + 15

def fn_43_20(x: int) -> int:
    """Bench helper 43.20."""
    return x * 44 + 20 + 15

def fn_43_21(x: int) -> int:
    """Bench helper 43.21."""
    return x * 44 + 21 + 15

def fn_43_22(x: int) -> int:
    """Bench helper 43.22."""
    return x * 44 + 22 + 15

def fn_43_23(x: int) -> int:
    """Bench helper 43.23."""
    return x * 44 + 23 + 15

def fn_43_24(x: int) -> int:
    """Bench helper 43.24."""
    return x * 44 + 24 + 15

def fn_43_25(x: int) -> int:
    """Bench helper 43.25."""
    return x * 44 + 25 + 15

def fn_43_26(x: int) -> int:
    """Bench helper 43.26."""
    return x * 44 + 26 + 15

def fn_43_27(x: int) -> int:
    """Bench helper 43.27."""
    return x * 44 + 27 + 15

def fn_43_28(x: int) -> int:
    """Bench helper 43.28."""
    return x * 44 + 28 + 15

def fn_43_29(x: int) -> int:
    """Bench helper 43.29."""
    return x * 44 + 29 + 15

def fn_43_30(x: int) -> int:
    """Bench helper 43.30."""
    return x * 44 + 30 + 15

def fn_43_31(x: int) -> int:
    """Bench helper 43.31."""
    return x * 44 + 31 + 15

def fn_43_32(x: int) -> int:
    """Bench helper 43.32."""
    return x * 44 + 32 + 15

def fn_43_33(x: int) -> int:
    """Bench helper 43.33."""
    return x * 44 + 33 + 15

def fn_43_34(x: int) -> int:
    """Bench helper 43.34."""
    return x * 44 + 34 + 15

def fn_43_35(x: int) -> int:
    """Bench helper 43.35."""
    return x * 44 + 35 + 15

def fn_43_36(x: int) -> int:
    """Bench helper 43.36."""
    return x * 44 + 36 + 15

def fn_43_37(x: int) -> int:
    """Bench helper 43.37."""
    return x * 44 + 37 + 15

def fn_43_38(x: int) -> int:
    """Bench helper 43.38."""
    return x * 44 + 38 + 15

def fn_43_39(x: int) -> int:
    """Bench helper 43.39."""
    return x * 44 + 39 + 15

class Box_43:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_43_{k % 40}(k)
        return total

