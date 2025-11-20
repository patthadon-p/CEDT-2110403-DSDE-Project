import datetime


def get_buddhist_year() -> str:
    current_datetime = datetime.datetime.now()
    buddhist_year = current_datetime.year + 542
    last_two_digits = str(buddhist_year)

    return last_two_digits
