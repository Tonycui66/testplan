from typing import Tuple


def normalize_pagination(page: int = 1, page_size: int = 20) -> Tuple[int, int]:
    normalized_page = max(1, page)
    normalized_page_size = min(max(1, page_size), 100)
    return normalized_page, normalized_page_size
