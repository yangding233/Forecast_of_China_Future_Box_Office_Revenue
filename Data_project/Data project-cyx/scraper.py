import os
import time
import re
import requests
import logging
import random
import pandas as pd
from io import BytesIO
from fontTools.ttLib import TTFont
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')


class FontHandler:
    def __init__(self, base_font_path):
        self.base_font_path = base_font_path

        # Standard fingerprints for digits 0-9
        self.standard_fingerprints = {
            '0': '0011111000101000011011000001100000000001110000000100000000011100000110000000011001010100000010101000',
            '1': '0000011101001011000010001000001100000000000000000000000000000000000000000000000000000000000000010001',
            '2': '0011011000101000011010100000100000001110000000111000011100000110100000101100000110000000001000000001',
            '3': '0011110100101000101011000010100001101100000111110000000001011100000001110000010100011100000010101000',
            '4': '0000010100000001000000000000000000000000000000000011000101011000010101000000000000000000000000010100',
            '5': '0100000010001000001000001010000011110000111000010100000000011100000101110000010000011100000010101000',
            '6': '0011111000011100101011100001100111101000110101000101000001010100000101101000000000011101000010110000',
            '7': '1000000001100000101000001001000000100000000101000000001000000010100000001100000001000000000101000000',
            '8': '0011011000101000101010100010101001110010011101110011000001011100000001101100110100011100000010001000',
            '9': '0011110100100000010001000001010100000100100101010100101111011100001100101000110000011000000010110000',
        }

    def glyph_to_fingerprint(self, font, glyph_name):
        try:
            glyph = font['glyf'][glyph_name]
            coordinates = glyph.getCoordinates(font['glyf'])[0]

            xs = [p[0] for p in coordinates]
            ys = [p[1] for p in coordinates]
            if not xs or not ys: return None

            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            width = max_x - min_x
            height = max_y - min_y

            if width == 0 or height == 0: return None

            grid_size = 10
            grid = [['0'] * grid_size for _ in range(grid_size)]

            for x, y in zip(xs, ys):
                # Normalize coordinates to 10x10 grid
                gx = int((x - min_x) / width * (grid_size - 1))
                gy = int((1 - (y - min_y) / height) * (grid_size - 1))

                if 0 <= gx < grid_size and 0 <= gy < grid_size:
                    grid[gy][gx] = '1'

            return "".join(["".join(row) for row in grid])

        except Exception:
            return None

    def generate_mapping(self, target_font_data):
        # Using a temporary file is not ideal but keeping logic as is
        temp_font_path = "temp_target.woff"
        with open(temp_font_path, "wb") as f:
            f.write(target_font_data)

        try:
            target_font = TTFont(BytesIO(target_font_data))
            new_map = {}

            for name in target_font.getGlyphOrder():
                if name.startswith('uni'):
                    target_fp = self.glyph_to_fingerprint(target_font, name)
                    if not target_fp: continue

                    best_num = None
                    max_score = -1

                    for num, std_fp in self.standard_fingerprints.items():
                        score = sum(1 for a, b in zip(target_fp, std_fp) if a == b and a == '1')
                        if score > max_score:
                            max_score = score
                            best_num = num

                    if best_num:
                        new_map[name.replace('uni', '').lower()] = best_num

            return new_map
        finally:
            if os.path.exists(temp_font_path):
                os.remove(temp_font_path)


