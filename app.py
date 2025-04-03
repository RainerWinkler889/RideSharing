from flask import Flask, request, jsonify, render_template, session, redirect
from flask_sqlalchemy import SQLAlchemy
import requests
import re
from geopy.distance import geodesic
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mitfahrboerse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mein_geheimes_schluessel'  # Setze ein geheimes Schlüssel für Sessions

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
    edit_code = db.Column(db.String(10), nullable=False)

with app.app_context():
    db.create_all()

def generate_edit_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

@app.before_request
def redirect_to_captcha():
    if 'captcha_verified' not in session:
        if request.endpoint and 'static' not in request.endpoint:  # Statische Dateien nicht umleiten
            if request.endpoint not in ['captcha', 'recaptcha']:
                return redirect('/recaptcha')

@app.route('/')
def index():
    return render_template('index.html')  # Diese Seite wird nur angezeigt, wenn das CAPTCHA bestanden wurde.

@app.route('/recaptcha', methods=['GET', 'POST'])
def captcha():
    if request.method == 'POST':
        # Überprüfe, ob die eingegebene Zahl korrekt ist
        captcha_input = request.form.get('captcha_input')
        if captcha_input == str(session.get('captcha_number')):
            session['captcha_verified'] = True  # Benutzer hat CAPTCHA bestanden
            return redirect('/')  # Weiterleitung zur Hauptseite nach erfolgreicher Eingabe
        else:
            return redirect('/recaptcha')  # Bei falscher Eingabe zurück zur CAPTCHA-Seite
    
    # Generiere eine zufällige 4-stellige Zahl für das CAPTCHA
    captcha_number = random.randint(1000, 9999)
    session['captcha_number'] = captcha_number  # Speichere die Zahl in der Session
    
    return render_template('recaptcha.html', captcha_number=captcha_number)

@app.route('/index')
def index_page():
    return render_template('index.html')  # Deine Hauptseite (index.html)

