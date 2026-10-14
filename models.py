import sqlite3
import warnings
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from category_encoders import OneHotEncoder, OrdinalEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.tree import DecisionTreeClassifier
import pickle

warnings.simplefilter(action="ignore", category=FutureWarning)

def wrangle(db_path):
    # Connect to database
    conn = sqlite3.connect(db_path)

    # Construct query
    query = """
        SELECT distinct(i.building_id) AS b_id,
           s.*,
           d.damage_grade
        FROM id_map AS i
        JOIN building_structure AS s ON i.building_id = s.building_id
        JOIN building_damage AS d ON i.building_id = d.building_id
        WHERE district_id = 4
    """
    df = pd.read_sql(query, conn, index_col="b_id")

    # Features to drop or transform
    col = [col for col in df.columns if "post_eq" in col]
    df["damage_grade"] = df["damage_grade"].str[-1].astype(int)
    df["severe_damage"] = (df["damage_grade"] > 3).astype(int)
    
    col.extend(["damage_grade", "count_floors_pre_eq", "building_id"])
    df.drop(columns=[c for c in col if c in df.columns], inplace=True)

    # Outlier handling
    mean_age = round(df["age_building"].mean(), 2)
    mean_plinth_area = round(df["plinth_area_sq_ft"].mean(), 2)
    df.loc[df["age_building"] > 200, "age_building"] = mean_age 
    df.loc[df["plinth_area_sq_ft"] > 2000, "plinth_area_sq_ft"] = mean_plinth_area
 
    return df

# --- 1. PREPARATION ---
df = wrangle("Database/nepal.sqlite")
target = "severe_damage"
X = df[["superstructure", "foundation_type", "age_building", "other_floor_type", "plinth_area_sq_ft"]]
y = df[target]

# Split for validation purposes
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- 2. LOGISTIC REGRESSION (Validation Phase) ---
lr_model = make_pipeline(
    OneHotEncoder(use_cat_names=True),
    LogisticRegression(max_iter=1000)
)
lr_model.fit(X_train, y_train)

print(f"LR Test Accuracy: {round(lr_model.score(X_test, y_test), 2)}")

# --- 3. DECISION TREE (Validation Phase) ---
dt_model = make_pipeline(
    OrdinalEncoder(), 
    DecisionTreeClassifier(max_depth=5, random_state=42)
)
dt_model.fit(X_train, y_train)

print(f"DT Test Accuracy: {round(dt_model.score(X_test, y_test), 2)}")

# --- 4. FINAL PRODUCTION TRAINING (The Industry Standard) ---
# Now that we know the models are good, we retrain on 100% of the data
# This ensures the pickled models have seen all available patterns.

print("\n--- Retraining final models on full dataset for production ---")

# Retrain Logistic Regression on full X and y
lr_model.fit(X, y)

# Retrain Decision Tree on full X and y
dt_model.fit(X, y)

# --- 5. SAVING MODELS ---
# These .pkl files now contain models trained on the FULL dataset
pickle.dump(dt_model, open('decision_tree.pkl', 'wb'))
pickle.dump(lr_model, open('logistic_regression.pkl', 'wb'))

print("Success: Final models trained on full data and saved as .pkl files! 🏆")