import os
import json
import hashlib

SAVE_FILE = "progress.dat"
# Sekretna sól uniemożliwiająca łatwe podrobienie hasha przez użytkownika lub AI
SECRET_SALT = "IDK_STH_FEOFJEOJGOEJGOEJGOJEG"

def calculate_hash(data_str: str) -> str:
    """Oblicza unikalny hash SHA-256 dla danych połączonych z sekretną solą."""
    combined = data_str + SECRET_SALT
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def get_max_unlocked_level() -> int:
    """Odczytuje plik zapisu, weryfikuje jego autentyczność i zwraca najwyższy odblokowany poziom.
    W przypadku wykrycia oszustwa (niepoprawny hash) resetuje postęp do poziomu 1.
    """
    # Jeśli plik nie istnieje, tworzymy nowy z poziomem 1
    if not os.path.exists(SAVE_FILE):
        save_progress(1)
        return 1

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            save_data = json.load(f)
        
        payload_str = save_data.get("payload", "")
        saved_hash = save_data.get("hash", "")
        
        # WERYFIKACJA ANTI-CHEAT: Obliczamy hash ponownie na podstawie wczytanych danych
        calculated_hash = calculate_hash(payload_str)
        
        if calculated_hash != saved_hash:
            print("\n" + "!"*60)
            print("[ANTI-CHEAT] WYKRYTO MANIPULACJĘ W PLIKU ZAPISU!")
            print("Suma kontrolna się nie zgadza. Resetowanie postępu do poziomu 1.")
            print("!"*60 + "\n")
            reset_progress()
            return 1
            
        # Jeśli hash jest poprawny, dekodujemy właściwe dane
        data = json.loads(payload_str)
        return int(data.get("max_level", 1))

    except Exception as e:
        print(f"[ERROR] Błąd odczytu pliku zapisu ({e}). Resetowanie do domyślnych.")
        reset_progress()
        return 1

def save_progress(level_id: int):
    """Zapisuje najwyższy odblokowany poziom do pliku wraz z bezpieczną sumą kontrolną."""
    data = {"max_level": level_id}
    payload_str = json.dumps(data)
    
    # Generujemy cyfrowy odcisk palca (hash) dla tych danych
    current_hash = calculate_hash(payload_str)
    
    save_data = {
        "payload": payload_str,
        "hash": current_hash
    }
    
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=4)

def reset_progress():
    """Wymusza całkowity reset postępu gry do poziomu 1."""
    save_progress(1)
    print("[INFO] Postęp gry został pomyślnie zresetowany.")