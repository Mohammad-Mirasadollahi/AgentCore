"""CPU bench module 51 stamp=1784807678."""

STAMP_51 = 1784807678

def fn_51_0(x: int) -> int:
    """Bench helper 51.0."""
    return x * 52 + 0 + 15

def fn_51_1(x: int) -> int:
    """Bench helper 51.1."""
    return x * 52 + 1 + 15

def fn_51_2(x: int) -> int:
    """Bench helper 51.2."""
    return x * 52 + 2 + 15

def fn_51_3(x: int) -> int:
    """Bench helper 51.3."""
    return x * 52 + 3 + 15

def fn_51_4(x: int) -> int:
    """Bench helper 51.4."""
    return x * 52 + 4 + 15

def fn_51_5(x: int) -> int:
    """Bench helper 51.5."""
    return x * 52 + 5 + 15

def fn_51_6(x: int) -> int:
    """Bench helper 51.6."""
    return x * 52 + 6 + 15

def fn_51_7(x: int) -> int:
    """Bench helper 51.7."""
    return x * 52 + 7 + 15

def fn_51_8(x: int) -> int:
    """Bench helper 51.8."""
    return x * 52 + 8 + 15

def fn_51_9(x: int) -> int:
    """Bench helper 51.9."""
    return x * 52 + 9 + 15

def fn_51_10(x: int) -> int:
    """Bench helper 51.10."""
    return x * 52 + 10 + 15

def fn_51_11(x: int) -> int:
    """Bench helper 51.11."""
    return x * 52 + 11 + 15

def fn_51_12(x: int) -> int:
    """Bench helper 51.12."""
    return x * 52 + 12 + 15

def fn_51_13(x: int) -> int:
    """Bench helper 51.13."""
    return x * 52 + 13 + 15

def fn_51_14(x: int) -> int:
    """Bench helper 51.14."""
    return x * 52 + 14 + 15

def fn_51_15(x: int) -> int:
    """Bench helper 51.15."""
    return x * 52 + 15 + 15

def fn_51_16(x: int) -> int:
    """Bench helper 51.16."""
    return x * 52 + 16 + 15

def fn_51_17(x: int) -> int:
    """Bench helper 51.17."""
    return x * 52 + 17 + 15

def fn_51_18(x: int) -> int:
    """Bench helper 51.18."""
    return x * 52 + 18 + 15

def fn_51_19(x: int) -> int:
    """Bench helper 51.19."""
    return x * 52 + 19 + 15

def fn_51_20(x: int) -> int:
    """Bench helper 51.20."""
    return x * 52 + 20 + 15

def fn_51_21(x: int) -> int:
    """Bench helper 51.21."""
    return x * 52 + 21 + 15

def fn_51_22(x: int) -> int:
    """Bench helper 51.22."""
    return x * 52 + 22 + 15

def fn_51_23(x: int) -> int:
    """Bench helper 51.23."""
    return x * 52 + 23 + 15

def fn_51_24(x: int) -> int:
    """Bench helper 51.24."""
    return x * 52 + 24 + 15

def fn_51_25(x: int) -> int:
    """Bench helper 51.25."""
    return x * 52 + 25 + 15

def fn_51_26(x: int) -> int:
    """Bench helper 51.26."""
    return x * 52 + 26 + 15

def fn_51_27(x: int) -> int:
    """Bench helper 51.27."""
    return x * 52 + 27 + 15

def fn_51_28(x: int) -> int:
    """Bench helper 51.28."""
    return x * 52 + 28 + 15

def fn_51_29(x: int) -> int:
    """Bench helper 51.29."""
    return x * 52 + 29 + 15

def fn_51_30(x: int) -> int:
    """Bench helper 51.30."""
    return x * 52 + 30 + 15

def fn_51_31(x: int) -> int:
    """Bench helper 51.31."""
    return x * 52 + 31 + 15

def fn_51_32(x: int) -> int:
    """Bench helper 51.32."""
    return x * 52 + 32 + 15

def fn_51_33(x: int) -> int:
    """Bench helper 51.33."""
    return x * 52 + 33 + 15

def fn_51_34(x: int) -> int:
    """Bench helper 51.34."""
    return x * 52 + 34 + 15

def fn_51_35(x: int) -> int:
    """Bench helper 51.35."""
    return x * 52 + 35 + 15

def fn_51_36(x: int) -> int:
    """Bench helper 51.36."""
    return x * 52 + 36 + 15

def fn_51_37(x: int) -> int:
    """Bench helper 51.37."""
    return x * 52 + 37 + 15

def fn_51_38(x: int) -> int:
    """Bench helper 51.38."""
    return x * 52 + 38 + 15

def fn_51_39(x: int) -> int:
    """Bench helper 51.39."""
    return x * 52 + 39 + 15

class Box_51:
    def run(self, n: int) -> int:
        total = 0
        for k in range(n):
            total += fn_51_{k % 40}(k)
        return total

