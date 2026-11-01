"""Download the real-sfx sound libraries and uisfx into a writable home folder, and write a config there.

The skill package itself carries no audio (skill uploads must stay small). Run once per machine or session:

    python scripts/get_sounds.py            # -> ~/.real-sfx (or REAL_SFX_HOME)
    python scripts/get_sounds.py --force    # download again

Afterwards every script finds ~/.real-sfx/config.json automatically (common.config_path), and the index lives there too.
Sources: Kenney packs (CC0), react-sounds ambience (MIT), cluesurf/wavebase transitions and nature foley
(public domain), hosted on the branch below; uisfx (CC0) from npm.
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO = "https://github.com/ula0740-ux/wavebase"
BRANCH = "real-sfx-sounds"
ZIP_URL = f"{REPO}/archive/refs/heads/{BRANCH}.zip"

LIBS = [
    ("kenney-impact", "kenney-impact-sounds", "main"),
    ("kenney-rpg-foley", "kenney-rpg-audio", "main"),
    ("kenney-casino", "kenney-casino-audio", "main"),
    ("react-sounds-ambience", "react-sounds-ambience", "main"),
    ("wavebase-transitions", "wavebase-transitions", "main"),
    ("wavebase-nature", "wavebase-nature", "main"),
    ("kenney-interface", "kenney-interface-sounds", "extra"),
    ("kenney-ui-audio", "kenney-ui-audio", "extra"),
]


def home():
    return Path(os.environ.get("REAL_SFX_HOME") or (Path.home() / ".real-sfx")).expanduser()


def fetch_libraries(dest: Path):
    tmp = dest.parent / (dest.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    git = shutil.which("git")
    if git:
        print(f"cloning {REPO} ({BRANCH}) ...", flush=True)
        env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1")
        r = subprocess.run([git, "clone", "--depth", "1", "--single-branch", "-b", BRANCH, REPO, str(tmp)], env=env)
        if r.returncode == 0 and (tmp / "libraries").is_dir():
            shutil.rmtree(dest, ignore_errors=True)
            shutil.move(str(tmp / "libraries"), str(dest))
            shutil.rmtree(tmp, ignore_errors=True)
            return
        print("git clone failed, trying the ZIP download ...", flush=True)
    print(f"downloading {ZIP_URL} ...", flush=True)
    data = urllib.request.urlopen(ZIP_URL, timeout=300).read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(tmp)
    inner = next(tmp.glob("*/libraries"))
    shutil.rmtree(dest, ignore_errors=True)
    shutil.move(str(inner), str(dest))
    shutil.rmtree(tmp, ignore_errors=True)


def install_uisfx(vendor: Path):
    vendor.mkdir(parents=True, exist_ok=True)
    if not (vendor / "package.json").exists():
        (vendor / "package.json").write_text('{"name":"real-sfx-vendor","private":true,"version":"1.0.0"}',
                                             encoding="utf-8")
    npm = shutil.which("npm")
    if not npm:
        print("npm not found: uisfx UI cues skipped (install Node.js, then run again). Libraries still work.")
        return False
    print("installing uisfx (CC0 UI sounds) ...", flush=True)
    subprocess.check_call([npm, "install", "uisfx", "--prefix", str(vendor), "--no-audit", "--no-fund"],
                          shell=(os.name == "nt"))
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="download again even if present")
    ap.add_argument("--no-uisfx", action="store_true")
    a = ap.parse_args()

    h = home()
    h.mkdir(parents=True, exist_ok=True)
    libs = h / "libraries"
    if a.force or not libs.is_dir() or not any(libs.iterdir()):
        fetch_libraries(libs)
    else:
        print(f"libraries already in {libs} (use --force to refresh)")

    ui = h / "vendor" / "node_modules" / "uisfx"
    if not a.no_uisfx and (a.force or not ui.is_dir()):
        install_uisfx(h / "vendor")

    cfg_p = h / "config.json"
    cfg = json.loads(cfg_p.read_text(encoding="utf-8")) if cfg_p.exists() else {}
    have = {l["name"]: l for l in cfg.get("libraries", [])}
    for name, folder, tier in LIBS:
        if (libs / folder).is_dir():
            have[name] = {"name": name, "path": str(libs / folder), "tier": tier}
    cfg["libraries"] = list(have.values())
    cfg["uisfx"] = {"path": str(ui), "default_pack": (cfg.get("uisfx") or {}).get("default_pack", "studio")}
    cfg.setdefault("skip_dir_names", ["_mister horse previews"])
    cfg["index_path"] = str(h / "library_index.json")
    cfg_p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"config written: {cfg_p}  ({len(cfg['libraries'])} libraries)")
    print("next: python scripts/build_index.py")


if __name__ == "__main__":
    sys.exit(main())
