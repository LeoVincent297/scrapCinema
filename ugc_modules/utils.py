from datetime import datetime

def format_time(time_str):
    return datetime.strptime(time_str.strip(), '%H:%M').strftime('%Hh%M') 