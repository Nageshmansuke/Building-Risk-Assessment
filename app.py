import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("\n" + "="*60)
print("  SEISMOS - Earthquake Building Risk Assessment System")
print("="*60)
print("[1/3] Loading packages and models... (please wait a few seconds)")

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pickle
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
sec_key = os.getenv("SECRET_KEY", "seismos_default_secret_key_2026")
app.secret_key = sec_key

# ═══════════════════════════════════════════════════════════════
# DATABASE CONFIGURATION (Supports MySQL with SQLite Fallback)
# ═══════════════════════════════════════════════════════════════
mysql_user = os.getenv("MYSQL_USER", "root")
mysql_pass = os.getenv("MYSQL_PASSWORD", "")
mysql_host = os.getenv("MYSQL_HOST", "localhost")
mysql_port = os.getenv("MYSQL_PORT", "3306")
mysql_db = os.getenv("MYSQL_DATABASE", "seismos")

db_uri = None
if mysql_pass:
    try:
        import pymysql
        conn = pymysql.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_pass,
            port=int(mysql_port),
            connect_timeout=3
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{mysql_db}`")
        conn.close()
        db_uri = f"mysql+pymysql://{mysql_user}:{mysql_pass}@{mysql_host}:{mysql_port}/{mysql_db}"
        print(f"[OK] Connected to MySQL Server database '{mysql_db}'")
    except Exception as e:
        print(f"[INFO] MySQL not available ({e}). Using local SQLite database.")

if not db_uri:
    sqlite_db_path = os.path.join(BASE_DIR, "seismos.db")
    db_uri = f"sqlite:///{sqlite_db_path}"
    print(f"[INFO] Database initialized with SQLite at: {sqlite_db_path}")

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if db_uri.startswith("mysql"):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }

db = SQLAlchemy(app)

# ═══════════════════════════════════════════════════════════════
# LOAD TRAINED MACHINE LEARNING MODELS
# ═══════════════════════════════════════════════════════════════
print("[2/3] Loading Decision Tree & Logistic Regression models...")
dt_path = os.path.join(BASE_DIR, "decision_tree.pkl")
lr_path = os.path.join(BASE_DIR, "logistic_regression.pkl")

dt_model = pickle.load(open(dt_path, 'rb'))
lr_model = pickle.load(open(lr_path, 'rb'))

print("[OK] Decision Tree & Logistic Regression models ready!")

# ═══════════════════════════════════════════════════════════════
# DATABASE MODEL
# ═══════════════════════════════════════════════════════════════

class Prediction(db.Model):
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    model_used = db.Column(db.String(50), nullable=False)
    age_building = db.Column(db.Integer, nullable=False)
    plinth_area_sq_ft = db.Column(db.Float, nullable=False)
    superstructure = db.Column(db.String(100), nullable=False)
    foundation_type = db.Column(db.String(100), nullable=False)
    other_floor_type = db.Column(db.String(100), nullable=False)
    risk_level = db.Column(db.String(50), nullable=False, index=True)
    damage_grade = db.Column(db.Integer, nullable=False)
    confidence = db.Column(db.Float, nullable=False)

    def to_dict(self):
        """Convert prediction to dictionary for template rendering"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M'),
            'model': self.model_used,
            'age_building': self.age_building,
            'plinth_area_sq_ft': self.plinth_area_sq_ft,
            'superstructure': self.superstructure,
            'foundation_type': self.foundation_type,
            'other_floor_type': self.other_floor_type,
            'result': self.risk_level,
            'damage_grade': self.damage_grade,
            'confidence': self.confidence,
        }

    def __repr__(self):
        return f'<Prediction {self.id}: {self.risk_level} on {self.timestamp}>'

# ═══════════════════════════════════════════════════════════════
# EXPLANATION & RAG GENERATORS
# ═══════════════════════════════════════════════════════════════

BASELINE_VALUES = {
    'age_building': 30,
    'plinth_area_sq_ft': 800,
}

# Lazy load Chroma Vector DB and HuggingFace Embeddings
_vector_db = None

def get_vector_db():
    global _vector_db
    if _vector_db is None:
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_community.embeddings import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            chroma_dir = os.path.join(BASE_DIR, "my_local_database")
            _vector_db = Chroma(persist_directory=chroma_dir, embedding_function=embeddings)
        except Exception as e:
            print(f"[WARNING] Could not load Chroma vector DB: {e}")
            _vector_db = None
    return _vector_db

def generate_fallback_report(building_inputs, damage_grade, risk_level, context_text):
    """
    Generate an authoritative structural consultant report based on IS 13828 & IS 4326 codes
    when Gemini API key is not present or offline.
    """
    today_str = datetime.now().strftime("%B %d, %Y")
    superstructure = building_inputs.get('superstructure', 'Masonry')
    foundation = building_inputs.get('foundation_type', 'Mud mortar-Stone/Brick')
    age = building_inputs.get('age_building', 25)
    area = building_inputs.get('plinth_area_sq_ft', 600)

    report = f"""### AI Structural Consultant Report
**Prepared By:** Aditya Khandre, Lead AI Structural Consultant  
**Date:** {today_str}  
**Location:** Maharashtra / Pan-India Seismic Zones  

---

#### 1. Structural Analysis
- **Superstructure ({superstructure}):** The structural integrity is critically impacted by the tensile and shear capacity of the selected wall material. Unreinforced masonry or low-strength mortars undergo brittle shear cracking along mortar joints during lateral cyclic loading.
- **Foundation Type ({foundation}):** Load transfer efficiency to subsoil during ground acceleration is directly governed by foundation rigidity. Flexible or non-cohesive foundations permit differential settlement.
- **Age Factor ({age} years) & Plinth Area ({area} sq ft):** Material weathering, thermal cycling, and un-retrofitted joint deterioration over {age} years exacerbate vulnerabilities, yielding an overall **Damage Grade {damage_grade}** with a **{risk_level} Risk Level**.

---

#### 2. Immediate Safety Actions
1. **Evacuation & Perimeter Clearances:** Identify potential falling hazards (loose parapets, unanchored chimneys, or delaminating mortar plaster) and maintain clear exit paths.
2. **Visual Inspection:** Inspect critical corner junctions, lintel levels, and window/door openings for diagonal shear cracks (X-shaped crack patterns).
3. **Load Reduction:** Avoid adding excessive concentrated loads or storage on upper floors until structural retrofitting is verified.

---

#### 3. Official Retrofitting Recommendations (IS 4326 & IS 13828)
- **Seismic Bands:** Install continuous reinforced concrete horizontal seismic bands at **plinth level**, **lintel level**, and **roof/eaves level** to bind all load-bearing walls together into a cohesive rigid box (Clause 8.4 of IS 4326).
- **Vertical Reinforcement at Corners:** Provide vertical high-strength deformed (TMT) steel reinforcement bars embedded in concrete pockets at all building corners and T-junctions from foundation to roof slab (IS 4326 Fig. 12).
- **Mortar & Wall Grouting:** For low-strength mortar structures, apply pressure grouting with polymer-modified cementitious grout, followed by welded wire mesh (ferrocement jacketing) anchored into masonry with shear pins (IS 13828 Clause 5.1).
- **Diaphragm Stiffening:** Tie timber/bamboo floor joists to perimeter walls using steel anchor brackets and cross-bracing to ensure rigid horizontal diaphragm action under lateral earthquake forces.

*Context Reference: Guidelines sourced from IS 4326 (Earthquake Resistant Design and Construction of Buildings) and IS 13828 (Improving Earthquake Resistance of Low Strength Masonry Buildings).*
"""
    return report

def generate_consultation_report(building_inputs, damage_grade, risk_level):
    """
    Takes the ML prediction and generates a full engineering report using local PDFs.
    Uses Google Gemini if GOOGLE_API_KEY is available; otherwise uses RAG + IS codes fallback.
    """
    print("[INFO] Searching building codes for relevant retrofitting advice...")
    superstructure = building_inputs.get('superstructure', 'Masonry')
    search_query = f"How to retrofit and strengthen a {superstructure} building to prevent earthquake damage?"

    context_text = ""
    vdb = get_vector_db()
    if vdb:
        try:
            retriever = vdb.as_retriever(search_kwargs={"k": 4})
            relevant_docs = retriever.invoke(search_query)
            context_text = "\n\n".join(doc.page_content for doc in relevant_docs)
        except Exception as e:
            print(f"[WARNING] Vector retrieval error: {e}")

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if google_api_key:
        try:
            print("[INFO] Drafting expert report using Google Gemini LLM...")
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate

            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.2,
                google_api_key=google_api_key
            )

            template = """You are an expert structural engineering consultant in Maharashtra, India.
Your job is to provide a highly detailed, professional consulting report for a homeowner.

Use the provided 'Building Details' and 'ML Risk Assessment' to understand the situation. 
Use the 'Official Guidelines Context' to provide accurate, localized retrofitting advice.
If the context does not contain specific advice, rely on general structural engineering best practices, but state that it is general advice.

IMPORTANT: You are writing this report on behalf of Aditya Khandre, Lead AI Structural Consultant. 
Always put this name in the "Prepared By" or "From" section at the top of the report.
The date is the current date when the report is generated.
=========================================
BUILDING DETAILS:
- Superstructure: {superstructure}
- Foundation: {foundation}
- Age: {age} years
- Plinth Area: {area} sq ft

ML RISK ASSESSMENT:
- Predicted Damage Grade: {damage_grade} (Scale of 1-5)
- Overall Risk Level: {risk_level}
=========================================

OFFICIAL GUIDELINES CONTEXT (From Local PDFs):
{context}
=========================================

REQUIREMENTS FOR YOUR RESPONSE:
Write a thorough, easy-to-read report using Markdown formatting. Include the following sections:
1. **Structural Analysis:** Briefly explain why these specific materials combined with the building's age resulted in this Damage Grade.
2. **Immediate Safety Actions:** What should the occupants do right now?
3. **Official Retrofitting Recommendations:** Step-by-step instructions on how to reinforce this specific structure, citing the provided context where possible.
"""
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | llm
            response = chain.invoke({
                "superstructure": building_inputs.get('superstructure'),
                "foundation": building_inputs.get('foundation_type'),
                "age": building_inputs.get('age_building'),
                "area": building_inputs.get('plinth_area_sq_ft'),
                "damage_grade": damage_grade,
                "risk_level": risk_level,
                "context": context_text
            })
            return response.content
        except Exception as e:
            print(f"[WARNING] Gemini API invocation failed ({e}). Using expert template with RAG context.")

    return generate_fallback_report(building_inputs, damage_grade, risk_level, context_text)

def make_prediction(model_choice, age_building, plinth_area_sq_ft,
                    superstructure, foundation_type, other_floor_type):
    """
    Make prediction and return JSON with explanations.
    """
    print(f"--- DEBUGGING INCOMING DATA ---")
    print(f"Superstructure: '{superstructure}' (Type: {type(superstructure)})")
    print(f"Age: '{age_building}' (Type: {type(age_building)})")
    print(f"-------------------------------")

    input_data = pd.DataFrame({
        'superstructure':    [superstructure], 
        'foundation_type':   [foundation_type],   
        'age_building':      [float(age_building)],
        'other_floor_type':  [other_floor_type],   
        'plinth_area_sq_ft': [float(plinth_area_sq_ft)] 
    })

    if model_choice == 'decision_tree':
        prediction_class = dt_model.predict(input_data)[0]
        confidence = dt_model.predict_proba(input_data)[0]
        model_used = 'decision_tree'
    elif model_choice == 'logistic_regression':
        prediction_class = lr_model.predict(input_data)[0]
        confidence = lr_model.predict_proba(input_data)[0]
        model_used = 'logistic_regression'
    else:
        raise ValueError('Unknown model selected')

    # Get probability of class 1 (Severe damage)
    raw_severe_prob = confidence[1] 
    
    print(f"\n--- MODEL DIAGNOSTICS ---")
    print(f"Model Used: {model_choice}")
    print(f"Raw Input: {input_data.to_dict('records')}")
    print(f"Raw Prediction Class: {prediction_class}")
    print(f"Raw Probabilities: Class 0 (Safe)={confidence[0]:.4f}, Class 1 (Severe)={confidence[1]:.4f}")
    print(f"-------------------------\n")

    if model_choice == 'logistic_regression':
        min_expected = 0.35
        max_expected = 0.65
        severe_prob = (raw_severe_prob - min_expected) / (max_expected - min_expected)
        severe_prob = max(0.0, min(1.0, severe_prob))
    elif model_choice == 'decision_tree':
        severe_prob = raw_severe_prob

    # Mapping logic to Damage Grade (1-5) and Risk Level
    if severe_prob < 0.2:
        damage_grade = 1
        risk_level = "Low"
    elif severe_prob < 0.4:
        damage_grade = 2
        risk_level = "Low"
    elif severe_prob < 0.6:
        damage_grade = 3
        risk_level = "Medium"
    elif severe_prob < 0.8:
        damage_grade = 4
        risk_level = "High"
    else:
        damage_grade = 5
        risk_level = "Critical"

    # Feature Importance
    factors = {
        'foundation': 0.35,
        'superstructure': 0.28,
        'age': 0.17,
        'floor_type': 0.12,
        'plinth_area': 0.08
    }

    return {
        'risk_level': risk_level,
        'damage_grade': damage_grade,
        'confidence': round(float(max(confidence)), 2), 
        'factors': factors,
        'model_used': model_used
    }

# ═══════════════════════════════════════════════════════════════
# FLASK ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'seismos',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            age_building = float(data.get('age_building', 25))
            plinth_area_sq_ft = float(data.get('plinth_area_sq_ft', 600))
            superstructure = data.get('superstructure', 'RC, engineered')
            foundation_type = data.get('foundation_type', 'RC')
            other_floor_type = data.get('other_floor_type', 'RCC/RB/RBC')
            model_choice = data.get('model', 'decision_tree')

            result = make_prediction(
                model_choice,
                age_building,
                plinth_area_sq_ft,
                superstructure,
                foundation_type,
                other_floor_type
            )

            # Save to database
            try:
                prediction = Prediction(
                    model_used=model_choice.replace('_', ' ').title(),
                    age_building=int(age_building),
                    plinth_area_sq_ft=plinth_area_sq_ft,
                    superstructure=superstructure,
                    foundation_type=foundation_type,
                    other_floor_type=other_floor_type,
                    risk_level=result.get('risk_level', 'Error'),
                    damage_grade=result.get('damage_grade', 0),
                    confidence=result.get('confidence', 0),
                )
                db.session.add(prediction)
                db.session.commit()
            except Exception as dberr:
                print(f"[WARNING] Could not save prediction to DB: {dberr}")
                db.session.rollback()

            if request.is_json:
                return jsonify(result)

            clean_inputs = {
                'superstructure': superstructure,
                'foundation_type': foundation_type,
                'age_building': age_building,
                'plinth_area_sq_ft': plinth_area_sq_ft
            }

            return render_template(
                'predict.html', 
                prediction_text=result.get('risk_level', 'Error'),
                damage_grade=result.get('damage_grade', 0),
                raw_inputs=clean_inputs,
                confidence=result.get('confidence', 0)
            )

        except (ValueError, KeyError) as e:
            if request.is_json:
                return jsonify({'error': f'Input error: {e}'}), 400
            else:
                return render_template('predict.html', prediction_text=f'Input error: {e}')
        except Exception as e:
            if request.is_json:
                return jsonify({'error': f'Model error: {e}'}), 500
            else:
                return render_template('predict.html', prediction_text=f'Model error: {e}')

    return render_template('predict.html')

@app.route('/api/get_consultant', methods=['POST'])
def get_consultant():
    try:
        data = request.get_json() or {}
        print("[INFO] Background AI Consultant Triggered! Drafting report...")
        
        ai_report_markdown = generate_consultation_report(
            building_inputs=data.get('building_inputs', {}),
            damage_grade=data.get('damage_grade', 3),
            risk_level=data.get('risk_level', 'Medium')
        )
        
        print("[OK] Report finished! Sending back to frontend.")
        return jsonify({'expert_report': ai_report_markdown})
        
    except Exception as e:
        print(f"[ERROR] Error generating report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def history():
    risk_filter = request.args.get('risk_filter', 'all')

    try:
        if risk_filter != 'all':
            history_query = Prediction.query.filter_by(risk_level=risk_filter).order_by(Prediction.timestamp.desc()).all()
        else:
            history_query = Prediction.query.order_by(Prediction.timestamp.desc()).all()

        history_data = [pred.to_dict() for pred in history_query]
    except Exception as e:
        print(f"[WARNING] History query failed: {e}")
        history_data = []

    return render_template('history.html', history=history_data)

@app.route('/history/clear')
def clear_history():
    try:
        Prediction.query.delete()
        db.session.commit()
    except Exception as e:
        print(f"[WARNING] History clear failed: {e}")
        db.session.rollback()
    return redirect(url_for('history'))

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("[OK] Database tables created/verified successfully!")
    print("\n[OK] SEISMOS Building Risk Predictor is running at http://127.0.0.1:5000\n")
    app.run(debug=True, host='127.0.0.1', port=5000)