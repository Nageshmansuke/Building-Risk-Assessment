import unittest
import os
import json
import tempfile

# Ensure SQLite is used for tests
os.environ["MYSQL_PASSWORD"] = ""
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"

from app import app, db, Prediction, make_prediction, generate_fallback_report


class QuakeGuardTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

        with app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def setUp(self):
        with app.app_context():
            Prediction.query.delete()
            db.session.commit()

    # 1. Navigation & Health Routes
    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('service'), 'quakeguard')

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'QuakeGuard', response.data)

    def test_about_page(self):
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)

    def test_history_page(self):
        response = self.client.get('/history')
        self.assertEqual(response.status_code, 200)

    def test_history_filter(self):
        response = self.client.get('/history?risk_filter=High')
        self.assertEqual(response.status_code, 200)

    # 2. ML Prediction Core
    def test_make_prediction_decision_tree(self):
        result = make_prediction(
            model_choice='decision_tree',
            age_building=15,
            plinth_area_sq_ft=750,
            superstructure='RC, engineered',
            foundation_type='RC',
            other_floor_type='RCC/RB/RBC'
        )
        self.assertIn('risk_level', result)
        self.assertIn('damage_grade', result)
        self.assertIn('confidence', result)
        self.assertIn('factors', result)
        self.assertEqual(result['model_used'], 'decision_tree')
        self.assertIn(result['risk_level'], ['Low', 'Medium', 'High', 'Critical'])
        self.assertIn(result['damage_grade'], [1, 2, 3, 4, 5])

    def test_make_prediction_logistic_regression(self):
        result = make_prediction(
            model_choice='logistic_regression',
            age_building=45,
            plinth_area_sq_ft=600,
            superstructure='Stone, mud mortar',
            foundation_type='Mud mortar-Stone/Brick',
            other_floor_type='TImber/Bamboo-Mud'
        )
        self.assertIn('risk_level', result)
        self.assertIn('damage_grade', result)
        self.assertEqual(result['model_used'], 'logistic_regression')
        self.assertIn(result['damage_grade'], [1, 2, 3, 4, 5])

    def test_make_prediction_invalid_model(self):
        with self.assertRaises(ValueError):
            make_prediction('random_forest_unsupported', 10, 500, 'RC', 'RC', 'RCC')

    # 3. Predict Route (API & Form)
    def test_predict_json_api(self):
        payload = {
            'model': 'decision_tree',
            'age_building': 20,
            'plinth_area_sq_ft': 650,
            'superstructure': 'RC, engineered',
            'foundation_type': 'RC',
            'other_floor_type': 'RCC/RB/RBC'
        }
        response = self.client.post(
            '/predict',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('risk_level', data)
        self.assertIn('damage_grade', data)

    def test_predict_form_post(self):
        form_data = {
            'model': 'decision_tree',
            'age_building': '25',
            'plinth_area_sq_ft': '800',
            'superstructure': 'Stone, mud mortar',
            'foundation_type': 'Mud mortar-Stone/Brick',
            'other_floor_type': 'TImber/Bamboo-Mud'
        }
        response = self.client.post('/predict', data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Risk', response.data)

    def test_predict_invalid_input_json(self):
        response = self.client.post(
            '/predict',
            data=json.dumps({'age_building': 'not_a_number'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    # 4. AI Consultant API & Fallback
    def test_ai_consultant_endpoint(self):
        payload = {
            'building_inputs': {
                'superstructure': 'Stone, mud mortar',
                'foundation_type': 'Mud mortar-Stone/Brick',
                'age_building': 40,
                'plinth_area_sq_ft': 600
            },
            'damage_grade': 4,
            'risk_level': 'High'
        }
        response = self.client.post(
            '/api/get_consultant',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('expert_report', data)
        self.assertIn('IS 4326', data['expert_report'])

    def test_fallback_report_generation(self):
        inputs = {
            'superstructure': 'Masonry',
            'foundation_type': 'Mud mortar-Stone/Brick',
            'age_building': 30,
            'plinth_area_sq_ft': 500
        }
        report = generate_fallback_report(inputs, 3, 'Medium', 'Sample context')
        self.assertIn('AI Structural Consultant Report', report)
        self.assertIn('IS 4326', report)

    # 5. Database Records & Persistence
    def test_prediction_model_persistence(self):
        with app.app_context():
            pred = Prediction(
                model_used='Decision Tree',
                age_building=25,
                plinth_area_sq_ft=600.0,
                superstructure='RC, engineered',
                foundation_type='RC',
                other_floor_type='RCC/RB/RBC',
                risk_level='Low',
                damage_grade=1,
                confidence=0.95
            )
            db.session.add(pred)
            db.session.commit()

            fetched = Prediction.query.first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.risk_level, 'Low')
            d = fetched.to_dict()
            self.assertEqual(d['result'], 'Low')
            self.assertEqual(d['damage_grade'], 1)


if __name__ == '__main__':
    unittest.main()
