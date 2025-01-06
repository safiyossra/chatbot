
from flask import Flask, request, jsonify, render_template
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import google.generativeai as genai
import os
import textwrap
from flask import Flask, request, jsonify, render_template
from connexion import add_user, authenticate_user, user_exists ,create_auth_token
from werkzeug.security import generate_password_hash
from flask_cors import CORS  # Importez CORS
from contact import contact_bp  # Importer les routes du fichier contact.py
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
import pymongo
import jwt
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
import pymongo
import jwt
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import textwrap
from rapidfuzz import process  # Pour la recherche floue

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["database1"]  # Remplacez par le nom de votre base de données
user_collection = db["users"]

SECRET_KEY = 'yossra'

# Configuration de MongoDB et Flask
app = Flask(__name__)
CORS(app, supports_credentials=True)

GOOGLE_API_KEY = 'AIzaSyDlny_qz8tHGX2NfxWfou1SYaaxV_wPSUA'
genai.configure(api_key=GOOGLE_API_KEY)

# Configuration de Chroma pour la persistance
CHROMA_DB_DIRECTORY = "C:/ChatBot-main/data/chroma_db"  # Répertoire où les données seront stockées

# Utilisation du modèle de génération Google
model = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY, temperature=0.2)

# Charger et diviser plusieurs PDF à partir d'un répertoire
pdf_directory = "C:/ChatBot-main/data" 
pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]

pages = []
for pdf_file in pdf_files:
    pdf_path = os.path.join(pdf_directory, pdf_file)
    pdf_loader = PyPDFLoader(pdf_path)
    pages.extend(pdf_loader.load_and_split())

# Préparer le texte pour l'intégration avec les embeddings
text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
context = "\n\n".join(str(p.page_content) for p in pages)
texts = text_splitter.split_text(context)

# Embedding avec Google Generative AI
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)

# Vérifiez si une base de données Chroma existe déjà, sinon créez-en une
if not os.path.exists(CHROMA_DB_DIRECTORY):
    os.makedirs(CHROMA_DB_DIRECTORY)
    # Créer une nouvelle base de données Chroma et y ajouter les textes
    vector_index = Chroma.from_texts(texts, embeddings, persist_directory=CHROMA_DB_DIRECTORY)
    vector_index.persist()  # Enregistrer la base de données sur le disque
else:
    # Charger la base de données Chroma existante
    vector_index = Chroma(persist_directory=CHROMA_DB_DIRECTORY, embedding_function=embeddings)

# Modèle de question et de réponse pour la cybersécurité
template = """Utilisez les éléments de contexte suivants pour répondre à la question à la fin. Si vous ne connaissez pas la réponse, dites simplement que vous ne savez pas, n'essayez pas d'inventer une réponse. 
Renvoyez une réponse sous forme de phrases complètes et pertinentes en vous concentrant sur les bonnes pratiques en cybersécurité. Terminez toujours la réponse par "Merci pour votre question !".
{context}
Question : {question}
Réponse utile :"""


QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

qa_chain = RetrievalQA.from_chain_type(
    model,
    retriever=vector_index.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True,
    chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
)




@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('question')

    if user_input:
        # Interroger la chaîne de récupération avec la question de l'utilisateur
        result = qa_chain.invoke({"query": user_input})

        # Convertir les documents source en chaînes de caractères
        source_documents = [str(doc) for doc in result['source_documents']]

        # Limiter la réponse pour éviter des longueurs excessives
        response_text = result['result'][:900]  # Limiter la longueur de la réponse pour la cybersécurité

        # Renvoi de la réponse
        return jsonify({
            'response': response_text,
            'sources': source_documents
        })
    return jsonify({'error': 'No question provided'}), 400







@app.route('/')
def index():
    return render_template('index.html')




from flask import Flask, request, jsonify
from connexion import add_user, authenticate_user, user_exists  

@app.route('/register', methods=['POST'])
def register():
    try:
        # Récupération des données du formulaire
        data = request.get_json()
        if not data:
            print("Erreur: Aucune donnée JSON reçue.")  # Debug
            return jsonify({'error': 'Requête invalide, aucune donnée reçue.'}), 400

        print(f"Données reçues: {data}")  # Debug: Afficher les données reçues

        # Vérification de la présence de tous les champs requis
        required_fields = ['first_name', 'last_name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                print(f"Erreur: Le champ {field} est manquant ou vide.")  # Debug
                return jsonify({'error': f"Le champ {field} est requis."}), 400

        first_name = data['first_name']
        last_name = data['last_name']
        email = data['email']
        password = data['password']

        # Vérification si l'utilisateur existe déjà
        if user_exists(email):
            print(f"L'utilisateur avec l'email {email} existe déjà.")  # Debug
            return jsonify({'error': 'Utilisateur déjà existant.'}), 400

        # Ajouter l'utilisateur
        user = add_user(first_name, last_name, email, password)

        # Vérification du succès de l'ajout de l'utilisateur
        if user:
            print(f"Utilisateur ajouté avec succès: {user}")  # Debug
            return jsonify({'message': 'Inscription réussie !'}), 201
        else:
            print("Erreur lors de l'ajout de l'utilisateur.")  # Debug
            return jsonify({'error': 'Une erreur est survenue pendant l\'inscription.'}), 500

    except Exception as e:
        print(f"Erreur générale: {e}")  # Debug: Afficher l'erreur
        return jsonify({'error': f"Une erreur est survenue : {str(e)}"}), 500


# Route pour la connexion de l'utilisateur
@app.route('/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        print(f"Essayer de se connecter avec email: {email}")  # Debug

        user = authenticate_user(email, password)
        
        # Debugging - afficher l'utilisateur retourné
        print(f"Utilisateur trouvé: {user}")
        
        if user:
            # Si l'utilisateur existe, assurez-vous qu'il a bien un 'id'
            if user.get('_id'):  # Utilisation de get pour éviter les erreurs
                print("Connexion réussie")  # Debug
                # Création du token
                token = create_auth_token(user["_id"])
                return jsonify({"message": "Connexion réussie", "user": user, "token": token}), 200
            else:
                print("Utilisateur trouvé sans '_id'")  # Debug
                return jsonify({"error": "Utilisateur invalide"}), 400
        else:
            print("Email ou mot de passe incorrect")  # Debug
            return jsonify({"error": "Email ou mot de passe incorrect"}), 401
    except Exception as e:
        print(f"Erreur lors de la connexion : {e}")  # Debug
        return jsonify({"error": "Une erreur est survenue."}), 500




# Route par défaut pour vérifier que l'application fonctionne
app.register_blueprint(contact_bp)


@app.route('/user', methods=['GET'])
def get_user():
    token = request.headers.get('Authorization')
    if token:
        try:
            # Extraire le token et le décoder
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token['user_id']
            
            # Rechercher l'utilisateur dans la collection MongoDB
            user = user_collection.find_one({"_id": ObjectId(user_id)})
            if user:
                # Convertir l'ObjectId en chaîne pour éviter les problèmes de sérialisation JSON
                user["_id"] = str(user["_id"])
                return jsonify({"first_name": user['first_name'], "last_name": user['last_name']}), 200
            else:
                return jsonify({"error": "User not found"}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
    return jsonify({"error": "No token provided"}), 400

if __name__ == '__main__':
    app.run(debug=True)
CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})  






