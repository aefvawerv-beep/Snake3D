import os
import json

def generate_all_levels():
    levels_dir = "levels"
    if not os.path.exists(levels_dir):
        os.makedirs(levels_dir)

    levels_data = []

    # --- LEVEL 1 (Brak przeszkód) ---
    levels_data.append({
        "id": 1, "name": "LEVEL 1", "grid_size": 10, "foods_to_win": 3,
        "snake_start": [{"x": 5, "y": 5, "z": 5}, {"x": 5, "y": 5, "z": 6}, {"x": 5, "y": 5, "z": 7}],
        "food_start": {"x": 5, "y": 5, "z": 2}, "obstacles": []
    })

    # --- LEVEL 2 (Wstępny: Tylko 1 przeszkoda, schowana bezpiecznie w rogu, z dala od jedzenia) ---
    levels_data.append({
        "id": 2, "name": "LEVEL 2", "grid_size": 10, "foods_to_win": 3,
        "snake_start": [{"x": 5, "y": 5, "z": 5}, {"x": 5, "y": 5, "z": 6}, {"x": 5, "y": 5, "z": 7}],
        "food_start": {"x": 5, "y": 5, "z": 2},
        "obstacles": [{"x": 1, "y": 1, "z": 1}] 
    })

    # --- LEVEL 3 (Wstępny: 3 rozproszone, niegroźne kostki na obrzeżach mapy) ---
    levels_data.append({
        "id": 3, "name": "LEVEL 3", "grid_size": 10, "foods_to_win": 4,
        "snake_start": [{"x": 5, "y": 5, "z": 5}, {"x": 5, "y": 5, "z": 6}, {"x": 5, "y": 5, "z": 7}],
        "food_start": {"x": 3, "y": 3, "z": 3},
        "obstacles": [
            {"x": 2, "y": 2, "z": 2}, 
            {"x": 8, "y": 2, "z": 8}, 
            {"x": 2, "y": 8, "z": 8}
        ]
    })

    # --- LEVEL 4 (Mała prosta ścianka z 3 bloczków w przestrzeni) ---
    levels_data.append({
        "id": 4, "name": "LEVEL 4", "grid_size": 11, "foods_to_win": 4,
        "snake_start": [{"x": 5, "y": 5, "z": 5}, {"x": 5, "y": 5, "z": 6}, {"x": 5, "y": 5, "z": 7}],
        "food_start": {"x": 5, "y": 5, "z": 2},
        "obstacles": [
            {"x": 5, "y": 3, "z": 3}, {"x": 5, "y": 4, "z": 3}, {"x": 5, "y": 5, "z": 3}
        ]
    })

    # --- LEVEL 5 (Środkowa bariera w kształcie krzyża) ---
    levels_data.append({
        "id": 5, "name": "LEVEL 5", "grid_size": 12, "foods_to_win": 5,
        "snake_start": [{"x": 6, "y": 6, "z": 6}, {"x": 6, "y": 6, "z": 7}, {"x": 6, "y": 6, "z": 8}],
        "food_start": {"x": 6, "y": 6, "z": 2},
        "obstacles": [
            {"x": 4, "y": 6, "z": 4}, {"x": 5, "y": 6, "z": 4}, {"x": 6, "y": 6, "z": 4}, {"x": 7, "y": 6, "z": 4}, {"x": 8, "y": 6, "z": 4},
            {"x": 6, "y": 4, "z": 4}, {"x": 6, "y": 5, "z": 4}, {"x": 6, "y": 7, "z": 4}, {"x": 6, "y": 8, "z": 4}
        ]
    })

    # --- LEVEL 6 (4 pionowe filary strukturalne) ---
    lvl6_obstacles = []
    for y in range(2, 11):
        lvl6_obstacles.append({"x": 3, "y": y, "z": 3})
        lvl6_obstacles.append({"x": 8, "y": y, "z": 3})
        lvl6_obstacles.append({"x": 3, "y": y, "z": 8})
        lvl6_obstacles.append({"x": 8, "y": y, "z": 8})

    levels_data.append({
        "id": 6, "name": "LEVEL 6", "grid_size": 12, "foods_to_win": 5,
        "snake_start": [{"x": 6, "y": 5, "z": 6}, {"x": 6, "y": 5, "z": 7}, {"x": 6, "y": 5, "z": 8}],
        "food_start": {"x": 3, "y": 5, "z": 4},
        "obstacles": lvl6_obstacles
    })

    # --- LEVEL 7 (Platformy dzielące przestrzeń góra/dół) ---
    lvl7_obstacles = []
    for x in range(3, 10):
        for z in range(3, 10):
            if x != 6 or z != 6: 
                lvl7_obstacles.append({"x": x, "y": 4, "z": z})
                lvl7_obstacles.append({"x": x, "y": 8, "z": z})

    levels_data.append({
        "id": 7, "name": "LEVEL 7", "grid_size": 13, "foods_to_win": 6,
        "snake_start": [{"x": 6, "y": 6, "z": 6}, {"x": 6, "y": 6, "z": 7}, {"x": 6, "y": 6, "z": 8}],
        "food_start": {"x": 3, "y": 2, "z": 3},
        "obstacles": lvl7_obstacles
    })

    # --- LEVEL 8 (KLATKA: Pierwsze jedzenie zamknięte w narożniku przeszkodami) ---
    levels_data.append({
        "id": 8, "name": "LEVEL 8", "grid_size": 12, "foods_to_win": 6,
        "snake_start": [{"x": 6, "y": 6, "z": 6}, {"x": 6, "y": 6, "z": 7}, {"x": 6, "y": 6, "z": 8}],
        "food_start": {"x": 1, "y": 1, "z": 1}, 
        "obstacles": [
            {"x": 1, "y": 1, "z": 2}, 
            {"x": 1, "y": 2, "z": 1},
            {"x": 2, "y": 1, "z": 1}
        ]
    })

    # --- LEVEL 9 (Szachownica najeżona pojedynczymi klockami) ---
    lvl8_obstacles = []
    for x in range(2, 13, 2):
        for y in range(2, 13, 2):
            for z in range(2, 13, 2):
                if not (5 <= x <= 9 and 5 <= y <= 9 and 5 <= z <= 9):
                    lvl8_obstacles.append({"x": x, "y": y, "z": z})

    levels_data.append({
        "id": 9, "name": "LEVEL 9", "grid_size": 14, "foods_to_win": 7,
        "snake_start": [{"x": 7, "y": 7, "z": 7}, {"x": 7, "y": 7, "z": 8}, {"x": 7, "y": 7, "z": 9}],
        "food_start": {"x": 1, "y": 1, "z": 1},
        "obstacles": lvl8_obstacles
    })

    # --- LEVEL 10 (Zaawansowany labirynt 3D) ---
    lvl10_obstacles = []
    for i in range(1, 13):
        if i % 2 == 0:
            for j in range(0, 10):
                lvl10_obstacles.append({"x": i, "y": j, "z": 4})
                lvl10_obstacles.append({"x": j, "y": i, "z": 8})
        else:
            for j in range(4, 13):
                lvl10_obstacles.append({"x": j, "y": i, "z": 6})

    lvl10_obstacles = [o for o in lvl10_obstacles if not (5 <= o["x"] <= 9 and 5 <= o["y"] <= 9 and 5 <= o["z"] <= 9)]

    levels_data.append({
        "id": 10, "name": "LEVEL 10", "grid_size": 14, "foods_to_win": 8,
        "snake_start": [{"x": 7, "y": 7, "z": 7}, {"x": 7, "y": 7, "z": 8}, {"x": 7, "y": 7, "z": 9}],
        "food_start": {"x": 13, "y": 13, "z": 13},
        "obstacles": lvl10_obstacles
    })

    # Zapisywanie (z automatycznym nadpisywaniem dla re-balansu)
    for lvl in levels_data:
        file_path = os.path.join(levels_dir, f"level{lvl['id']}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(lvl, f, indent=4, ensure_ascii=False)
        print(f"Zaktualizowano balans: {lvl['name']}")

if __name__ == "__main__":
    generate_all_levels()
    print("\n[SUKCES] Poziomy 1-10 zostały wygenerowane z nowym balansem trudności!")