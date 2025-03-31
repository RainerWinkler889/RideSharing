from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mitfahrboerse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Datenbankmodell für Mitfahrgelegenheit
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

# Initialisiert die Datenbank, wenn sie noch nicht existiert
with app.app_context():
    db.create_all()

# Route für die Startseite (Root-URL)
@app.route('/')
def index():
    return render_template('index.html')

# API zum Speichern einer Mitfahrgelegenheit
@app.route('/api/offer', methods=['POST'])
def offer():
    # Hier kommt die Überprüfung der übergebenen Daten
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Keine Daten empfangen!'}), 400

    # Pflichtfelder prüfen
    required_fields = ['plz', 'ort', 'name', 'email']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} ist erforderlich!'}), 400

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
        info=data.get('info')
    )
    
    # Speichern in der Datenbank
    try:
        db.session.add(mitfahrgelegenheit)
        db.session.commit()
        return jsonify({'message': 'Mitfahrgelegenheit wurde erfolgreich angeboten!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Fehler beim Speichern der Mitfahrgelegenheit.'}), 500

# API zum Suchen von Mitfahrgelegenheiten
@app.route('/api/search', methods=['GET'])
def search():
    plz = request.args.get('plz')
    ort = request.args.get('ort')

    if not plz or not ort:
        return jsonify({'error': 'PLZ und Ort sind Pflichtfelder!'}), 400

    results = Mitfahrgelegenheit.query.filter_by(plz=plz, ort=ort).all()

    result_list = [
        {
            'id': fahrt.id,
            'plz': fahrt.plz,
            'ort': fahrt.ort,
            'strasse': fahrt.strasse,
            'name': fahrt.name,
            'email': fahrt.email,
            'klasse': fahrt.klasse,
            'handy': fahrt.handy,
            'gueltig_von': fahrt.gueltig_von,
            'gueltig_bis': fahrt.gueltig_bis,
            'info': fahrt.info
        } for fahrt in results
    ]

    return jsonify(result_list), 200

if __name__ == '__main__':
    app.run(debug=True)