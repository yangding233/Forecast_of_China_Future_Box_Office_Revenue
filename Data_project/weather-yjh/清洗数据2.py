import csv
import chardet
from datetime import datetime, date

# ------------------- Configuration Options -------------------
INPUT_CSV = "20241215-202512深圳天气数据.csv"
OUTPUT_CSV = "清理后_20241215-202512深圳天气数据.csv"
DATE_COLUMN = "日期"
WEEK_COLUMN = "星期"
WEATHER_COLUMN = "天气"
# 【New】 Define the name of the new column
HOLIDAY_FLAG_COLUMN = "是否法定节假日"
OUTPUT_ENCODING = "gbk"


# ------------------- Core Function -------------------
def detect_encoding(file_path):
    """Automatically detect the encoding of the source file"""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read(10000))
    encoding = result['encoding'] or 'utf-8'
    if encoding == 'gb2312':
        encoding = 'gbk'
    return encoding


def parse_date(date_str):
    """Parse the date"""
    try:
        return datetime.strptime(date_str.strip(), "%Y/%m/%d").date()
    except ValueError:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()


def process_weather(weather):
    """Handling weather: Bad weather 0, Good weather 1"""
    bad_weathers = {"中雨", "大雨", "暴雨", "雾霾", "雪"}  # Slightly expanded it
    weather = weather.strip()
    return 0 if any(bad in weather for bad in bad_weathers) else 1


def get_holiday_config():
    """Specify the specific dates of statutory holidays (including consecutive holidays after adjustment)
    Note: The "holidays" set here includes the red-sticked "holidays" on the calendar. """
    holidays = set()
    # New Year's Day: 2025/1/1
    holidays.add(date(2025, 1, 1))
    # Spring Festival: 2025/1/28 - 2025/2/4
    for day in range(28, 32):
        holidays.add(date(2025, 1, day))
    for day in range(1, 5):
        holidays.add(date(2025, 2, day))
    # Qingming Festival: 2025/4/4 - 2025/4/6
    for day in range(4, 7):
        holidays.add(date(2025, 4, day))
    # Labor Day: May 1, 2025 - May 5, 2025
    for day in range(1, 6):
        holidays.add(date(2025, 5, day))
    # Dragon Boat Festival: 2025/5/31 - 2025/6/2
    holidays.add(date(2025, 5, 31))
    holidays.add(date(2025, 6, 1))
    holidays.add(date(2025, 6, 2))
    # National Day + Mid-Autumn Festival: 2025/10/1 - 2025/10/8
    for day in range(1, 9):
        holidays.add(date(2025, 10, day))

    # Paid Leave for Returning to Work (the days marked with "Shift" on the calendar)
    adjust_work_days = {
        date(2025, 1, 26), date(2025, 2, 8),
        date(2025, 4, 27),
        date(2025, 9, 28), date(2025, 10, 11)
    }
    return holidays, adjust_work_days


def is_rest_day(date_obj, holidays, adjust_work_days):
    """Determine the values in the "Weekday" column: whether it is a rest day (1) / working day (0)
    Logic: Public holidays OR (Regular weekends AND Not taking compensatory leave and working)"""
    if date_obj in holidays:
        return 1
    if date_obj in adjust_work_days:
        return 0
    return 1 if date_obj.weekday() >= 5 else 0


def process_csv():
    input_encoding = detect_encoding(INPUT_CSV)

    # Obtain holiday configuration in advance to avoid repeated calls within the loop
    holidays_set, adjust_work_set = get_holiday_config()

    try:
        with open(INPUT_CSV, 'r', encoding=input_encoding, errors='ignore') as infile:
            dialect = csv.Sniffer().sniff(infile.read(1000))
            infile.seek(0)
            reader = csv.DictReader(infile, dialect=dialect)

            # ------------------- Modification 1: Update Table Headers -------------------
            # Retrieve the original column names and add the new column names
            fieldnames = reader.fieldnames
            if HOLIDAY_FLAG_COLUMN not in fieldnames:
                fieldnames = fieldnames + [HOLIDAY_FLAG_COLUMN]

            with open(OUTPUT_CSV, 'w', newline='', encoding=OUTPUT_ENCODING) as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()

                for row_num, row in enumerate(reader, start=2):
                    try:
                        date_str = row[DATE_COLUMN].strip()
                        date_obj = parse_date(date_str)

                        # Process the original "Weekday" column (weekends = 1, weekdays = 0)
                        row[WEEK_COLUMN] = is_rest_day(date_obj, holidays_set, adjust_work_set)

                        # Handle the original "Weather" column
                        row[WEATHER_COLUMN] = process_weather(row[WEATHER_COLUMN])

                        # ------------------- Modification 2: Calculating the values of the new column -------------------
                        # If the date is in the holidays set, it is a legal holiday (1), otherwise it is (0)
                        # Note: Ordinary weekends are 0, only the red holidays are 1
                        is_statutory = 1 if date_obj in holidays_set else 0
                        row[HOLIDAY_FLAG_COLUMN] = is_statutory

                        writer.writerow(row)

                    except Exception as e:
                        print(f"第{row_num}行处理失败：{e}，跳过")

        print(f"✅ 处理完成！")
        print(f"📄 输出文件：{OUTPUT_CSV}")
        print(f"➕ 已新增列：[{HOLIDAY_FLAG_COLUMN}] (1=法定节假日, 0=其他)")
        print(f"🔄 已更新列：[{WEEK_COLUMN}] (1=休息, 0=上班)")

    except Exception as e:
        print(f"❌ 程序出错：{e}")


if __name__ == "__main__":
    process_csv()