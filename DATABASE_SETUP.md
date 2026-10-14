# SEISMOS - MySQL Database Integration Guide

## Overview

The SEISMOS application has been updated to use MySQL database for persistent storage of earthquake damage predictions. This replaces the previous session-based storage system.

## Setup Instructions

### 1. Install Dependencies

Make sure all required Python packages are installed:

```bash
pip install -r requirements.txt
```

### 2. MySQL Configuration

Update the MySQL credentials in `app.py` if needed (currently set to):

- Host: `localhost`
- User: `your-name`
- Password: `your-pass`
- Database: `seismos` (auto-created)

Edit the connection string in `app.py` line 18:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:'your-db-password'@localhost:3306/seismos'
```

### 3. Initialize Database

Run the initialization script to create the MySQL database:

```bash
python init_db.py
```

This will:

- Connect to MySQL
- Create the `seismos` database (if not exists)
- Set up the connection

### 4. Create Database Tables

When you run the Flask app, tables are automatically created:

```bash
python app.py
```

## Features

### Database Schema

The `predictions` table stores:

- `id`: Unique identifier (Primary Key)
- `timestamp`: When prediction was made
- `model_used`: Which ML model (Decision Tree / Logistic Regression)
- `age_building`: Building age in years
- `plinth_area_sq_ft`: Building area in square feet
- `superstructure`: Type of structure material
- `foundation_type`: Foundation material type
- `other_floor_type`: Floor system type
- `risk_level`: Prediction result (Low/Medium/High/Critical)
- `damage_grade`: Damage severity grade (1-5)
- `confidence`: Model confidence score (0-1)

### Updated Routes

#### `/predict` (POST)

- Accepts form or JSON data
- Makes prediction using ML model
- **Saves prediction to MySQL database**
- Returns result page

#### `/history` (GET)

- Fetches all predictions from MySQL database
- Orders by timestamp (newest first)
- Supports filtering by risk level via `?risk_filter=medium` parameter
- Displays in sortable table

#### `/history/clear` (GET)

- Deletes all predictions from database
- Redirects to history page

### History Page Display

The history page now shows:

- Timestamp of prediction
- ML model used (Decision Tree / Logistic Regression)
- Input parameters (superstructure, foundation, age, area)
- Risk level with color-coded badge
- Model confidence percentage
- Filtering by risk level (Low, Medium, High, Critical)

## Data Persistence

- All predictions are permanently stored in MySQL
- Data survives application restarts
- Scalable for large datasets
- Indexed for fast filtering

## Files Changed

1. **app.py**: Added SQLAlchemy setup, Prediction model, database operations
2. **templates/history.html**: Updated to display building prediction data instead of earthquake data
3. **init_db.py**: New database initialization script
4. **requirements.txt**: New dependency list

## Troubleshooting

### Connection Error

If you get "Cannot connect to MySQL":

1. Verify MySQL is running (e.g., `net start MySQL80` on Windows)
2. Check credentials in app.py match your MySQL setup
3. Ensure database exists (run `init_db.py`)

### Unicode Error

Windows with certain locales may have emoji encoding issues. All emojis have been removed from the code to prevent this.

### Empty History

If no predictions show initially, this is expected - you need to make predictions first via the `/predict` page.

## Example Usage

1. **Make a prediction**:
   - Go to `/predict`
   - Fill in building parameters
   - Select a model
   - Submit form
   - Prediction is saved to database

2. **View history**:
   - Go to `/history`
   - See all previous predictions
   - Filter by risk level
   - Clear history if needed

## API Integration

You can also make predictions via JSON API:

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age_building": 30,
    "plinth_area_sq_ft": 800,
    "superstructure": "rc_engineered",
    "foundation_type": "rc",
    "other_floor_type": "rcc_rb_rbc",
    "model": "decision_tree"
  }'
```

This returns JSON with prediction details but does NOT save to database (HTML form requests do).
To also save via API, modify the route to always save predictions.

## Next Steps

- Test predictions on the `/predict` page
- Verify data appears in history
- Check MySQL database directly with: `mysql -u root -p seismos`
- Query: `SELECT * FROM predictions;`
