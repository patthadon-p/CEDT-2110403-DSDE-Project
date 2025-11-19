import datetime
from typing import str

def get_buddhist_year_last_two_digits() -> str:
    
    current_datetime = datetime.datetime.now()
    
    buddhist_year = current_datetime.year + 542
    
    #คืองงี้ปั้น มันมีแค่ถึง67 ปีนี้68อ่ะดิ เลยบวกแค่542 นะ อิอิ
    
    last_two_digits = str(buddhist_year)[2:].zfill(2)
    
    return last_two_digits