from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mitfahrboerse.db'
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

db.create_all()

@app.route('/suchen', methods=['GET'])
def suchen():
    plz = request.args.get('plz')
    ort = request.args.get('ort')

    if not plz or not ort:
        return jsonify({'error': 'PLZ und Ort sind Pflichtfelder!'}), 400

    ergebnisse = Mitfahrgelegenheit.query.filter_by(plz=plz, ort=ort).all()
    
    ergebnisliste = [
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
        } for fahrt in ergebnisse
    ]

    return jsonify(ergebnisliste), 200