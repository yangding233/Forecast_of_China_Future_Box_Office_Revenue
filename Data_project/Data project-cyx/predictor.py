import pandas as pd
import joblib
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta


plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def get_input(prompt, default_val):
    val = input(f"{prompt} [Default {default_val}]: ")
    if val.strip() == "":
        return default_val
    return val


def predict_bulletproof():
    print("Try to predict")

    try:
        model = joblib.load('best_model.pkl')
    except:
        print("Error: Model file not found")
        return

    # Inputs
    date_str = get_input("Start Date", "2025-12-19")
    start_date = datetime.strptime(date_str, "%Y-%m-%d")
    current_box = float(get_input("💰 Current Box Office (10k)", 13607))
    total_screens = float(get_input("📺 Total Screens (10k)", 38)) * 10000
    is_holiday = int(get_input("🎉 Is Holiday (1/0)", 0))
    weather = float(get_input("☀️ Weather Score", 4.5))

    print("-" * 30)
    print("🎥 Top 1 Data (Day 1 Input):")
    t1_share_base = float(get_input("   Top 1 Screen Share (%)", 46.5))
    t1_occu_base = float(get_input("   Top 1 Attendance (%)", 15))
    t1_days = float(get_input("   Top 1 Days Released", 1))
    t1_is_new = 1 if t1_days <= 3 else 0

    # Preparation Loop
    final_results = []
    dates_list = []
    last_val = current_box

    # Weekday Multipliers (0=Mon...6=Sun)
    occu_multipliers = {0: 0.4, 1: 0.35, 2: 0.35, 3: 0.35, 4: 0.9, 5: 1.3, 6: 1.1}
    start_weekday = start_date.weekday()
    base_factor = occu_multipliers.get(start_weekday, 1.0)

    print("\n>>> Simulating...")

    for i in range(1, 8):
        future_date = start_date + timedelta(days=i)
        wd = future_date.weekday()

        # Dynamic Simulation
        today_factor = occu_multipliers.get(wd, 0.4)
        relative_factor = today_factor / base_factor if base_factor > 0 else 1.0

        sim_t1_occu = max(t1_occu_base * relative_factor, 1.0)  # Ensure attendance > 0
        decay = 0.98 ** i

        features = pd.DataFrame([{
            'Yesterday_Box': last_val, 'Mean_3_Days': last_val, 'Mean_7_Days': last_val,
            'Has_New_Movie': t1_is_new, 'Box_Office': last_val,
            'Total_Screens': total_screens, 'Weather_Index': weather,
            'Is_Holiday': is_holiday, 'Weekday': wd + 1,
            'Top1_Share': t1_share_base * decay, 'Top1_Occu': sim_t1_occu,
            'Top2_Share': 20, 'Top2_Occu': 10 * relative_factor,
            'Top3_Share': 10, 'Top3_Occu': 8 * relative_factor
        }])

        cols = ['Yesterday_Box', 'Mean_3_Days', 'Mean_7_Days', 'Has_New_Movie',
                'Box_Office', 'Total_Screens', 'Weather_Index', 'Is_Holiday', 'Weekday',
                'Top1_Share', 'Top1_Occu', 'Top2_Share', 'Top2_Occu', 'Top3_Share', 'Top3_Occu']

        # AI Prediction
        pred = model.predict(features[cols])[0][0]

        # Business Rules (Correction Logic)
        adjusted = pred
        reason = "AI Prediction"

        # Floor Lock: Cannot be negative, cannot be below operating cost
        min_floor = 500  # 500k Floor
        if adjusted < min_floor:
            adjusted = min_floor
            reason = "Floor Rebound (Physical Lock)"

        # Friday/Saturday Rally (Fix Friday Crash)
        if not is_holiday:
            if wd == 4:  # Friday
                target = last_val * 1.2  # Rise 20%
                if adjusted < target:
                    adjusted = target
                    reason = "Friday Forced Rally"
            elif wd == 5:  # Saturday
                target = last_val * 1.3
                if adjusted < target:
                    adjusted = target
                    reason = "Saturday Explosion"

        # Weekday Plateau
        if not is_holiday and wd in [0, 1, 2, 3]:
            if wd == 0:  # Monday
                floor = last_val * 0.4
                if adjusted < floor: adjusted = floor
            else:  # Tue-Thu
                plateau = last_val * 0.9  # Max drop 10%
                if adjusted < plateau:
                    adjusted = plateau
                    reason = "Weekday Stability"

        # Double check negative
        adjusted = max(adjusted, 500.0)

        # Recording
        final_results.append(adjusted)
        dates_list.append(future_date.strftime('%m-%d'))
        last_val = adjusted

        wd_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][wd]
        print(f"[{future_date.strftime('%m-%d')} {wd_en}] {int(adjusted)}k | {reason}")

    # Plotting
    plt.figure(figsize=(10, 6))
    plot_dates = [date_str[5:]] + dates_list
    plot_vals = [current_box] + final_results

    plt.plot(plot_dates, plot_vals, marker='o', linewidth=3, color='#d62728')
    plt.scatter(plot_dates[0], plot_vals[0], s=150, c='blue')

    # Force Y-axis bottom to 0
    plt.ylim(bottom=0)

    for x, y in zip(plot_dates, plot_vals):
        plt.text(x, y + max(plot_vals) * 0.02, f'{int(y)}', ha='center', va='bottom', fontsize=10)

    plt.title(f'Future 7 Days Prediction (Final Adjusted)', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.show()


if __name__ == "__main__":
    predict_bulletproof()