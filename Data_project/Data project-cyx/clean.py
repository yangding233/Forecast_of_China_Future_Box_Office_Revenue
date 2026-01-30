import pandas as pd
import numpy as np


def process_data():
    print(">>> Step 1: Processing weather data...")
    try:
        # Load weather data (using gbk to prevent encoding errors)
        df_bj = pd.read_csv('weather_bj.csv', encoding='gbk')
        df_gz = pd.read_csv('weather_gz.csv', encoding='gbk')
        df_sh = pd.read_csv('weather_sh.csv', encoding='gbk')
        df_sz = pd.read_csv('weather_sz.csv', encoding='gbk')
    except Exception as e:
        print(f"File load error: {e}")
        return

    # Unify date format
    for df in [df_bj, df_gz, df_sh, df_sz]:
        df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')

    # Calculate weather index
    df_weather = df_bj[['日期', '星期', '是否法定节假日']].copy()

    # Calculate average across 4 cities
    df_weather['avg_score'] = (df_bj['天气'] + df_gz['天气'] + df_sh['天气'] + df_sz['天气']) / 4
    df_weather = df_weather.fillna(1)

    print(">>> Step 2: Processing box office data...")
    df_box = pd.read_csv('maoyan_data.csv')
    df_box['日期'] = pd.to_datetime(df_box['日期']).dt.strftime('%Y-%m-%d')

    # Extract daily total box office
    daily = df_box[['日期', '当日大盘(万)', '大盘总场次(万)']].drop_duplicates(subset=['日期'])

    # Extract detailed features for Top 3 movies
    for i in [1, 2, 3]:
        temp = df_box[df_box['排名'] == i][['日期', '上映天数', '排片占比', '上座率']]
        temp.columns = ['日期', f'Top{i}_Days', f'Top{i}_Share', f'Top{i}_Occu']
        daily = pd.merge(daily, temp, on='日期', how='left')

    # Merge weather
    final_df = pd.merge(daily, df_weather, on='日期', how='left').fillna(0)

    # Rename columns to English (Standardization)
    rename_dict = {
        '日期': 'Date',
        '当日大盘(万)': 'Box_Office',
        '大盘总场次(万)': 'Total_Screens',
        '星期': 'Weekday',
        '是否法定节假日': 'Is_Holiday',
        'avg_score': 'Weather_Index',
    }
    final_df.rename(columns=rename_dict, inplace=True)

    final_df.to_csv('final_data.csv', index=False, encoding='utf-8-sig')
    print("Data cleaning complete to save to final_data.csv")
    print(final_df.head(1))


if __name__ == "__main__":
    process_data()