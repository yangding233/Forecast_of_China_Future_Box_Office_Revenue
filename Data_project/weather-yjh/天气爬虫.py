import requests
import parsel
import csv
import execjs
from datetime import datetime

# -------------------------- Configuration Constants --------------------------
CITY = "shenzhen"  # Target City (Can be changed to Beijing, Shanghai, etc.)
JS_FILE_PATH = "天气.js"  # Path of the JS file for encryption algorithm
CSV_FILE_PATH = "20241215-202512深圳天气数据.csv"  # Output CSV file path

# Time Range Configuration
START_MONTH = 202412  # Starting month (December 2024)
END_MONTH = 202512  # End month (December 2025)

# Request Headers (It is recommended to regularly update cookies to avoid expiration)
headers = {
    'cookie': 'UserId=17653456165230907; Hm_lvt_30606b57e40fddacb2c26d2b789efbcb=1765345632; Hm_lvt_7c50c7060f1f743bccf8c150a646e90a=1765345617,1765433213; HMACCOUNT=A431BD1F735966EC; Hm_lpvt_7c50c7060f1f743bccf8c150a646e90a=1765433695',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0'
}


def get_month_list(start_month, end_month):
    """Generate the list of months to be scraped (such as 202412, 202501... 202512)"""
    month_list = []
    current_year = start_month // 100
    current_month = start_month % 100

    while True:
        # Concatenate the current month identifier (such as 202412)
        current_month_str = current_year * 100 + current_month
        month_list.append(current_month_str)

        # Determine if it has reached the end month
        if current_month_str == end_month:
            break

        # Monthly Increment (Handling the transition from December to January of the following year)
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    return month_list


def crawl_latter_half_month(month_str, city, js_context, csv_writer, start_day=15):
    """
    Retrieve the data from the second half of the specified month (only for the encrypted interface), and filter out the records after the start_day
    :param month_str: Month identifier (e.g. 202412)
    :param city: City name
    :param js_context: Pre-compiled JS context
    :param csv_writer: CSV writing object
    :param start_day: Starting date (default 15th) """
    try:
        # 1. Call JavaScript to obtain the encrypted parameters
        crypte = js_context.call('GetSign', int(month_str), city)

        # 2. Construct the interface URL and send a POST request
        api_url = f"https://lishi.tianqi.com/monthdata/{city}/{month_str}"
        data = {'crypte': crypte}
        # Dynamically generate referer (to avoid anti-crawling caused by fixed referer)
        headers['referer'] = f'https://lishi.tianqi.com/{city}/{month_str}.html'
        api_response = requests.post(url=api_url, headers=headers, data=data, timeout=10)
        api_response.raise_for_status()
        json_data = api_response.json()

        # 3. Parse the JSON data and filter out the records from the 15th day and onwards
        for item in json_data:
            date_str = item.get('date_str', '')
            if not date_str:
                continue

            # Extract the "day" from the date (e.g. 2024-12-15 → 15)
            try:
                day = int(date_str.split('-')[-1])
            except (IndexError, ValueError):
                continue

            # Only keep records from the 15th and onwards
            if day >= start_day:
                dit = {
                    '日期': date_str,
                    '星期': item.get('week', '未知'),
                    '天气': item.get('weather', '未知')
                }
                csv_writer.writerow(dit)
                print(f"[{month_str}] Data screening in the latter half of the month:{dit}")

        print(f"[{month_str}] The data for the latter half of the 15th and subsequent days has been successfully retrieved!")

    except requests.exceptions.RequestException as e:
        print(f"[{month_str}] Failure in the network request in the latter half of the period.{e}")
    except Exception as e:
        print(f"[{month_str}] Data analysis for the latter half of the month failed.{e}")


def crawl_full_month(month_str, city, js_context, csv_writer):
    """
    Retrieve the full-month data for the specified month (HTML for the first half + encrypted API for the second half)
    :param month_str: Month identifier (e.g. 202501)
    :param city: City name
    :param js_context: Pre-compiled JS context
    :param csv_writer: CSV writing object """
    try:
        # -------------------------- Fetching data from the first half of the month (HTML parsing) --------------------------
        # Construct the URL of the HTML page for the current month
        html_url = f"https://lishi.tianqi.com/{city}/{month_str}.html"
        headers['referer'] = f'https://lishi.tianqi.com/{city}/{month_str}.html'
        response = requests.get(url=html_url, headers=headers, timeout=10)
        response.raise_for_status()  # Throw HTTP request exception (such as 404, 500)
        html = response.text

        # Analyze HTML
        selector = parsel.Selector(html)
        lis = selector.css('.inleft .tian_three .thrui li')

        for li in lis:
            # Extract the date and the day of the week (add non-null check to avoid index errors)
            date_text = li.css('.th200::text').get()
            if not date_text:
                continue
            date_info = date_text.split(' ')
            if len(date_info) < 2:
                continue
            date = date_info[0]
            week = date_info[1]

            # Extract weather (add length check to avoid index out-of-bounds error)
            w_info = li.css('.th140::text').getall()
            weather = w_info[2] if len(w_info) >= 3 else "未知"

            # 写入CSV
            dit = {'日期': date, '星期': week, '天气': weather}
            csv_writer.writerow(dit)
            print(f"[{month_str}] Data for the first half of the month:{dit}")

        # -------------------------- Retrieving data from the second half of the month (encrypted interface) --------------------------
        crawl_latter_half_month(month_str, city, js_context, csv_writer, start_day=1) # start_day = 1 indicates that all the data from the latter half of the month will be retained.

    except requests.exceptions.RequestException as e:
        print(f"[{month_str}] Full month of network requests failed:{e}")
    except Exception as e:
        print(f"[{month_str}] Failed to parse the full-month data:{e}")


def main():
    # 1. Generate the list of months to be crawled (202412, 202501...202512)
    month_list = get_month_list(START_MONTH, END_MONTH)
    print(f"List of months to be crawled:{month_list}")

    # 2. Initialize the CSV file (automatically close the file using the 'with' statement)
    with open(CSV_FILE_PATH, mode='w', encoding='utf-8-sig', newline='') as f:
        csv_writer = csv.DictWriter(f, fieldnames=['日期', '星期', '天气'])
        csv_writer.writeheader()

        # 3. Precompiled JavaScript Code (Compile only once to enhance efficiency)
        try:
            js_context = execjs.compile(open(JS_FILE_PATH, encoding='utf-8').read())
        except FileNotFoundError:
            print(f"Error: Unable to find the JS file {JS_FILE_PATH}")
            return
        except Exception as e:
            print(f"JS code compilation failed:{e}")
            return

        # 4. Traverse the list of months and handle each case separately
        for month_str in month_list:
            print(f"\n========== Processing begins {month_str} month ==========")
            if month_str == 202412:
                # December 2024: Only crawl the data from the second half of the month starting from the 15th
                crawl_latter_half_month(month_str, CITY, js_context, csv_writer, start_day=15)
            else:
                # 2025 Month: Fetching Data for the Entire Month
                crawl_full_month(month_str, CITY, js_context, csv_writer)

    print(f"\nData scraping completed! Saved to {CSV_FILE_PATH}")


if __name__ == "__main__":
    main()