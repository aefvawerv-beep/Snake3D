from game_window import GameWindow
from scenes import load_all_levels


if __name__ == "__main__":
    
    try:
        print("[SYSTEM] Sprawdzanie spójności plików poziomów...")
        load_all_levels()
        print("[SYSTEM] Pliki JSON poprawne. Uruchamianie gry...")
    except Exception as e:
        print(e)
        import sys
        sys.exit(1)
    
    game_window = GameWindow()
    game_window.run()
