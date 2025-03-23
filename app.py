from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
from sqlalchemy.exc import SQLAlchemyError
from together import Together
from dotenv import load_dotenv
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
import random
from ai.generate_ai_flashcards import generate_flashcards_api

load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow frontend requests
app.secret_key = os.getenv("SECRET_KEY")  # Replace with a real secret key
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Flask session secret key
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')  # JWT secret key
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=365 * 10)  # 10 years
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    subjects = db.relationship('Subject', backref='user', cascade='all, delete-orphan')  # Cascade delete subjects

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }

# Define the Subject model
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)  # Cascade delete
    decks = db.relationship('Deck', backref='subject', cascade='all, delete-orphan')  # Cascade delete decks

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id
        }

# Define the Deck model
class Deck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # subject_name = db.Column(db.String(100), nullable=False)  # Add this line
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete='CASCADE'), nullable=False)  # Cascade delete
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)  # Cascade delete
    flashcards = db.relationship('Flashcard', backref='deck', cascade='all, delete-orphan')  # Cascade delete flashcards
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject_id': self.subject_id,
            # 'subject_name': self.subject_name,
            'user_id': self.user_id,
        }

# Define the Flashcard model
class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.String(200), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('deck.id', ondelete='CASCADE'), nullable=False)  # Cascade delete
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete='CASCADE'), nullable=False)  # Cascade delete
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)  # Cascade delete
    status = db.Column(db.String(20), default='learning')  # after untouched - Options: learning, nearly_there, learned

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'deck_id': self.deck_id,
            'subject_id': self.subject_id,
            'user_id': self.user_id,
            "status": self.status
        }
# Initialize the database
def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

# Initialize the Together client
client = Together(api_key=os.getenv('TOGETHER_API_KEY'))

# Function to generate flashcards
def generate_flashcards(topic, quantity, exam_board):
    return generate_flashcards_api(topic, quantity, exam_board)

# HOME PAGE
@app.route('/home')
# @jwt_required()  # Ensure the request has a valid JWT
def home():
    return render_template("home.html")
    
@app.route("/get-username", methods=["GET"])
@jwt_required()
def get_username():
    user_id = get_jwt_identity()  # Get the `sub` claim from the token
    print("User ID from token:", user_id)  # Debugging statement

    # Fetch the user from the database using their ID
    user = User.query.get(int(user_id))  # Convert user_id to int (if it's a string)

    if user:
        # Return the user's name
        return jsonify({"username": user.name}), 200
    else:
        # Handle the case where the user is not found
        return jsonify({"message": "User not found!"}), 404

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/generate-flashcards-page")
def generate_flashcards_page():
    return render_template("generate_flashcards.html")

# SUBJECTS
@app.route("/create-subject-api", methods=["POST"])
@jwt_required()  # Ensure the request has a valid JWT
def create_subject():
    try:
        data = request.get_json()
        name = data.get('name')
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        if not name or not user_id:
            return jsonify({'message': 'All fields are required!'}), 400

        # Check if a subject with the same name already exists for this user
        if Subject.query.filter_by(name=name, user_id=user_id).first():
            return jsonify({'message': 'Subject with the same name already exists for this user!'}), 409

        # Create a new subject
        new_subject = Subject(name=name, user_id=user_id)

        # Add the new subject to the database session and commit
        db.session.add(new_subject)
        db.session.commit()

        return jsonify({'message': 'Subject added successfully!'}), 201
    except Exception as e:
        db.session.rollback()  # Rollback the transaction in case of an error
        return jsonify({'message': str(e)}), 500
    
# FLASHCARDS
@app.route("/create-flashcard-api", methods=["POST"])
@jwt_required()  # Ensure the request has a valid JWT
def create_flashcard():
    try:
        data = request.get_json()
        deck_id = data.get('deck_id')  # Get the deck ID from the request
        question = data.get('question')  # Get the question
        answer = data.get('answer')  # Get the answer
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Fetch the deck to get the subject_id
        deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first()
        if not deck:
            return jsonify({'message': 'Deck not found or does not belong to the user!'}), 404

        subject_id = deck.subject_id  # Get the subject_id from the deck

        # Validate required fields
        if not deck_id or not question or not answer or not user_id or not subject_id:
            return jsonify({'message': 'Deck ID, question, answer, user ID, and subject ID are required!'}), 400

        # Create a new flashcard
        new_flashcard = Flashcard(
            question=question,
            answer=answer,
            deck_id=deck_id,
            subject_id=subject_id,  # Include subject_id
            user_id=user_id  # Include user_id
        )
        db.session.add(new_flashcard)
        db.session.commit()

        return jsonify({'message': 'Flashcard created successfully!', 'flashcard_id': new_flashcard.id}), 201
    except Exception as e:
        db.session.rollback()  # Rollback the transaction in case of an error
        return jsonify({'message': str(e)}), 500
    
