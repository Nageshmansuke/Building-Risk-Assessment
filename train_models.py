import pickle
import numpy as np
import pandas as pd
from category_encoders import OneHotEncoder, OrdinalEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import make_pipeline

def generate_synthetic_nepal_data(n_samples=10000, random_seed=42):
    np.random.seed(random_seed)

    superstructures = [
        'Stone, mud mortar', 'Brick, cement mortar', 'Adobe/mud',
        'Stone, cement mortar', 'RC, non-engineered', 'Timber',
        'Brick, mud mortar', 'Bamboo', 'Stone', 'RC, engineered', 'Other'
    ]
    # Vulnerability score (higher = higher risk of severe damage)
    superstructure_risk = {
        'Adobe/mud': 0.85,
        'Stone, mud mortar': 0.82,
        'Stone': 0.78,
        'Brick, mud mortar': 0.70,
        'Other': 0.55,
        'Stone, cement mortar': 0.50,
        'Timber': 0.40,
        'Bamboo': 0.38,
        'RC, non-engineered': 0.35,
        'Brick, cement mortar': 0.25,
        'RC, engineered': 0.10,
    }

    foundation_types = [
        'Mud mortar-Stone/Brick', 'RC', 'Cement-Stone/Brick',
        'Bamboo/Timber', 'Other'
    ]
    foundation_risk = {
        'Mud mortar-Stone/Brick': 0.80,
        'Other': 0.50,
        'Bamboo/Timber': 0.45,
        'Cement-Stone/Brick': 0.28,
        'RC': 0.12,
    }

    other_floor_types = [
        'TImber/Bamboo-Mud', 'Not applicable', 'Timber-Planck', 'RCC/RB/RBC'
    ]
    floor_risk = {
        'TImber/Bamboo-Mud': 0.75,
        'Not applicable': 0.50,
        'Timber-Planck': 0.40,
        'RCC/RB/RBC': 0.15,
    }

    # Generate synthetic samples
    selected_super = np.random.choice(superstructures, size=n_samples)
    selected_found = np.random.choice(foundation_types, size=n_samples)
    selected_floor = np.random.choice(other_floor_types, size=n_samples)
    ages = np.random.gamma(shape=2.5, scale=12, size=n_samples).clip(1, 150)
    plinth_areas = np.random.gamma(shape=3.0, scale=250, size=n_samples).clip(80, 1900)

    # Compute risk probability
    base_prob = (
        0.38 * np.array([superstructure_risk[s] for s in selected_super]) +
        0.32 * np.array([foundation_risk[f] for f in selected_found]) +
        0.18 * np.array([floor_risk[fl] for fl in selected_floor]) +
        0.08 * (ages / 120.0).clip(0, 1) +
        0.04 * (plinth_areas / 1500.0).clip(0, 1)
    )

    # Add small realistic noise
    noise = np.random.normal(0, 0.05, size=n_samples)
    probs = (base_prob + noise).clip(0.02, 0.98)
    severe_damage = (probs >= 0.50).astype(int)

    df = pd.DataFrame({
        'superstructure': selected_super,
        'foundation_type': selected_found,
        'age_building': np.round(ages, 1),
        'other_floor_type': selected_floor,
        'plinth_area_sq_ft': np.round(plinth_areas, 1),
        'severe_damage': severe_damage
    })

    return df

def train_and_save():
    print("Generating comprehensive dataset representing Nepal earthquake building vulnerabilities...")
    df = generate_synthetic_nepal_data(n_samples=12000)
    
    X = df[["superstructure", "foundation_type", "age_building", "other_floor_type", "plinth_area_sq_ft"]]
    y = df["severe_damage"]

    print("Training Logistic Regression pipeline...")
    lr_model = make_pipeline(
        OneHotEncoder(use_cat_names=True, handle_unknown='value'),
        LogisticRegression(max_iter=1000, random_state=42)
    )
    lr_model.fit(X, y)
    print(f"LR Model classes: {lr_model.classes_}")

    print("Training Decision Tree pipeline...")
    dt_model = make_pipeline(
        OrdinalEncoder(handle_unknown='value'),
        DecisionTreeClassifier(max_depth=5, random_state=42)
    )
    dt_model.fit(X, y)
    print(f"DT Model classes: {dt_model.classes_}")

    with open('decision_tree.pkl', 'wb') as f:
        pickle.dump(dt_model, f)
    print("Saved decision_tree.pkl successfully!")

    with open('logistic_regression.pkl', 'wb') as f:
        pickle.dump(lr_model, f)
    print("Saved logistic_regression.pkl successfully!")

if __name__ == '__main__':
    train_and_save()
