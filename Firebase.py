import firebase_admin
from firebase_admin import credentials, firestore
import random
import string

db = None
connected = False

def check_firebase_connection():
    try:
        # Define the collection and document
        collection_name = 'test_connection'
        document_id = 'test_doc'
        doc_ref = db.collection(collection_name).document(document_id)

        # Write a test document
        doc_ref.set({'test_field': 'test_value'})

        # Read the test document
        doc = doc_ref.get()

        if doc.exists:

            # Delete the test document
            doc_ref.delete()
            return True, ""
        else:
            return False, "Document does not exist. Connection might have failed."

    except Exception as e:
        return False, f"Failed to connect to Firebase: {e}"


def initialize_firebase():
    global db, connected
    try:
        # Path to the serviceAccountKey.json file downloaded from Firebase Console
        cred = credentials.Certificate("cred.json")

        # Initialize the app with a service account, granting admin privileges
        firebase_admin.initialize_app(cred)

        # Initialize Firestore DB
        db = firestore.client()

        c, msg = check_firebase_connection()
        connected = c
        return c, msg
    except:
        connected = False
        return False, "Firebase setup improperly."

def generate_random_string(length):
    # Define the set of characters to include in the random string
    characters = string.ascii_letters + string.digits
    # Generate a random string
    random_string = ''.join(random.choices(characters, k=length))
    return random_string


# Add data to Firestore
def add_data(name, mapping):
    if name == "":
        name = generate_random_string(5)
    doc_ref = db.collection('alumni').document(name)
    doc_ref.set(mapping)


def user_exists(collection_name, name):
    doc_ref = db.collection(collection_name).document(name)
    return doc_ref.get().exists


# Read data from Firestore
def read_data():
    users_ref = db.collection('users')
    docs = users_ref.stream()

    for doc in docs:
        print(f'{doc.id} => {doc.to_dict()}')