@app.route("/fetch-flashcards/<int:deck_id>", methods=["GET"])
@jwt_required()
def fetch_flashcards(deck_id):
    try:
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Validate required fields
        if not deck_id or not user_id:
            return jsonify({'message': 'Deck ID and user ID are required!'}), 400

        # Fetch the deck to ensure it exists and belongs to the user
        deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first()
        if not deck:
            return jsonify({'message': 'Deck not found or does not belong to the user!'}), 404

        subject_id = deck.subject_id  # Get the subject_id from the deck

        # Fetch all flashcards for the deck and its subject
        flashcards = Flashcard.query.filter_by(user_id=user_id, deck_id=deck_id, subject_id=subject_id).all()

        # Convert the flashcards to a list of dictionaries
        flashcards_list = [flashcard.to_dict() for flashcard in flashcards]

        return jsonify({'flashcards': flashcards_list}), 200

    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching flashcards: {e}")
        return jsonify({'message': 'An error occurred while fetching flashcards. Please try again.'}), 500

# DECKS

@app.route('/fetch-deck-name/<int:deck_id>')
@jwt_required()
def fetch_deck_name(deck_id):
    try:
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Validate required fields
        if not deck_id or not user_id:
            return jsonify({'message': 'Deck ID and user ID are required!'}), 400

        # Fetch the deck to ensure it exists and belongs to the user
        deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first()
        if not deck:
            return jsonify({'message': 'Deck not found or does not belong to the user!'}), 404

        return jsonify({'deck_name': deck.name}), 200
    except Exception as e:
        print(f"Error fetching deck name: {e}")
        return jsonify({'message': 'An error occurred while fetching the deck name.'}), 500
    
@app.route('/create-deck-api', methods=['POST'])
@jwt_required()
def create_deck():
    
    try:
        data = request.get_json()
        name = data.get('name')
        subject_id = data.get('subjectId')
        user_id = int(get_jwt_identity())

        if not name or not subject_id or not user_id:
            return jsonify({'message': 'All fields are required!'}), 400

        # Verify that the subject belongs to the user
        subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
        if not subject:
            return jsonify({'message': 'Subject not found or unauthorized!'}), 404


        # Create a new deck
        new_deck = Deck(name=name, subject_id=subject_id, user_id=user_id)

        # Add the new deck to the database session and commit
        db.session.add(new_deck)
        db.session.commit()

        return jsonify({'message': 'Deck created successfully!', 'deck': new_deck.to_dict()}), 201
    except Exception as e:
        db.session.rollback()  # Rollback the transaction in case of an error
        print(f"Error creating deck: {e}")
        return jsonify({'message': 'An error occurred while creating the deck.'}), 500

@app.route("/get-subjects", methods=["GET"])
@jwt_required()
def get_subjects():
    try:
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Fetch all subjects for this user
        subjects = Subject.query.filter_by(user_id=user_id).all()

        if subjects:
            # Return a list of subjects as JSON
            return jsonify([subject.to_dict() for subject in subjects]), 200
        else:
            # Handle the case where there are no subjects for this user
            return jsonify({'message': 'No subjects found for this user!'}), 404
    except Exception as e:
        # Log the error and return a 500 response
        print(f"Error fetching subjects: {e}")
        return jsonify({'message': 'An error occurred while fetching subjects.'}), 500
    
