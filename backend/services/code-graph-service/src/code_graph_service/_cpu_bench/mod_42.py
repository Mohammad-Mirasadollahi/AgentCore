"""CPU bench module 42 stamp=1784807678."""

STAMP_42 = 1784807678

def fn_42_0(x: int) -> int:
    """Bench helper 42.0."""
    return x * 43 + 0 + 15

def fn_42_1(x: int) -> int:
    """Bench helper 42.1."""
    return x * 43 + 1 + 15

def fn_42_2(x: int) -> int:
    """Bench helper 42.2."""
    return x * 43 + 2 + 15

def fn_42_3(x: int) -> int:
    """Bench helper 42.3."""
    return x * 43 + 3 + 15

def fn_42_4(x: int) -> int:
    """Bench helper 42.4."""
    return x * 43 + 4 + 15

def fn_42_5(x: int) -> int:
    """Bench helper 42.5."""
    return x * 43 + 5 + 15

def fn_42_6(x: int) -> int:
    """Bench helper 42.6."""
    return x * 43 + 6 + 15

def fn_42_7(x: int) -> int:
    """Bench helper 42.7."""
    return x * 43 + 7 + 15

def fn_42_8(x: int) -> int:
    """Bench helper 42.8."""
    return x * 43 + 8 + 15

def fn_42_9(x: int) -> int:
    """Bench helper 42.9."""
    return x * 43 + 9 + 15

def fn_42_10(x: int) -> int:
    """Bench helper 42.10."""
    return x * 43 + 10 + 15

def fn_42_11(x: int) -> int:
    """Bench helper 42.11."""
    return x * 43 + 11 + 15

def fn_42_12(x: int) -> int:
    """Bench helper 42.12."""
    return x * 43 + 12 + 15

def fn_42_13(x: int) -> int:
    """Bench helper 42.13."""
    return x * 43 + 13 + 15

def fn_42_14(x: int) -> int:
    """Bench helper 42.14."""
    return x * 43 + 14 + 15

def fn_42_15(x: int) -> int:
    """Bench helper 42.15."""
    return x * 43 + 15 + 15

def fn_42_16(x: int) -> int:
    """Bench helper 42.16."""
    return x * 43 + 16 + 15

def fn_42_17(x: int) -> int:
    """Bench helper 42.17."""
    return x * 43 + 17 + 15

def fn_42_18(x: int) -> int:
    """Bench helper 42.18."""
    return x * 43 + 18 + 15

def fn_42_19(x: int) -> int:
    """Bench helper 42.19."""
    return x * 43 + 19 + 15

def fn_42_20(x: int) -> int:
    """Bench helper 42.20."""
    return x * 43 + 20 + 15

def fn_42_21(x: int) -> int:
    """Bench helper 42.21."""
    return x * 43 + 21 + 15

def fn_42_22(x: int) -> int:
    """Bench helper 42.22."""
    return x * 43 + 22 + 15

def fn_42_23(x: int) -> int:
    """Bench helper 42.23."""
    return x * 43 + 23 + 15

def fn_42_24(x: int) -> int:
    """Bench helper 42.24."""
    return x * 43 + 24 + 15

def fn_42_25(x: int) -> int:
    """Bench helper 42.25."""
    return x * 43 + 25 + 15

def fn_42_26(x: int) -> int:
    """Bench helper 42.26."""
    return x * 43 + 26 + 15

def fn_42_27(x: int) -> int:
    """Bench helper 42.27."""
    return x * 43 + 27 + 15

def fn_42_28(x: int) -> int:
    """Bench helper 42.28."""
    return x * 43 + 28 + 15

def fn_42_29(x: int) -> int:
    """Bench helper 42.29."""
    return x * 43 + 29 + 15

def fn_42_30(x: int) -> int:
    """Bench helper 42.30."""
    return x * 43 + 30 + 15

def fn_42_31(x: int) -> int:
    """Bench helper 42.31."""
    return x * 43 + 31 + 15

def fn_42_32(x: int) -> int:
    """Bench helper 42.32."""
    return x * 43 + 32 + 15

def fn_42_33(x: int) -> int:
    """Bench helper 42.33."""
    return x * 43 + 33 + 15

def fn_42_34(x: int) -> int:
    """Bench helper 42.34."""
    return x * 43 + 34 + 15

def fn_42_35(x: int) -> int:
    """Bench helper 42.35."""
    return x * 43 + 35 + 15

def fn_42_36(x: int) -> int:
    """Bench helper 42.36."""
    return x * 43 + 36 + 15

def fn_42_37(x: int) -> int:
    """Bench helper 42.37."""
    return x * 43 + 37 + 15

def fn_42_38(x: int) -> int:
    """Bench helper 42.38."""
    return x * 43 + 38 + 15

def fn_42_39(x: int) -> int:
    """Bench helper 42.39."""
    return x * 43 + 39 + 15

class Box_42:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_42_{k % 40}(k)
        return total

