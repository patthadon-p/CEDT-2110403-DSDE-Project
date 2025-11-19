import datetime


def get_buddhist_year_last_two_digits() -> str:
    current_datetime = datetime.datetime.now()
    buddhist_year = current_datetime.year + 542
    last_two_digits = str(buddhist_year)[2:].zfill(2)

    return last_two_digits
