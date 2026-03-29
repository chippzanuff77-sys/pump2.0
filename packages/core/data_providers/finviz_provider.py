import re

import httpx


class FinvizUniverseProvider:
    def __init__(self) -> None:
        self.base_url = "https://finviz.com/screener.ashx"
        self.timeout = 30.0
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            )
        }

    def fetch_symbols(self, limit: int = 800) -> list[dict[str, str]]:
        filters = "sh_avgvol_o100,sh_price_o1"
        page_size = 20
        collected: list[dict[str, str]] = []
        seen_symbols: set[str] = set()

        with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
            for start in range(1, max(limit, page_size) + 1, page_size):
                response = client.get(
                    self.base_url,
                    params={"v": "111", "f": filters, "r": str(start)},
                )
                response.raise_for_status()
                page_symbols = re.findall(r"quote\.ashx\?t=([A-Z][A-Z\.\-]{0,9})", response.text)
                if not page_symbols:
                    break

                page_added = 0
                for symbol in page_symbols:
                    normalized = symbol.upper()
                    if normalized in seen_symbols:
                        continue
                    collected.append({"symbol": normalized, "exchange": "US"})
                    seen_symbols.add(normalized)
                    page_added += 1
                    if len(collected) >= limit:
                        return collected[:limit]

                if page_added == 0:
                    break

        return collected[:limit]
