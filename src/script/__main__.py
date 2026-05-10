import psycopg

from .deals_fetcher import fetch_deals
from .deals_repository import DealsRepository


def main() -> None:
    deals = fetch_deals()

    with psycopg.connect() as conn:
        DealsRepository(conn).update(deals)


if __name__ == "__main__":
    main()
