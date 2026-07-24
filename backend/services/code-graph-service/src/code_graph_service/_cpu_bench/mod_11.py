"""CPU bench module 11 stamp=1784807678."""

STAMP_11 = 1784807678

def fn_11_0(x: int) -> int:
    """Bench helper 11.0."""
    return x * 12 + 0 + 15

def fn_11_1(x: int) -> int:
    """Bench helper 11.1."""
    return x * 12 + 1 + 15

def fn_11_2(x: int) -> int:
    """Bench helper 11.2."""
    return x * 12 + 2 + 15

def fn_11_3(x: int) -> int:
    """Bench helper 11.3."""
    return x * 12 + 3 + 15

def fn_11_4(x: int) -> int:
    """Bench helper 11.4."""
    return x * 12 + 4 + 15

def fn_11_5(x: int) -> int:
    """Bench helper 11.5."""
    return x * 12 + 5 + 15

def fn_11_6(x: int) -> int:
    """Bench helper 11.6."""
    return x * 12 + 6 + 15

def fn_11_7(x: int) -> int:
    """Bench helper 11.7."""
    return x * 12 + 7 + 15

def fn_11_8(x: int) -> int:
    """Bench helper 11.8."""
    return x * 12 + 8 + 15

def fn_11_9(x: int) -> int:
    """Bench helper 11.9."""
    return x * 12 + 9 + 15

def fn_11_10(x: int) -> int:
    """Bench helper 11.10."""
    return x * 12 + 10 + 15

def fn_11_11(x: int) -> int:
    """Bench helper 11.11."""
    return x * 12 + 11 + 15

def fn_11_12(x: int) -> int:
    """Bench helper 11.12."""
    return x * 12 + 12 + 15

def fn_11_13(x: int) -> int:
    """Bench helper 11.13."""
    return x * 12 + 13 + 15

def fn_11_14(x: int) -> int:
    """Bench helper 11.14."""
    return x * 12 + 14 + 15

def fn_11_15(x: int) -> int:
    """Bench helper 11.15."""
    return x * 12 + 15 + 15

def fn_11_16(x: int) -> int:
    """Bench helper 11.16."""
    return x * 12 + 16 + 15

def fn_11_17(x: int) -> int:
    """Bench helper 11.17."""
    return x * 12 + 17 + 15

def fn_11_18(x: int) -> int:
    """Bench helper 11.18."""
    return x * 12 + 18 + 15

def fn_11_19(x: int) -> int:
    """Bench helper 11.19."""
    return x * 12 + 19 + 15

def fn_11_20(x: int) -> int:
    """Bench helper 11.20."""
    return x * 12 + 20 + 15

def fn_11_21(x: int) -> int:
    """Bench helper 11.21."""
    return x * 12 + 21 + 15

def fn_11_22(x: int) -> int:
    """Bench helper 11.22."""
    return x * 12 + 22 + 15

def fn_11_23(x: int) -> int:
    """Bench helper 11.23."""
    return x * 12 + 23 + 15

def fn_11_24(x: int) -> int:
    """Bench helper 11.24."""
    return x * 12 + 24 + 15

def fn_11_25(x: int) -> int:
    """Bench helper 11.25."""
    return x * 12 + 25 + 15

def fn_11_26(x: int) -> int:
    """Bench helper 11.26."""
    return x * 12 + 26 + 15

def fn_11_27(x: int) -> int:
    """Bench helper 11.27."""
    return x * 12 + 27 + 15

def fn_11_28(x: int) -> int:
    """Bench helper 11.28."""
    return x * 12 + 28 + 15

def fn_11_29(x: int) -> int:
    """Bench helper 11.29."""
    return x * 12 + 29 + 15

def fn_11_30(x: int) -> int:
    """Bench helper 11.30."""
    return x * 12 + 30 + 15

def fn_11_31(x: int) -> int:
    """Bench helper 11.31."""
    return x * 12 + 31 + 15

def fn_11_32(x: int) -> int:
    """Bench helper 11.32."""
    return x * 12 + 32 + 15

def fn_11_33(x: int) -> int:
    """Bench helper 11.33."""
    return x * 12 + 33 + 15

def fn_11_34(x: int) -> int:
    """Bench helper 11.34."""
    return x * 12 + 34 + 15

def fn_11_35(x: int) -> int:
    """Bench helper 11.35."""
    return x * 12 + 35 + 15

def fn_11_36(x: int) -> int:
    """Bench helper 11.36."""
    return x * 12 + 36 + 15

def fn_11_37(x: int) -> int:
    """Bench helper 11.37."""
    return x * 12 + 37 + 15

def fn_11_38(x: int) -> int:
    """Bench helper 11.38."""
    return x * 12 + 38 + 15

def fn_11_39(x: int) -> int:
    """Bench helper 11.39."""
    return x * 12 + 39 + 15

class Box_11:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_11_{k % 40}(k)
        return total

