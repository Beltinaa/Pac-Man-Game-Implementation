import json

from config import HIGHSCORES_FILE, MAX_HIGHSCORES, NAME_INPUT_MAX_LEN


def load_highscores():
    try:
        with open(HIGHSCORES_FILE, 'r') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    entries = []
    for entry in data:
        if isinstance(entry, dict) and 'name' in entry and 'score' in entry:
            try:
                score = int(entry['score'])
            except (TypeError, ValueError):
                continue
            if score < 0:
                continue
            entries.append({'name': str(entry['name']), 'score': score})
    entries.sort(key=lambda e: e['score'], reverse=True)
    return entries[:MAX_HIGHSCORES]


def save_highscore(name, score_value):
    if score_value < 0:
        return load_highscores()
    name = (name.strip() or 'PLAYER')[:NAME_INPUT_MAX_LEN]
    entries = load_highscores()
    entries.append({'name': name, 'score': score_value})
    entries.sort(key=lambda e: e['score'], reverse=True)
    entries = entries[:MAX_HIGHSCORES]
    try:
        with open(HIGHSCORES_FILE, 'w') as f:
            json.dump(entries, f, indent=2)
    except OSError:
        pass
    return entries
