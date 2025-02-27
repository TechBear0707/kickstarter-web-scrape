import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Load environment variables from .env file
load_dotenv()

# Get Firebase credentials file path from the environment
firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")


def initialize_firebase(json_file_path=None):
    """
    Initialize Firebase using the provided JSON file path.
    If no path is provided, it loads from the environment variable.
    Returns a Firestore client.
    """
    if json_file_path is None:
        json_file_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    cred = credentials.Certificate(json_file_path)
    # Initialize the Firebase app; if already initialized, this will return the existing app
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    return firestore.client()


# Initialize Firestore
db = initialize_firebase()

# Example: Add or update a document in the "trending_games" collection
doc_ref = db.collection("trending_games").document("Exploding Kittens")
doc_ref.set({
    "URL": "cats.com",
    "Category": "Games",
    "Description": "this is a test to insert data"
})

# Retrieve the document from Firestore and print the URL field
doc = doc_ref.get()
if doc.exists:
    data = doc.to_dict()
    print(data.get("URL"))
else:
    print("No such document!")
