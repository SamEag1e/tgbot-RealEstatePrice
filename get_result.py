"""
This module handles making the URL and getting required data from it.

Function:
    - request_to_webapp: Requests to website based on filters and 
        returns required data.
Third party import:
    - bs4: BeautifulSoup library for parsing HTML documents.
Local import:
    - cfg: Configuration settings for the module.
"""

import requests

from bs4 import BeautifulSoup

from cfg import REQ_URL


def request_to_webapp(filters: dict):
    """Requests to website based on filters and returns required data.
    Arg:
        filters (dict): A dict containing all the filters for GET method.
    returns:
        str: Main part of #result_section in response.
    """
    url = _query_maker(filters)
    return _parse_response(requests.get(url=url, timeout=10))


def _query_maker(filters: dict) -> str:
    query = REQ_URL
    query += f'?days={filters["days"]}&category={filters["category"]}'
    query += f'&city={filters["city"]}&district={filters["district"]}'
    if filters["category"] == "Apartment":
        for filter_ in filters["details"]:
            if "طبقه" in filter_:
                query += f"&apr_floor_number={filter_[1]}"
            elif "کل طبقات" in filter_:
                query += f"&apr_total_floors={filter_[1]}"
            elif "ساخت" in filter_:
                query += f"&apr_production_year={filter_[1]}"
            elif "اتاق" in filter_:
                query += f"&apr_rooms={filter_[1]}"
            elif "آسانسور" in filter_:
                query += "&elevator=on"
            elif "پارکینگ" in filter_:
                query += "&parking=on"
            elif "انباری" in filter_:
                query += "&storeroom=on"

    elif filters["category"] == "Villa":
        for filter_ in filters["details"]:
            if "ساخت" in filter_:
                query += f"&villa_production_year={filter_[1]}"
            elif "اتاق" in filter_:
                query += f"&villa_rooms={filter_[1]}"
            elif "بالکن" in filter_:
                query += "&balcony=on"
            elif "پارکینگ" in filter_:
                query += "&parking=on"
            elif "انباری" in filter_:
                query += "&storeroom=on"
    return query


def _parse_response(response) -> str:
    soup = BeautifulSoup(response.text, "html.parser")
    div = soup.find(
        "div", class_="container text-center my-5 p-5 reuslt-section"
    )
    for b in div.find_all("b"):
        b.insert_before("*")
        b.insert_after("*")
        b.unwrap()
    return div.get_text(separator=" ", strip=False)
