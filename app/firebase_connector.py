import firebase_admin
from firebase_admin import credentials, firestore
import os

def init_firebase():
    try:
        cred_path = os.path.join('firebase', 'serviceAccountKey.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("✅ Firebase initialized successfully.")
        return db
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        return None
