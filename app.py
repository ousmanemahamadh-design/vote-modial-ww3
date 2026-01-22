 import os
import json
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Nom du fichier de sauvegarde
DATA_FILE = "votes.json"

# Fonction pour charger les votes depuis le fichier
def load_votes():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"OUI": 0, "NON": 0, "WA": 0}

# Fonction pour sauvegarder les votes dans le fichier
def save_votes(v):
    with open(DATA_FILE, "w") as f:
        json.dump(v, f)

# Initialisation des votes au démarrage
votes = load_votes()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('vote')
def handle_vote(data):
    choice = data.get('choice')
    if choice in votes:
        votes[choice] += 1
        save_votes(votes)  # Sauvegarde immédiate
        emit('update_votes', votes, broadcast=True)

@socketio.on('get_initial_votes')
def handle_initial_votes():
    emit('update_votes', votes)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
