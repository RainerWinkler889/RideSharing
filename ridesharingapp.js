import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const RideSharingApp = () => {
  const [offer, setOffer] = useState({
    plz: "",
    ort: "",
    strasse: "",
    name: "",
    email: "",
  });

  // Beispielangebote mit Koordinaten
  const [offers, setOffers] = useState([
    { 
      id: 1, 
      plz: "10115", 
      ort: "Berlin", 
      strasse: "Musterstraße 1", 
      name: "Max Mustermann", 
      email: "max@example.com", 
      position: [52.5200, 13.4050] // Koordinaten für Berlin
    },
    { 
      id: 2, 
      plz: "80331", 
      ort: "München", 
      strasse: "Beispielweg 5", 
      name: "Anna Schmidt", 
      email: "anna@example.com", 
      position: [48.1351, 11.5820] // Koordinaten für München
    }
  ]);

  const handleChange = (e) => {
    setOffer({ ...offer, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    alert("Mitfahrgelegenheit angeboten: " + JSON.stringify(offer));
    // Hier kannst du auch ein API-Request machen, um das Angebot zu speichern
  };

  return (
    <div>
      <h1>Mitfahrgelegenheit anbieten</h1>
      <form onSubmit={handleSubmit}>
        <input name="plz" placeholder="PLZ" required onChange={handleChange} />
        <input name="ort" placeholder="Ort" required onChange={handleChange} />
        <input name="strasse" placeholder="Straße, Hausnummer" onChange={handleChange} />
        <input name="name" placeholder="Name" required onChange={handleChange} />
        <input name="email" placeholder="E-Mail" required onChange={handleChange} />
        <button type="submit">Anbieten</button>
      </form>

      <h1>Mitfahrgelegenheit suchen</h1>
      <form>
        <input name="plz" placeholder="PLZ" required />
        <input name="ort" placeholder="Ort" required />
        <button type="submit">Suchen</button>
      </form>

      <h1>Karte</h1>
      <MapContainer center={[51.1657, 10.4515]} zoom={6} style={{ height: "400px", width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {offers.map((o) => (
          <Marker key={o.id} position={o.position}>
            <Popup>
              <b>{o.name}</b><br/>
              {o.strasse}, {o.ort} ({o.plz})<br/>
              Email: {o.email}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};

export default RideSharingApp;