from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import requests
import re
from geopy.distance import geodesic

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mitfahrboerse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Datenbankinitialisierung
db = SQLAlchemy(app)

class Mitfahrgelegenheit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plz = db.Column(db.String(10), nullable=False)
    ort = db.Column(db.String(100), nullable=False)
    strasse = db.Column(db.String(200), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    klasse = db.Column(db.String(50), nullable=True)
    handy = db.Column(db.String(20), nullable=True)
    gueltig_von = db.Column(db.String(20), nullable=True)
    gueltig_bis = db.Column(db.String(20), nullable=True)
    info = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

with app.app_context():
    db.create_all()

def is_valid_input(data):
    if not re.fullmatch(r'\d{5}', data['plz']):
        return 'Ungültige PLZ! Muss 5 Ziffern enthalten.'
    if not re.fullmatch(r'^[a-zA-ZäöüÄÖÜß\s-]+$', data['ort']):
        return 'Ungültiger Ort! Nur Buchstaben, Leerzeichen und Bindestriche erlaubt.'
    if not re.fullmatch(r'^[a-zA-ZäöüÄÖÜß\s-]+$', data['name']):
        return 'Ungültiger Name! Nur Buchstaben, Leerzeichen und Bindestriche erlaubt.'
    if not re.fullmatch(r'^[\w\.-]+@[\w\.-]+\.\w+$', data['email']):
        return 'Ungültige E-Mail-Adresse!'
    if 'handy' in data and data['handy'] and not re.fullmatch(r'^[+]?\d+$', data['handy']):
        return 'Ungültige Handynummer! Nur Zahlen und optional ein führendes + erlaubt.'
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/offer', methods=['POST'])
def offer():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Keine Daten empfangen!'}), 400

    required_fields = ['plz', 'ort', 'name', 'email']
    for field in required_fields:
        if field not in data or not data[field].strip():
            return jsonify({'error': f'{field} ist erforderlich!'}), 400
    
    validation_error = is_valid_input(data)
    if validation_error:
        return jsonify({'error': validation_error}), 400

    location = f"{data['plz']} {data['ort']}, Germany"
    geocode_url = f"https://nominatim.openstreetmap.org/search?format=json&q={location}"
    headers = {'User-Agent': 'Mitfahrboerse/1.0 (winklerr535@gmail.com)'}

    try:
        response = requests.get(geocode_url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        latitude = float(response_json[0]['lat']) if response_json else None
        longitude = float(response_json[0]['lon']) if response_json else None
    except requests.exceptions.RequestException as e:
        print(f"Fehler bei der API-Anfrage: {e}")
        return jsonify({'error': 'Fehler bei der Geocoding-Anfrage.'}), 500

    mitfahrgelegenheit = Mitfahrgelegenheit(
        plz=data['plz'],
        ort=data['ort'],
        strasse=data.get('strasse'),
        name=data['name'],
        email=data['email'],
        klasse=data.get('klasse'),
        handy=data.get('handy'),
        gueltig_von=data.get('gueltig_von'),
        gueltig_bis=data.get('gueltig_bis'),
        info=data.get('info'),
        latitude=latitude,
        longitude=longitude
    )

    try:
        db.session.add(mitfahrgelegenheit)
        db.session.commit()
        return jsonify({'message': 'Mitfahrgelegenheit erfolgreich angeboten!'}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Fehler beim Speichern: {e}")
        return jsonify({'error': 'Fehler beim Speichern.'}), 500

@app.route('/api/offers', methods=['GET'])
def get_all_offers():
    results = Mitfahrgelegenheit.query.all()
    return jsonify([{**vars(fahrt), '_sa_instance_state': None} for fahrt in results]), 200

@app.route('/api/search', methods=['GET'])
def search_offer():
    plz = request.args.get('plz')
    ort = request.args.get('ort')
    if not plz or not ort:
        return jsonify({'error': 'PLZ und Ort sind erforderlich'}), 400
    results = Mitfahrgelegenheit.query.filter_by(plz=plz, ort=ort).all()
    if not results:
        return jsonify({'error': 'Keine Angebote gefunden'}), 404
    return jsonify([{**vars(fahrt), '_sa_instance_state': None} for fahrt in results]), 200

@app.route('/api/search_radius', methods=['GET'])
def search_radius():
    plz = request.args.get('plz')
    ort = request.args.get('ort')
    radius = request.args.get('radius', type=int)

    if not plz or not ort or not radius:
        return jsonify({'error': 'PLZ, Ort und Radius sind erforderlich'}), 400

    # Geocoding, um die geographischen Koordinaten (Latitude und Longitude) des Ortes zu ermitteln
    location = f"{plz} {ort}, Germany"
    geocode_url = f"https://nominatim.openstreetmap.org/search?format=json&q={location}"
    headers = {'User-Agent': 'Mitfahrboerse/1.0 (winklerr535@gmail.com)'}

    try:
        response = requests.get(geocode_url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        latitude = float(response_json[0]['lat']) if response_json else None
        longitude = float(response_json[0]['lon']) if response_json else None
    except requests.exceptions.RequestException as e:
        print(f"Fehler bei der API-Anfrage: {e}")
        return jsonify({'error': 'Fehler bei der Geocoding-Anfrage.'}), 500

    if not latitude or not longitude:
        return jsonify({'error': 'Geocoding für den angegebenen Ort fehlgeschlagen.'}), 500

    # Angebote aus der Datenbank, die innerhalb des Radius liegen
    results = Mitfahrgelegenheit.query.all()
    nearby_offers = []

    for offer in results:
        # Berechne die Entfernung zwischen dem aktuellen Angebot und dem eingegebenen Standort
        offer_location = (offer.latitude, offer.longitude)
        user_location = (latitude, longitude)
        distance = geodesic(user_location, offer_location).km  # Entfernung in km

        # Wenn die Entfernung innerhalb des Radius liegt, füge das Angebot zu den Ergebnissen hinzu
        if distance <= radius:
            nearby_offers.append({**vars(offer), '_sa_instance_state': None})

    if not nearby_offers:
        return jsonify({'error': 'Keine Angebote im angegebenen Radius gefunden'}), 404

    return jsonify(nearby_offers), 200

if __name__ == '__main__':
    app.run(debug=True)
