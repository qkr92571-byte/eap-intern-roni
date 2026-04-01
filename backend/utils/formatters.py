"""
공통 포맷팅 유틸리티
"""


def format_currency(amount: int) -> str:
    """금액을 읽기 쉬운 한국어 형식으로 포맷팅 (예: 1억 5천만원)"""
    if amount is None:
        return "0원"
    if amount < 10000:
        return f"{amount:,}원"

    result = []
    eok = amount // 100_000_000
    if eok > 0:
        result.append(f"{eok}억")
        amount %= 100_000_000
    cheonman = amount // 10_000_000
    if cheonman > 0:
        result.append(f"{cheonman}천만")
        amount %= 10_000_000
    man = amount // 10_000
    if man > 0:
        result.append(f"{man}만")
        amount %= 10_000
    if amount > 0:
        result.append(f"{amount:,}")

    return " ".join(result) + "원"
