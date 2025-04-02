import sqlite3
import random

# Verbindung zur SQLite-Datenbank herstellen
db_path = "mitfahrboerse.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tabelle erstellen, falls nicht vorhanden
cursor.execute("""
CREATE TABLE IF NOT EXISTS mitfahrgelegenheit (
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

# Datei DE.txt einlesen
with open('/Users/paulrau/Downloads/app_python/RideSharing/DE.txt', 'r') as f:
    lines = f.readlines()

# Alle relevanten Daten aus der DE.txt extrahieren
orte = []
for line in lines:
    parts = line.strip().split("\t")
    if len(parts) >= 6:  # Sicherstellen, dass alle benötigten Felder vorhanden sind
        plz = parts[0]  # PLZ
        ort = parts[1]  # Ort
        lat = float(parts[4])  # Latitude
        lon = float(parts[5])  # Longitude
        orte.append((plz, ort, lat, lon))

# Liste für Namen und E-Mail-Domains
namen = ["Max Mustermann", "Erika Musterfrau", "Hans Müller", "Julia Schmidt", "Lukas Wagner",
         "Michael Schröder", "Sophie Lehmann", "Felix Becker", "Laura Fischer", "Tobias Meier"]

email_domains = ["example.com", "test.de", "demo.org", "mail.net", "webmail.com"]

# 500 zufällige Einträge generieren
data = []
for i in range(500):
    plz, ort, lat, lon = random.choice(orte)  # Zufälligen Ort wählen
    name = random.choice(namen)
    email = name.lower().replace(" ", ".") + "@" + random.choice(email_domains)

    # Eintrag in die Liste hinzufügen
    data.append((plz, ort, "", name, email, "", "", "", "", "", lat, lon))

# Einfügen in die Datenbank
cursor.executemany("""
INSERT INTO mitfahrgelegenheit (plz, ort, strasse, name, email, klasse, handy, gueltig_von, gueltig_bis, info, latitude, longitude)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
""", data)

# Änderungen speichern und Verbindung schließen
conn.commit()

# Überprüfen, ob die Daten erfolgreich eingefügt wurden
cursor.execute("SELECT COUNT(*) FROM mitfahrgelegenheit")
count = cursor.fetchone()[0]
print(f"{count} Datensätze wurden erfolgreich eingefügt.")

# Verbindung schließen
conn.close()

print("Datenbank wurde erfolgreich erstellt und Daten wurden eingefügt!")