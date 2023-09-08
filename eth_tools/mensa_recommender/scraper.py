"""
URLs come in the form of:
https://ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene/offerWeek.html?
language=en&date=2023-09-04&id=4
id=4 is Clausiusbar; id=12 is Polyterrasse
date=2023-09-04 date within the week of the menu
"""

import datetime


MENSA_MAP = dict(
    clausiusbar=4,
    foodtrailer=9,
    polyterrasse=12,
    polysnack=13,
    tannenbar=14,
)


def convert_date(date):
    """Converts a datetime.date object to a string in the format YYYY-MM-DD"""
    return date.strftime("%Y-%m-%d")


def get_mensa_url_week(mensa, date=datetime.date.today()):
    """Returns the URL for the given mensa and date"""
    return ("https://ethz.ch/de/campus/erleben/gastronomie-und-einkaufen/gastronomie/menueplaene" +
            f"/offerWeek.html?language=en&date={convert_date(date)}&id={MENSA_MAP[mensa]}")


def parse_mensa_week(mensa, date=datetime.date.today()):
    """Parses the menu for the given mensa and date"""
    url = get_mensa_url_week(mensa, date)
    # TODO : parse the menu
    return [
        {
            "day": "monday",
            "menus": [
                {
                    "type": "garden",
                    "name": "bleble_curry",
                    "price": [6.5, 7.5, 7.5],
                    "description": "bleble",
                    "allergens": ["gluten", "lactose"],
                },
                {
                    "type": "local",
                    "name": "bleble_curry",
                    "price": [6.5, 7.5, 7.5],
                    "description": "bleble",
                    "allergens": ["gluten", "lactose"],
                }
            ]
        },
        {
            "day": "tuesday",
            "menus": [
                {
                    "type": "garden",
                    "name": "bleble_curry",
                    "price": [6.5, 7.5, 7.5],
                    "description": "bleble",
                    "allergens": ["gluten", "lactose"],
                },
                {
                    "type": "local",
                    "name": "bleble_curry",
                    "price": [6.5, 7.5, 7.5],
                    "description": "bleble",
                    "allergens": ["gluten", "lactose"],
                }
            ]
        },
        # ...
    ]
