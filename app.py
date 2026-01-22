from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import hashlib, json, os, requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cle-secrete-ww3-2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# Limite : 1 vote par minute par IP
limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")

FICHIER_DATA = "data.json"

def charger_donnees():
    if os.path.exists(FICHIER_DATA):
        with open(FICHIER_DATA, 'r') as f: return json.load(f)
    return {"OUI": 0, "NON": 0, "IP_HASHES": [], "MESSAGES": []}

db = charger_donnees()

def obtenir_pays(ip):
    try:
        if ip == '127.0.0.1': return 'FR'
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
        return r.get('countryCode', 'UN')
    except: return "UN"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/voter', methods=['POST'])
@limiter.limit("1 per minute")
def voter():
    choix = request.json.get('choix')
    ip_hash = hashlib.sha256(request.remote_addr.encode()).hexdigest()

    if ip_hash in db["IP_HASHES"]:
        return jsonify({"erreur": "Vous avez déjà exprimé votre opinion."}), 403

    if choix in ["OUI", "NON"]:
        db[choix] += 1
        db["IP_HASHES"].append(ip_hash)
        pays = obtenir_pays(request.remote_addr)
        with open(FICHIER_DATA, 'w') as f: json.dump(db, f)
        
        socketio.emit('mise_a_jour', {
            'oui': db['OUI'], 'non': db['NON'], 
            'total': db['OUI'] + db['NON'], 'pays': pays
        })
        return jsonify({"succes": "Vote enregistré"})
    return jsonify({"erreur": "Action invalide"}), 400

@app.route('/envoyer_message', methods=['POST'])
@limiter.limit("2 per minute")
def msg():
    texte = request.json.get('message', '')[:100]
    if texte:
        pays = obtenir_pays(request.remote_addr)
        nouveau = {"texte": texte, "pays": pays}
        db["MESSAGES"].insert(0, nouveau)
        db["MESSAGES"] = db["MESSAGES"][:10]
        socketio.emit('nouveau_message', nouveau)
        return jsonify({"succes": "Message envoyé"})
    return jsonify({"erreur": "Message vide"}), 400

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)