class MaoyanSpider:
    def __init__(self, base_font_path='base_font.woff'):
        self.font_handler = FontHandler(base_font_path)
        self.driver = None
        self.current_font_map = {}
        self.current_font_url = None

    def start_driver(self):
        options = Options()
        # options.add_argument('--headless') # Uncomment if needed
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
            """
        })
        logging.info("WebDriver started successfully.")

    def close_driver(self):
        if self.driver:
            self.driver.quit()

    def _download_font(self, url):
        try:
            if url.startswith('//'):
                url = 'https:' + url
            resp = requests.get(url)
            if resp.status_code == 200:
                return resp.content
            else:
                logging.error(f"Font download failed: {resp.status_code}")
                return None
        except Exception as e:
            logging.error(f"Font download exception: {e}")
            return None

    def update_font_mapping(self):
        try:
            page_source = self.driver.page_source
            match = re.search(r'url\("([^"]+\.woff)"\)', page_source)
            if not match:
                match = re.search(r"url\('([^']+\.woff)'\)", page_source)

            if match:
                font_url = match.group(1)
                if font_url != self.current_font_url:
                    logging.info(f"New font URL detected: {font_url}")
                    self.current_font_url = font_url
                    font_content = self._download_font(font_url)
                    if font_content:
                        self.current_font_map = self.font_handler.generate_mapping(font_content)
                        logging.info(f"Font decryption success, mapped count: {len(self.current_font_map)}")
                    else:
                        logging.error("Failed to download font content.")
                else:
                    logging.info("Font URL unchanged, using existing mapping.")
            else:
                logging.warning("No .woff font link found in page.")

        except Exception as e:
            logging.error(f"Error updating font mapping: {e}")

    def decode_text(self, content):
        if not content or not self.current_font_map:
            return content

        result = []
        for char in content:
            char_code = ord(char)
            hex_code = hex(char_code)[2:].lower()
            if hex_code in self.current_font_map:
                result.append(str(self.current_font_map[hex_code]))
            else:
                result.append(char)
        return "".join(result)

    def clean_number(self, text):
        if not text: return "0"

        if "上映" in text:
            match = re.search(r"(\d+)", text)
            return match.group(1) if match else "0"
        if "点映" in text or "重映" in text:
            match = re.search(r"(\d+)", text)
            return match.group(1) if match else "0"

        try:
            clean_text = text.replace(',', '')
            unit_mult = 1.0
            if '亿' in clean_text:
                unit_mult = 10000.0
            elif '万' in clean_text:
                unit_mult = 1.0

            match = re.search(r"(\d+\.?\d*)", clean_text)
            if match:
                val = float(match.group(1)) * unit_mult
                return "{:.2f}".format(val)
        except:
            pass

        if '%' in text:
            match = re.search(r"(\d+\.?\d*)", text)
            return match.group(1) if match else "0"

        match = re.search(r"(\d+\.?\d*)", text)
        return match.group(1) if match else "0"

    def crawl_one_day(self, date_str):
        url = f"https://piaofang.maoyan.com/dashboard/movie?date={date_str}"
        logging.info(f"Crawling: {url}")

        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "nation-box")))

            self.update_font_mapping()

            # 1. Total Screenings
            total_screenings = "0"
            try:
                screen_el = self.driver.find_element(By.XPATH,
                                                     "//div[@class='today-dashboard-view']//p[contains(text(), '总场次')]")
                total_screenings = self.clean_number(self.decode_text(screen_el.text))
            except Exception:
                pass

            # 2. Total Box Office
            try:
                total_box_el = self.driver.find_element(By.CSS_SELECTOR, ".nation-box .mtsi-num")
                unit_el = self.driver.find_element(By.CSS_SELECTOR, ".nation-box .unit")
                raw_str = self.decode_text(total_box_el.text).strip() + unit_el.text.strip()
                total_box_str = self.clean_number(raw_str)
            except:
                total_box_str = "0"

            logging.info(f"[{date_str}] Box: {total_box_str}k, Screens: {total_screenings}k")

            # 3. Top Movies
            top_movies = []
            rows = self.driver.find_elements(By.CSS_SELECTOR, ".dashboard-table tbody tr")

            for i in range(min(3, len(rows))):
                row = rows[i]
                movie_data = {}
                tds = row.find_elements(By.TAG_NAME, "td")

                try:
                    name_el = row.find_element(By.CSS_SELECTOR, ".moviename-name")
                    movie_data['name'] = name_el.text.strip()

                    info_el = row.find_element(By.CSS_SELECTOR, ".moviename-info span:first-child")
                    movie_data['release_days'] = self.clean_number(info_el.text.strip())
                except:
                    movie_data['name'] = "Unknown"
                    movie_data['release_days'] = "0"

                try:
                    box_el = tds[1].find_element(By.CSS_SELECTOR, ".mtsi-num-pos")
                    raw_box = self.decode_text(box_el.text).strip()
                    movie_data['box_office'] = self.clean_number(raw_box)
                except:
                    movie_data['box_office'] = "0"

                movie_data['box_share'] = self.clean_number(tds[2].text.strip())

                try:
                    movie_data['screen_share'] = self.clean_number(self.decode_text(tds[4].text.strip()))
                except:
                    movie_data['screen_share'] = "0"

                try:
                    movie_data['attendance'] = self.clean_number(self.decode_text(tds[6].text.strip()))
                except:
                    movie_data['attendance'] = "0"

                movie_data['rank'] = i + 1
                top_movies.append(movie_data)

            return {
                "date": date_str,
                "total_box": total_box_str,
                "total_screenings": total_screenings,
                "top_movies": top_movies
            }

        except Exception as e:
            logging.error(f"Failed to crawl {date_str}: {e}")
            return None


def generate_date_range(end_date_str, days_back=365):
    end_date = pd.to_datetime(end_date_str)
    start_date = end_date - pd.Timedelta(days=days_back)
    return pd.date_range(start=start_date, end=end_date, freq='D').strftime('%Y-%m-%d').tolist()


def save_to_csv(data_list, filename="maoyan_data.csv"):
    df = pd.DataFrame(data_list)
    header = not os.path.exists(filename)
    df.to_csv(filename, mode='a', header=header, index=False, encoding='utf-8-sig')
    logging.info(f"Saved {len(data_list)} records to {filename}")


def main():
    spider = MaoyanSpider(base_font_path='base_font.woff')
    spider.start_driver()

    try:
        today = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        dates = generate_date_range(today, days_back=360)
        dates.reverse()

        logging.info(f"Planned to crawl {len(dates)} days...")
        buffer_data = []

        for i, date_str in enumerate(dates):
            result = spider.crawl_one_day(date_str)

            if result:
                for movie in result['top_movies']:
                    flat_data = {
                        "日期": result['date'],
                        "当日大盘(万)": result['total_box'],
                        "大盘总场次(万)": result['total_screenings'],
                        "排名": movie['rank'],
                        "影片名": movie['name'],
                        "上映天数": movie['release_days'],
                        "综合票房(万)": movie['box_office'],
                        "票房占比": movie['box_share'],
                        "排片占比": movie['screen_share'],
                        "上座率": movie['attendance']
                    }
                    buffer_data.append(flat_data)

                print(f"Success: {date_str}")
            else:
                print(f"Failed: {date_str}")

            if (i + 1) % 5 == 0 or (i + 1) == len(dates):
                if buffer_data:
                    save_to_csv(buffer_data)
                    buffer_data = []

            time.sleep(random.uniform(2, 4))

    except KeyboardInterrupt:
        logging.info("Interrupted by user, saving data...")
        if buffer_data:
            save_to_csv(buffer_data)
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        spider.close_driver()
        logging.info("Finished.")


if __name__ == "__main__":
    main()