@app.route('/delete-subject-api', methods=['DELETE'])
@jwt_required()
def delete_subject():
    try:
        data = request.get_json()
        subject_id = data.get('subjectId')
        user_id = int(get_jwt_identity())

        if not subject_id or not user_id:
            return jsonify({'message': 'Subject ID and user ID are required!'}), 400

        # Verify that the subject belongs to the user
        subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
        if not subject:
            return jsonify({'message': 'Subject not found or unauthorized!'}), 404

        # Delete the subject and all associated decks and flashcards
        db.session.delete(subject)
        db.session.commit()

        return jsonify({'message': 'Subject deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()  # Rollback the transaction in case of an error
        print(f"Error deleting subject: {e}")
        return jsonify({'message': 'An error occurred while deleting the subject.'}), 500

@app.route("/create-flashcards-page/<int:deck_id>")
def create_flashcards_page(deck_id):
    # Fetch the deck from the database
    deck = Deck.query.get(deck_id)

    if not deck:
        return "Deck not found.", 404

    # Render the create_flashcards.html template and pass the deck_id and deck name
    return render_template("create_flashcards.html", deck_id=deck.id, deck_name=deck.name)

@app.route("/get-deck/<deck_id>", methods=["GET"])
def get_deck(deck_id):
    deck = Deck.query.get(deck_id)
    if deck:
        return jsonify({"deck": {"id": deck.id, "name": deck.name}})
    else:
        return jsonify({"message": "Deck not found."}), 404

@app.route("/delete-flashcard/<int:flashcard_id>", methods=["DELETE"])
@jwt_required()
def delete_flashcard(flashcard_id):
    try:
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Fetch the flashcard
        flashcard = Flashcard.query.filter_by(id=flashcard_id, user_id=user_id).first()
        if not flashcard:
            return jsonify({'message': 'Flashcard not found or does not belong to the user.'}), 404

        # Delete the flashcard
        db.session.delete(flashcard)
        db.session.commit()

        return jsonify({'message': 'Flashcard deleted successfully.'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return jsonify({'message': 'An error occurred while deleting the flashcard.'}), 500
    except Exception as e:
        print(f"Error deleting flashcard: {e}")
        return jsonify({'message': 'An error occurred while deleting the flashcard.'}), 500

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/sign-up")
def sign_up():
    return render_template("sign_up.html")

@app.route("/sign-up-api", methods=["POST"])
def register_user():
    data = request.get_json()
    name = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({'message': 'All fields are required!'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists!'}), 409
    
    if User.query.filter_by(name=name).first():
        return jsonify({'message': 'Username already exists!'}), 409
    
    hashed_password = generate_password_hash(password)
    new_user = User(name=name, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully!'}), 201

# LOGIN API
@app.route("/login-api", methods=["POST"])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'All fields are required!'}), 400
    
    user = User.query.filter_by(name=username).first()
    try:
        if not user or not check_password_hash(user.password, password):
            return jsonify({'message': 'Invalid credentials!'}), 401
        else:
            session['logged_in'] = True
            access_token = create_access_token(identity=str(user.id))
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
    return jsonify({'access_token': access_token}), 200

@app.route("/generate-flashcards", methods=["POST"])
def generate_flashcards_route():
    data = request.json
    topic = data.get("topic")
    exam_board = data.get("exam_board")
    quantity = int(data.get("amount"))

    if not topic or not quantity:
        return jsonify({"error": "Missing topic or amount."}), 400
    
    try:
        flashcards = generate_flashcards(topic, int(quantity), exam_board)
        # Ensure flashcards is a JSON serializable object
        return jsonify({"flashcards": flashcards})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/add-flashcard", methods=["POST"])
@jwt_required()  # Add parentheses here
def add_flashcard():
    try:
        data = request.get_json()
        deck_id = data.get("deck_id")
        question = data.get("question")
        answer = data.get("answer")
        subject_id = None
        user_id = get_jwt_identity()

        if not deck_id or not question or not answer:
            return jsonify({"error": "Missing deck ID, question, or answer."}), 400
        
        deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first()
        if not deck or deck.user_id != int(user_id):
            return jsonify({"error": "Deck not found or not authorized."}), 403
        
        subject_id = deck.subject_id
        
        new_flashcard = Flashcard(question=question, answer=answer, user_id=user_id, deck_id=deck_id, subject_id=subject_id)
        db.session.add(new_flashcard)
        db.session.commit()

        return jsonify({"message": "Flashcard added successfully!", "flashcard_id": new_flashcard.id}), 201
    except Exception as e:
        db.session.rollback()  # Rollback the transaction in case of an error
        return jsonify({"error": str(e)}), 500
    
@app.route("/init-db")
def init_db_route():
    db.drop_all()
    db.create_all()
    return "Database initialized!"

@app.route("/show-users")
def show_users():
    users = User.query.all()
    user_list = [{"name": user.name, "email": user.email, "id": user.id} for user in users]
    return jsonify(user_list)

@app.route("/show-subjects")
def show_subjects():
    subjects = Subject.query.all()
    subjects_list = [{"name": subject.name, "user_id": subject.user_id, "id": subject.id} for subject in subjects]

    return jsonify(subjects_list)

@app.route("/show-decks")
def show_decks():
    decks = Deck.query.all()
    decks_list = [{"name": deck.name, "user_id": deck.user_id, "id": deck.id, "subject_id": deck.subject_id} for deck in decks]

    return jsonify(decks_list)

@app.route("/show-flashcards")
def show_flashcards():
    flashcards = Flashcard.query.all()
    flashcards_list = [{"question": flashcard.question, "answer": flashcard.answer, "user_id": flashcard.user_id, "id": flashcard.id, "subject_id": flashcard.subject_id, "deck_id": flashcard.deck_id, "status": flashcard.status} for flashcard in flashcards]

    return jsonify(flashcards_list)

@app.route('/get-decks', methods=['GET'])
@jwt_required()
def get_decks():
    try:
        subject_id = request.args.get('subject_id')  # Get the subject ID from the query parameters
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Fetch all decks for this subject and user
        decks = Deck.query.filter_by(subject_id=subject_id, user_id=user_id).all()

        if decks:
            # Return a list of decks as JSON
            return jsonify({'decks': [deck.to_dict() for deck in decks]}), 200
        else:
            # Handle the case where there are no decks for this subject
            return jsonify({'message': 'No decks found for this subject!'}), 404
    except Exception as e:
        # Log the error and return a 500 response
        print(f"Error fetching decks: {e}")
        return jsonify({'message': 'An error occurred while fetching decks.'}), 500
    
@app.route('/fetch-all-decks', methods=['GET'])
@jwt_required()
def fetch_decks():
    try:
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Fetch all decks for this subject and user
        decks = Deck.query.filter_by(user_id=user_id).all()

        if decks:
            # Return a list of decks as JSON
            return jsonify({'decks': [deck.to_dict() for deck in decks]}), 200
    except Exception as e:
        # Log the error and return a 500 response
        print(f"Error fetching decks: {e}")
        return jsonify({'message': 'An error occurred while fetching decks.'}), 500
    
@app.route('/get-subject-name/<int:subject_id>', methods=['GET'])
@jwt_required()
def get_subject_name(subject_id):
    try:
        user_id = get_jwt_identity()
        subject = Subject.query.filter_by(id=subject_id, user_id=user_id).first()
        if subject:
            return jsonify({'subject_name': subject.name}), 200

    except Exception as e:
        print(f"Error getting subject name: {e}")
        return jsonify({'message': 'An error occurred while fetching subject name.'}), 500
    
@app.route('/delete-deck-api', methods=['DELETE'])
@jwt_required()
def delete_deck():
    try:
        data = request.get_json()
        deck_id = data.get('deckId')
        user_id = int(get_jwt_identity())

        if not deck_id or not user_id:
            return jsonify({'message': 'Deck ID and user ID are required!'}), 400

        # Verify that the deck belongs to the user
        deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first()
        if not deck:
            return jsonify({'message': 'Deck not found or unauthorized!'}), 404

        # Delete the deck and all associated flashcards
        db.session.delete(deck)
        db.session.commit()

        return jsonify({'message': 'Deck deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()  # Rollback the transaction in case of an error
        print(f"Error deleting deck: {e}")
        return jsonify({'message': 'An error occurred while deleting the deck.'}), 500
    
@app.route('/add-generated-flashcards-to-deck/<int:deck_id>', methods=['POST'])
@jwt_required()
def add_generated_flashcards_to_deck(deck_id):
    try:
        data = request.get_json()
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Log the request data for debugging
        print("Request Data:", data)

        # Validate required fields
        flashcards = data.get('flashcards')
        subject_id = data.get('subject_id')

        if not flashcards or not subject_id:
            return jsonify({'message': 'Flashcards and subject_id are required!'}), 400

        # Fetch the deck to ensure it belongs to the user
        deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first()

        if not deck:
            return jsonify({'message': 'Deck not found or does not belong to the user.'}), 404

        # Add each flashcard  to the deck
        for flashcard_data in flashcards:
            question = flashcard_data.get('question')
            answer = flashcard_data.get('answer')

            if not question or not answer:
                print(f"Skipping invalid flashcard: {flashcard_data}")
                continue  # Skip invalid flashcards

            # Create a new flashcard
            new_flashcard = Flashcard(
                question=question,
                answer=answer,
                status="untouched",  # Default status
                deck_id=deck_id,
                subject_id=subject_id,
                user_id=user_id
            )

            # Add the flashcard to the database session
            db.session.add(new_flashcard)

        # Commit the changes to the database
        db.session.commit()

        return jsonify({'message': 'Flashcards added to the deck successfully!'}), 200

    except Exception as e:
        # Rollback in case of an error
        db.session.rollback()
        print(f"Error adding flashcards to deck: {e}")
        return jsonify({'message': 'An error occurred while adding flashcards to the deck.'}), 500


    
@app.route("/create-flashcards-from-text", methods=["POST"])
@jwt_required()  # Ensure the request has a valid JWT
def create_flashcards_from_text():
    try:
        data = request.get_json()

        # Extract the text and deck_id from the data
        text = data.get('text')
        deck_id = data.get('deck_id')
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Validate required fields
        if not text or not deck_id or not user_id:
            return jsonify({'message': 'Text, deck_id, and user_id are required.'}), 400

        # Fetch the deck to get the subject_id
        deck = Deck.query.filter_by(id=deck_id, user_id=user_id).first()
        if not deck:
            return jsonify({'message': 'Deck not found or does not belong to the user.'}), 404

        subject_id = deck.subject_id  # Get the subject_id from the deck

        # Split the text into lines and remove empty lines
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Validate that the number of lines is even (pairs of questions and answers)
        if len(lines) % 2 != 0:
            return jsonify({'message': 'Invalid text format. Ensure each question has an answer.'}), 400

        # Create flashcards from the extracted text
        flashcards = []
        for i in range(0, len(lines), 2):
            question = lines[i]
            answer = lines[i + 1]

            # Create a new flashcard and add it to the database
            new_flashcard = Flashcard(
                question=question,
                answer=answer,
                deck_id=deck_id,
                subject_id=subject_id,
                user_id=user_id
            )
            db.session.add(new_flashcard)
            flashcards.append(new_flashcard.to_dict())

        # Commit the changes to the database
        db.session.commit()

        return jsonify({"flashcards": flashcards}), 201
    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the transaction in case of an error
        print(f"Database error: {e}")
        return jsonify({'message': 'An error occurred while saving flashcards to the database.'}), 500
    except Exception as e:
        print(f"Error creating flashcards: {e}")
        return jsonify({'message': 'An error occurred while creating flashcards.'}), 500
    
@app.route('/study-deck/<int:deck_id>', methods=['GET'])
# @jwt_required()
def study_deck(deck_id):
    return render_template('study.html')
    
@app.route("/update-flashcard-status", methods=['POST'])
@jwt_required()
def update_flashcard_status():
    try:
        data = request.get_json()

        # Extract the flashcard_id and status from the data
        flashcard_id = data.get('flashcard_id')
        deck_id = data.get('deck_id')
        status = data.get('status')
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Validate required fields
        if not flashcard_id or not status or not user_id:
            return jsonify({'message': 'Flashcard ID, status, and user_id are required.'}), 400

        # Fetch the flashcard to update its status
        flashcard = Flashcard.query.filter_by(id=flashcard_id, user_id=user_id, deck_id=deck_id).first()
        if not flashcard:
            return jsonify({'message': 'Flashcard not found or does not belong to the user.'}), 404

        # Update the flashcard status
        flashcard.status = status
        db.session.commit()  # Commit the changes to the database

        # Return a success response
        return jsonify({'message': 'Flashcard status updated successfully.'}), 200
    except Exception as e:
        print(f"Error updating flashcard status: {e}")
        db.session.rollback()  # Rollback in case of an error
        return jsonify({'message': 'An error occurred while updating flashcard status.'}), 500
    
@app.route("/get-flashcards-list", methods=["POST"])
@jwt_required()
def get_flashcards_list():
    try:
        data = request.get_json()

        # Extract the deck_id and q_flashcards from the data
        q_flashcards = int(data.get('q_flashcards'))
        deck_id = int(data.get('deck_id'))
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Validate required fields
        if not deck_id or not user_id:
            return jsonify({'message': 'Deck ID and user ID are required.'}), 400

        # Validate q_flashcards
        if not q_flashcards:
            return jsonify({'message': 'Invalid quantity of flashcards requested.'}), 400

        # Fetch the flashcards for the specified deck
        flashcards = Flashcard.query.filter_by(deck_id=deck_id, user_id=user_id).all()

        # If no flashcards are found, return an empty list
        if not flashcards:
            return jsonify({"flashcards": []}), 200

        # Convert flashcards to a 2D list
        flashcards_2d = [
            [flashcard.id, flashcard.question, flashcard.answer, flashcard.status]
            for flashcard in flashcards
        ]

        STATUS_INDEX = 3  # Index of the status field in the 2D list

        # Get the final list of flashcards
        random_flashcards = get_random_list(flashcards_2d, quantity=q_flashcards, status_index=STATUS_INDEX)
        return jsonify({"flashcards": random_flashcards}), 200
    except Exception as e:
        print(f"Error fetching flashcards for deck: {e}")
        return jsonify({'message': 'An error occurred while fetching flashcards.'}), 500

def get_random_list(flashcards, quantity, status_index):
    # Separate flashcards into untouched and others
    untouched = [card for card in flashcards if card[status_index] == "untouched"]
    others = [card for card in flashcards if card[status_index] != "untouched" and card[status_index] != "learned"]

    # Initialize the final list with untouched flashcards
    final_list = untouched[:quantity]  # Take up to 'quantity' untouched flashcards

    # If we still need more flashcards, randomly select from the 'others' list
    while len(final_list) < quantity and others:
        random_index = random.randint(0, len(others) - 1)
        final_list.append(others.pop(random_index))  # Add a random card and remove it from 'others'

    # If we still need more flashcards and 'others' is empty, reset 'others' to all non-learned flashcards
    if len(final_list) < quantity:
        others = [card for card in flashcards if card[status_index] != "learned"]
        while len(final_list) < quantity and others:
            random_index = random.randint(0, len(others) - 1)
            final_list.append(others.pop(random_index))

    return final_list

@app.route("/reset-deck-status/<int:deck_id>", methods=["POST"])
@jwt_required()
def reset_deck_status(deck_id):
    try:
        user_id = int(get_jwt_identity())  # Get the user ID from the JWT token

        # Fetch all flashcards in the deck that belong to the user
        flashcards = Flashcard.query.filter_by(deck_id=deck_id, user_id=user_id).all()

        if not flashcards:
            return jsonify({"message": "No flashcards found in this deck."}), 404

        # Reset the status of all flashcards to "untouched"
        for flashcard in flashcards:
            flashcard.status = "untouched"
        db.session.commit()

        return jsonify({"message": "Deck status reset successfully."}), 200
    except Exception as e:
        print(f"Error resetting deck status: {e}")
        db.session.rollback()
        return jsonify({"message": "An error occurred while resetting the deck status."}), 500
    

@app.route('/open-deck/<int:deck_id>', methods=['GET'])
def open_deck(deck_id):
    return render_template('open_deck.html')

@app.route('/check-deck-exists', methods=['GET'])
@jwt_required()
def check_deck_exists():
    user_id = int(get_jwt_identity())
    try:
        # Query the database for decks with the given user_id
        decks_exist = Deck.query.filter_by(user_id=user_id).first() is not None

        # Return the result as JSON
        return jsonify({"decks_exist": decks_exist}), 200
    except Exception as e:
        print(f"Error checking decks: {e}")
        return jsonify({"message": "An error occurred while checking decks."}), 500
    

if __name__ == '__main__':
    init_db()  # Initialize the database when the app starts
    app.run(host='0.0.0.0', port=5000, debug=True)
