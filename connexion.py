from flask import Flask, jsonify  # Importation de jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import pymongo
import jwt
from datetime import datetime, timedelta

# Connexion à la base de données MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["database1"]  # Remplacez par le nom de votre base de données
user_collection = db["users"]

def add_user(first_name, last_name, email, password, username=None):
    try:
        # Vérification si l'utilisateur existe déjà
        print(f"Vérification de l'existence de l'utilisateur avec l'email {email}...")  # Debug
        if user_exists(email):
            print("L'utilisateur existe déjà dans la base de données.")  # Debug
            return None

        # Hachage du mot de passe
        print(f"Hachage du mot de passe pour l'utilisateur {email}...")  # Debug
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')  # Méthode correcte

        # Création de l'objet utilisateur
        user = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": hashed_password,
            "username": username if username else email.split('@')[0]  # Par défaut, une partie de l'email comme username
        }

        # Insertion de l'utilisateur dans la base de données
        print("Insertion de l'utilisateur dans la base de données...")  # Debug
        result = user_collection.insert_one(user)

        print(f"Utilisateur ajouté avec l'ID {result.inserted_id}")  # Debug
        return user

    except Exception as e:
        print(f"Erreur lors de l'ajout de l'utilisateur: {e}")  # Debug
        return None

# # Fonction pour vérifier si l'utilisateur existe déjà
# def user_exists(email):
#     try:
#         return user_collection.find_one({"email": email}) is not None
#     except Exception as e:
#         print(f"Erreur lors de la vérification de l'utilisateur : {e}")  # Debug
#         return False

def user_exists(email):
    try:
        print(f"Recherche de l'utilisateur avec l'email {email}...")  # Debug
        user = user_collection.find_one({'email': email})
        return user is not None
    except Exception as e:
        print(f"Erreur lors de la vérification de l'existence de l'utilisateur: {e}")  # Debug
        return False

from werkzeug.security import check_password_hash
from bson.objectid import ObjectId  # Import nécessaire pour vérifier les ObjectId

SECRET_KEY = 'yossra'  # Utilisez une clé secrète pour signer le JWT

# Fonction pour authentifier l'utilisateur
def authenticate_user(email, password):
    try:
        # Récupérer l'utilisateur de la base de données
        user = user_collection.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            # Convertir ObjectId en chaîne pour la sérialisation JSON
            user["_id"] = str(user["_id"])  # Conversion de l'ObjectId en chaîne
            return user
        else:
            return None
    except Exception as e:
        print(f"Erreur lors de l'authentification : {e}")
        return None

# Fonction pour créer un token d'authentification
def create_auth_token(user_id):
    expiration = datetime.utcnow() + timedelta(hours=1)  # Le token expire après 1 heure
    token = jwt.encode(
        {'user_id': user_id, 'exp': expiration},
        SECRET_KEY,
        algorithm='HS256'
    )
    return token

