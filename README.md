# Actually Useful Task Manager

Flask web aplikacija za upravljanje taskovima sa podrškom za timski rad kroz sobe/workspaces.

## Funkcionalnosti

### Autentifikacija
- **Registracija** - Korisnici mogu da kreiraju nalog sa username, email i lozinkom
- **Login** - Sigurnosna prijava sa hešovanim lozinkama
- **Logout** - Odjava iz sistema

### Task Management
- **Kreiranje taskova** - Dodaj nove taskove u sobi (ENTER podrška)
- **Claimovanje taskova** - Preuzmi task za rad (Tasks → In Progress)
- **Završavanje taskova** - Markiraj task kao završen (In Progress → Finished)
- **Brisanje taskova** - Vlasnik sobe može da briše taskove (X dugme)
- **Praćenje autora** - Svaki task prikazuje ko ga je kreirao, claimovao i završio
- **Vremenske informacije** - Hover za prikaz vremena akcija

### Sobe / Workspaces
- **Kreiranje soba** - Napravi novu sobu sa jedinstvenim 6-znak kodom
- **Pridruživanje sobama** - Unesi kod da bi se pridružio postojećoj sobi
- **Timski rad** - Više korisnika može raditi na taskovima unutar iste sobe
- **Vlasništvo** - Prikaz vlasnika sobe sa krunom ikonom
- **Kopiranje koda** - Klik na kod sobe za automatsko kopiranje
- **Lista članova** - Pregled svih članova sa vremenom pridruživanja

## Tehnologije

- **Backend**: Flask (Python)
- **Baza podataka**: SQLite
- **Frontend**: Bootstrap 5, jQuery, Font Awesome
- **Bezbednost**: Werkzeug password hashing

## Instalacija

1. Instaliraj potrebne pakete:
```bash
pip install -r requirements.txt
```

2. Pokreni aplikaciju:
```bash
python app.py
```

Aplikacija će biti dostupna na `http://localhost:5000`

## Struktura baze podataka

### User
- id, username, email, password_hash, created_at

### Room  
- id, name, unique_code, owner_id, created_at

### RoomMember
- id, room_id, user_id, joined_at

### Task
- id, title, description, status, created_by, claimed_by, claimed_at, completed_at, created_at, room_id

## Deployment

Aplikacija je spremna za deployment na:
- PythonAnywhere (preporučeno za početnike)
- Render
- Vercel
- Glitch

## Korišćenje

1. **Registracija** - Kreiraj nalog na login stranici
2. **Kreiraj sobu** - Nakon prijave, kreiraj novu sobu ili pridruži se postojećoj
3. **Dodaj taskove** - Unutar sobe dodaj nove taskove
4. **Radi na taskovima** - Claimuj taskove i završi ih
5. **Timski rad** - Pozovi druge članove da se pridruže sobi pomoću unique koda

## Autori

Svaki task prikazuje kompletnu istoriju:
- **Kreirao**: Korisnik koji je napravio task
- **Claimovao**: Korisnik koji preuzeo task za rad
- **Završio**: Korisnik koji je markirao task kao završen
