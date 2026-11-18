"""Сохранение, загрузка, импорт и экспорт профилей."""

import gzip
import json
import os
import tempfile

from .i18n import tr

VALID_EVENT_TYPES = {
    "mouse_move", "mouse_click", "mouse_scroll",
    "key_down", "key_up", "hotkey_combo", "modifier_combo",
}


def validate_events(events):
    if not isinstance(events, list):
        raise ValueError(tr("import_bad_format"))
    normalized = []
    previous_time = 0.0
    for event in events:
        if not isinstance(event, dict):
            raise ValueError(tr("import_bad_format"))
        if isinstance(event.get("time"), bool) or not isinstance(event.get("time"), (int, float)) or event["time"] < 0:
            raise ValueError(tr("import_bad_format"))
        if event["type"] not in VALID_EVENT_TYPES or not isinstance(event.get("data"), dict):
            raise ValueError(tr("import_bad_format"))
        if event["time"] < previous_time:
            raise ValueError(tr("import_bad_format"))
        previous_time = float(event["time"])
        normalized.append(event)
    return normalized


def _validated_profile(data, default_name_factory, pid):
    if not isinstance(data, dict):
        return {"name": default_name_factory(pid), "events": validate_events(data)}
    name = data.get("name", default_name_factory(pid))
    if not isinstance(name, str) or not name.strip():
        name = default_name_factory(pid)
    return {"name": name, "events": validate_events(data.get("events", []))}


def save_profile(profile_dir, pid, profile_data, logger):
    fname = os.path.join(profile_dir, f"profile_{pid}.json.gz")
    logger.debug(f"[PROFILES] Saving profile {pid} to {fname}")
    temp_name = None
    try:
        payload = json.dumps(profile_data, ensure_ascii=False)
        fd, temp_name = tempfile.mkstemp(prefix=f"profile_{pid}_", suffix=".tmp", dir=profile_dir)
        os.close(fd)
        with gzip.open(temp_name, "wt", encoding="utf-8") as f:
            f.write(payload)
        os.replace(temp_name, fname)
        logger.info(f"Saved compressed profile {pid}")
    except Exception as e:
        if temp_name:
            try:
                os.remove(temp_name)
            except OSError:
                pass
        logger.error(f"Save error: {e}")


def delete_profile(profile_dir, pid, logger):
    """Удаляет сохранённый профиль и старый несжатый вариант."""
    removed = False
    for suffix in (".json.gz", ".json"):
        path = os.path.join(profile_dir, f"profile_{pid}{suffix}")
        try:
            if os.path.exists(path):
                os.remove(path)
                removed = True
                logger.info(f"Deleted profile file {path}")
        except OSError as exc:
            logger.error(f"Delete error for profile {pid}: {exc}")
    return removed


def load_all_profiles(profile_dir, default_name_factory, logger):
    logger.debug(f"[PROFILES] Loading all profiles from {profile_dir}")
    profiles = {}
    for i in range(1, 11):
        fname_gz = os.path.join(profile_dir, f"profile_{i}.json.gz")
        fname_json = os.path.join(profile_dir, f"profile_{i}.json")
        fname = fname_gz if os.path.exists(fname_gz) else (fname_json if os.path.exists(fname_json) else None)
        if fname:
            try:
                opener = gzip.open if fname.endswith(".gz") else open
                with opener(fname, "rt", encoding="utf-8") as f:
                    profiles[i] = _validated_profile(json.load(f), default_name_factory, i)
            except Exception as e:
                logger.error(f"Load error profile {i}: {e}")
        profiles.setdefault(i, {"name": default_name_factory(i), "events": []})
    return profiles


def export_profile(path, profile_data, logger):
    logger.debug(f"[PROFILES] Exporting profile to {path}")
    try:
        profile_data = {"name": profile_data.get("name", ""), "events": validate_events(profile_data.get("events", []))}
        payload = json.dumps(profile_data, ensure_ascii=False, indent=2)
        if path.lower().endswith(".gz"):
            with gzip.open(path, "wt", encoding="utf-8") as f:
                f.write(payload)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(payload)
        return True
    except Exception as e:
        logger.error(f"Export error: {e}")
        return False


def read_imported_profile(path, logger):
    logger.debug(f"[PROFILES] Reading imported profile from {path}")
    try:
        opener = gzip.open if path.lower().endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Import read error: {e}")
        raise
    if isinstance(data, dict):
        new_name = data.get("name")
        if not isinstance(new_name, str) or not new_name.strip():
            raise ValueError(tr("import_bad_format"))
        return new_name, validate_events(data.get("events"))
    if isinstance(data, list):
        return None, validate_events(data)
    raise ValueError(tr("import_bad_format"))


def resolve_import_name(new_name, path, pid, current_profiles, default_name_factory):
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
