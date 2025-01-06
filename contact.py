from flask import Blueprint, request, jsonify
import pymongo

# Créer un Blueprint pour les routes de contact
contact_bp = Blueprint('contact', __name__)

# Connexion à MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["database1"]  # Remplacez par le nom de votre base de données
user_collection = db["contact"]  # La collection "contact" dans la base de données

# Route pour traiter le formulaire de contact
@contact_bp.route('/api/contact', methods=['POST'])
def contact_form():
    try:
        # Récupérer les données envoyées depuis le front-end
        data = request.get_json()

        # Valider les données reçues
        if not all(field in data for field in ['firstName', 'lastName', 'email', 'message']):
            return jsonify({"message": "Tous les champs sont requis."}), 400

        # Créer un objet de contact avec les données
        contact_info = {
            'firstName': data['firstName'],
            'lastName': data['lastName'],
            'email': data['email'],
            'message': data['message']
        }

        # Sauvegarder les informations du formulaire dans la collection "contact" de MongoDB
        result = user_collection.insert_one(contact_info)  # Insérer les données dans MongoDB

        # Inclure l'ObjectId dans la réponse après l'avoir converti en chaîne
        contact_info['_id'] = str(result.inserted_id)

        # Exemple de réponse de confirmation
        return jsonify({
            'message': 'Formulaire de contact envoyé avec succès.',
            'contact': contact_info
        }), 200

    except Exception as e:
        # Gérer les erreurs et retourner un message d'erreur
        return jsonify({"message": f"Erreur: {str(e)}"}), 500
