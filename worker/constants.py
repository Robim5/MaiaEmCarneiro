""" constantes partilhadas pelo worker """

TABLE_NAME = "flight_monthly_rollup"
AIRLABS_SCHEDULES_URL = "https://airlabs.co/api/v9/schedules"
# Tem de ser string: os.getenv só aceita default string; parse_schedule_times usa .split(",")
DEFAULT_SCHEDULE_TIMES = "12:00,23:50"
