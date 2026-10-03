"""Safe file writes: a crash (OOM kill, reboot...) never leaves a half-written file.

Each write goes to a temporary file in the same folder, is flushed to disk,
then atomically replaces the target with os.replace(). Readers always see
either the old content or the new one, never a truncated file.
"""
import datetime
import json
import logging
import os
import shutil
import tempfile

logger = logging.getLogger(__name__)


def atomic_write_text(path, text, encoding=None, backup=False):
    """Atomically replace `path` with `text`.

    `encoding=None` keeps the platform default, like a bare open(path, "w").
    With `backup=True`, the previous version is kept as `path + ".bak"`.
    """
    folder = os.path.dirname(path) or "."
    os.makedirs(folder, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=folder, prefix="." + os.path.basename(path) + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())

        # mkstemp creates the file as 0600: keep the permissions of the file we replace
        try:
            os.chmod(tmp_path, os.stat(path).st_mode)
        except FileNotFoundError:
            umask = os.umask(0)
            os.umask(umask)
            os.chmod(tmp_path, 0o666 & ~umask)

        if backup and os.path.exists(path):
            shutil.copy2(path, path + ".bak")

        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise

    # Make the rename itself durable (not supported on Windows)
    try:
        dir_fd = os.open(folder, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    except OSError:
        pass
    finally:
        os.close(dir_fd)


def remove_stale_temp_files(folder):
    """Delete temporary files left behind by a write interrupted by a crash.

    Only call it at startup, when no write can be in progress.
    """
    try:
        names = os.listdir(folder)
    except FileNotFoundError:
        return
    for name in names:
        if name.startswith(".") and name.endswith(".tmp"):
            try:
                os.unlink(os.path.join(folder, name))
                logger.info(f"Fichier temporaire orphelin supprimé : {os.path.join(folder, name)}")
            except OSError:
                pass


def atomic_write_json(path, data, backup=False, **json_kwargs):
    atomic_write_text(path, json.dumps(data, **json_kwargs), encoding="utf-8", backup=backup)


def load_json_safely(path, default):
    """Load a JSON file without ever losing data.

    - missing file: fall back to the `.bak` copy if there is one, else `default`
    - corrupted file: move it aside as `<path>.corrupt-<date>` (never overwritten),
      then fall back to the `.bak` copy, else `default`
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if not os.path.exists(path + ".bak"):
            return default
        logger.warning(f"{path} introuvable, restauration depuis {path}.bak")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        corrupt_path = f"{path}.corrupt-{datetime.datetime.now():%Y%m%d-%H%M%S}"
        os.replace(path, corrupt_path)
        logger.critical(f"{path} est corrompu ({e}) : mis de côté dans {corrupt_path}")

    try:
        with open(path + ".bak", "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.warning(f"{path} restauré depuis {path}.bak")
        return data
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.critical(f"Pas de sauvegarde utilisable pour {path} ({e}), démarrage à vide")
        return default