@app.route('/api/offer', methods=['POST'])
def offer():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Keine Daten empfangen!'}), 400

    required_fields = ['plz', 'ort', 'name', 'email']
    for field in required_fields:
        if field not in data or not data[field].strip():
            return jsonify({'error': f'{field} ist erforderlich!'}), 400

    location = f"{data['plz']} {data['ort']}, Germany"
    geocode_url = f"https://nominatim.openstreetmap.org/search?format=json&q={location}"
    headers = {'User-Agent': 'Mitfahrboerse/1.0'}

    try:
        response = requests.get(geocode_url, headers=headers)
        response.raise_for_status()
        response_json = response.json()

        if response_json:
            latitude = float(response_json[0]['lat'])
            longitude = float(response_json[0]['lon'])
        else:
            return jsonify({'error': 'Geolocation konnte nicht ermittelt werden!'}), 500  # Kein Standardwert mehr

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Fehler bei der Geocoding-Anfrage: {str(e)}'}), 500

    edit_code = generate_edit_code()
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
        longitude=longitude,
        edit_code=edit_code
    )

    try:
        db.session.add(mitfahrgelegenheit)
        db.session.commit()
        return jsonify({'message': 'Mitfahrgelegenheit erfolgreich angeboten!', 'edit_code': edit_code}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Fehler beim Speichern: ' + str(e)}), 500

@app.route('/api/offers', methods=['GET'])
def get_all_offers():
    results = Mitfahrgelegenheit.query.all()
    return jsonify([{key: getattr(fahrt, key) for key in vars(fahrt) if key != '_sa_instance_state'} for fahrt in results]), 200

@app.route('/api/search', methods=['GET'])
def search_offer():
    plz = request.args.get('plz')
    ort = request.args.get('ort')
    if not plz or not ort:
        return jsonify({'error': 'PLZ und Ort sind erforderlich'}), 400

    location = f"{plz} {ort}, Germany"
    geocode_url = f"https://nominatim.openstreetmap.org/search?format=json&q={location}"
    headers = {'User-Agent': 'Mitfahrboerse/1.0'}

    try:
        response = requests.get(geocode_url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        
        # Überprüfe die Antwort
        if not response_json:
            return jsonify({'error': f'Geocoding keine Ergebnisse für {location}'}), 500
        
        latitude = float(response_json[0]['lat']) if response_json else None
        longitude = float(response_json[0]['lon']) if response_json else None

        # Falls keine Koordinaten gefunden wurden, gibt eine Fehlermeldung zurück
        if not latitude or not longitude:
            return jsonify({'error': f'Koordinaten für {location} konnten nicht gefunden werden.'}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Fehler bei der Geocoding-Anfrage: ' + str(e)}), 500

    results = Mitfahrgelegenheit.query.filter_by(plz=plz, ort=ort).all()
    if not results:
        return jsonify({'error': 'Keine Angebote gefunden'}), 404
    return jsonify([{key: getattr(fahrt, key) for key in vars(fahrt) if key != '_sa_instance_state'} for fahrt in results]), 200

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
    headers = {'User-Agent': 'Mitfahrboerse/1.0'}

    try:
        response = requests.get(geocode_url, headers=headers)
        response.raise_for_status()
        response_json = response.json()
        
        # Überprüfe die Antwort
        if not response_json:
            return jsonify({'error': f'Geocoding keine Ergebnisse für {location}'}), 500
        
        latitude = float(response_json[0]['lat']) if response_json else None
        longitude = float(response_json[0]['lon']) if response_json else None

        # Falls keine Koordinaten gefunden wurden, gibt eine Fehlermeldung zurück
        if not latitude or not longitude:
            return jsonify({'error': f'Koordinaten für {location} konnten nicht gefunden werden.'}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Fehler bei der Geocoding-Anfrage: ' + str(e)}), 500

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
            nearby_offers.append({key: getattr(offer, key) for key in vars(offer) if key != '_sa_instance_state'})

    if not nearby_offers:
        return jsonify({'error': 'Keine Angebote im angegebenen Radius gefunden'}), 404

    return jsonify(nearby_offers), 200

@app.route('/api/edit_offer', methods=['PUT', 'POST'])
def edit_offer():
    if request.method == 'POST':
        data = request.form.to_dict()
    else:
        data = request.get_json()

    if not data or 'edit_code' not in data or not data['edit_code'].strip():
        return jsonify({'error': 'Bearbeitungscode ist erforderlich!'}), 400

    offer = Mitfahrgelegenheit.query.filter_by(edit_code=data['edit_code']).first()
    if not offer:
        return jsonify({'error': 'Kein Angebot mit diesem Bearbeitungscode gefunden!'}), 404

    new_plz = data.get('plz', offer.plz)
    new_ort = data.get('ort', offer.ort)

    # Nur wenn PLZ oder Ort geändert wurden, neue Koordinaten holen
    if new_plz != offer.plz or new_ort != offer.ort:
        location = f"{new_plz} {new_ort}, Germany"
        geocode_url = f"https://nominatim.openstreetmap.org/search?format=json&q={location}"
        headers = {'User-Agent': 'Mitfahrboerse/1.0'}

        try:
            response = requests.get(geocode_url, headers=headers)
            response.raise_for_status()
            response_json = response.json()

            if response_json:
                offer.latitude = float(response_json[0]['lat'])
                offer.longitude = float(response_json[0]['lon'])
            else:
                return jsonify({'error': 'Geolocation konnte nicht aktualisiert werden!'}), 500

        except requests.exceptions.RequestException as e:
            return jsonify({'error': f'Fehler bei der Geocoding-Anfrage: {str(e)}'}), 500

    # Alle anderen Felder aktualisieren, wenn sie angegeben sind
    allowed_fields = ['plz', 'ort', 'strasse', 'name', 'email', 'klasse', 'handy', 'gueltig_von', 'gueltig_bis', 'info']
    for field in allowed_fields:
        if field in data and data[field].strip():
            setattr(offer, field, data[field])

    try:
        db.session.commit()
        return jsonify({'message': 'Mitfahrgelegenheit erfolgreich aktualisiert!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Fehler beim Aktualisieren: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=False)