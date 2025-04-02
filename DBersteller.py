


import sqlite3
import random

# Verbindung zur SQLite-Datenbank herstellen
db_path = "mitfahrboerse.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tabelle erstellen, falls nicht vorhanden
cursor.execute("""
CREATE TABLE IF NOT EXISTS mitfahrgelegenheiten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plz TEXT,
    ort TEXT,
    strasse TEXT,
    name TEXT,
    email TEXT,
    klasse TEXT,
    handy TEXT,
    gueltig_von TEXT,
    gueltig_bis TEXT,
    info TEXT,
    latitude REAL,
    longitude REAL
);
""")

# Zufällige Testdaten
orte = [
    ("10115", "Berlin", 52.532, 13.384),
    ("80331", "München", 48.137, 11.575),
    ("04109", "Leipzig", 51.339, 12.374),
    ("50667", "Köln", 50.939, 6.957),
    ("01067", "Dresden", 51.051, 13.741),
    ("20095", "Hamburg", 53.550, 10.000),
    ("90402", "Nürnberg", 49.452, 11.076),
    ("70173", "Stuttgart", 48.778, 9.180),
    ("60311", "Frankfurt am Main", 50.110, 8.682),
    ("28195", "Bremen", 53.081, 8.805)
]

namen = ["Max Mustermann", "Erika Musterfrau", "Hans Müller", "Julia Schmidt", "Lukas Wagner",
         "Michael Schröder", "Sophie Lehmann", "Felix Becker", "Laura Fischer", "Tobias Meier"]

email_domains = ["example.com", "test.de", "demo.org", "mail.net", "webmail.com"]

# 150 zufällige Einträge generieren
data = []
for i in range(150):
    plz, ort, lat, lon = random.choice(orte)
    name = random.choice(namen)
    email = name.lower().replace(" ", ".") + "@" + random.choice(email_domains)
    
    data.append((plz, ort, "", name, email, "", "", "", "", "", lat, lon))

# Einfügen in die Datenbank
cursor.executemany("""
INSERT INTO mitfahrgelegenheiten (plz, ort, strasse, name, email, klasse, handy, gueltig_von, gueltig_bis, info, latitude, longitude)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", data)

# Änderungen speichern und Verbindung schließen
conn.commit()

# Überprüfen, ob die Daten erfolgreich eingefügt wurden
cursor.execute("SELECT COUNT(*) FROM mitfahrgelegenheiten")
count = cursor.fetchone()[0]
print(f"{count} Datensätze wurden erfolgreich eingefügt.")

# Verbindung schließen
conn.close()

print("Datenbank wurde erfolgreich erstellt und Daten wurden eingefügt!")
