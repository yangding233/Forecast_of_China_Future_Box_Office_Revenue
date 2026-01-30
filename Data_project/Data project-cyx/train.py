import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
import joblib


def train_model():
    print("Training...")
    try:
        df = pd.read_csv('final_data.csv')
    except:
        print("Error: final_data.csv not found")
        return

    #  Construct Core Trend Features
    df['Yesterday_Box'] = df['Box_Office'].shift(1)
    df['Mean_3_Days'] = df['Box_Office'].rolling(window=3).mean().shift(1)
    df['Mean_7_Days'] = df['Box_Office'].rolling(window=7).mean().shift(1)

    # Construct "New Movie" Feature (Has_New_Movie)
    # Logic: If Top1 days <= 2 and Screen Share > 20%, consider it a strong new release
    if 'Top1_Days' in df.columns:
        df['Has_New_Movie'] = ((df['Top1_Days'] <= 2) & (df['Top1_Share'] > 20)).astype(int)
    else:
        df['Has_New_Movie'] = 0

    # Construct Targets: Future 7 Days
    targets = []
    for i in range(1, 8):
        col = f'Future_Day_{i}'
        df[col] = df['Box_Office'].shift(-i)
        targets.append(col)

    df_clean = df.dropna()

    # Define Features (Added Top3, Removed School Holidays)
    features = [
        'Yesterday_Box', 'Mean_3_Days', 'Mean_7_Days',  # History Inertia
        'Has_New_Movie',                                # New Movie Simulation
        'Box_Office', 'Total_Screens',
        'Weather_Index',                                # Weather
        'Is_Holiday', 'Weekday',
        'Top1_Share', 'Top1_Occu',                      # Use attendance instead of score
        'Top2_Share', 'Top2_Occu',
        'Top3_Share', 'Top3_Occu'                       # Added Top3 for precision
    ]

    print(f"Training Feature List: {features}")

    X = df_clean[features]
    y = df_clean[targets]

    # Training (Shuffle to learn general patterns)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True, random_state=42)

    hgb = HistGradientBoostingRegressor(
        max_iter=500, learning_rate=0.04, max_depth=15, l2_regularization=2.0, random_state=42
    )

    model = MultiOutputRegressor(hgb)
    model.fit(X_train, y_train)

    score = model.score(X_test, y_test)
    print(f"R² Score: {score:.4f}")

    joblib.dump(model, 'best_model.pkl')
    print("saved as: best_model.pkl")


if __name__ == "__main__":
    train_model()