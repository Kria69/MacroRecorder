"""Сохранение, загрузка, импорт и экспорт профилей."""

import os
import json
import gzip

from .i18n import tr


def save_profile(profile_dir, pid, profile_data, logger):
    """Сохраняет профиль в сжатый .json.gz."""
    fname = os.path.join(profile_dir, f"profile_{pid}.json.gz")
    logger.debug(f"[PROFILES] Saving profile {pid} to {fname}")
    try:
        payload = json.dumps(profile_data, ensure_ascii=False)
        with gzip.open(fname, 'wt', encoding='utf-8') as f:
            f.write(payload)
        logger.info(f"Saved compressed profile {pid}")
    except Exception as e:
        logger.error(f"Save error: {e}")


def load_all_profiles(profile_dir, default_name_factory, logger):
    """Загружает профили 1..10 из .json.gz / .json."""
    logger.debug(f"[PROFILES] Loading all profiles from {profile_dir}")
    profiles = {}
    for i in range(1, 11):
        fname_gz = os.path.join(profile_dir, f"profile_{i}.json.gz")
        fname_json = os.path.join(profile_dir, f"profile_{i}.json")
        fname = fname_gz if os.path.exists(fname_gz) else (fname_json if os.path.exists(fname_json) else None)
        if fname:
            logger.debug(f"[PROFILES] Found file for profile {i}: {os.path.basename(fname)}")
            try:
                if fname.endswith('.gz'):
                    with gzip.open(fname, 'rt', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    with open(fname, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                if isinstance(data, dict):
                    profiles[i] = data
                    profiles[i].setdefault("name", default_name_factory(i))
                    profiles[i].setdefault("events", [])
                else:
                    profiles[i] = {"name": default_name_factory(i), "events": data}
            except Exception as e:
                logger.error(f"Load error profile {i}: {e}")
        if i not in profiles:
            profiles[i] = {"name": default_name_factory(i), "events": []}
    return profiles


def export_profile(path, profile_data, logger):
    """Экспортирует профиль в файл (.json или .json.gz по расширению)."""
    logger.debug(f"[PROFILES] Exporting profile to {path}")
    try:
        payload = json.dumps(profile_data, ensure_ascii=False, indent=2)
        if path.lower().endswith(".gz"):
            with gzip.open(path, 'wt', encoding='utf-8') as f:
                f.write(payload)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(payload)
        return True
    except Exception as e:
        logger.error(f"Export error: {e}")
        return False


def read_imported_profile(path, logger):
    """
    Читает файл профиля для импорта.
    Возвращает (new_name_or_None, events_list) либо выбрасывает ValueError
    при неверном формате.
    """
    logger.debug(f"[PROFILES] Reading imported profile from {path}")
    try:
        if path.lower().endswith('.gz'):
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    except Exception as e:
        logger.error(f"Import read error: {e}")
        raise

    if isinstance(data, dict):
        new_name = data.get("name")
        new_events = data.get("events")
        if not isinstance(new_name, str) or not isinstance(new_events, list):
            raise ValueError(tr("import_bad_format"))
        return new_name, new_events
    elif isinstance(data, list):
        return None, data
    else:
        raise ValueError(tr("import_bad_format"))


def resolve_import_name(new_name, path, pid, current_profiles, default_name_factory):
    """Формирует уникальное имя для импортируемого профиля."""
    if not new_name:
        base = os.path.basename(path)
        if base.lower().endswith(".json.gz"):
            base = base[:-8]
        elif base.lower().endswith(".json"):
            base = base[:-5]
        new_name = base or default_name_factory(pid)

    for other_pid, other_data in current_profiles.items():
        if other_pid != pid and other_data["name"] == new_name:
            new_name = f"{new_name} ({pid})"
            break

    return new_name