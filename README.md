# real-sfx sound libraries

Sound packs downloaded by the real-sfx skill (scripts/get_sounds.py). Each folder has its licence:
Kenney packs (CC0), react-sounds ambience (MIT), cluesurf/wavebase transitions and nature foley (public domain).

## Install the skill in Claude Code

    git clone --depth 1 -b real-sfx-sounds https://github.com/ula0740-ux/wavebase /tmp/rsfx
    mkdir -p ~/.claude/skills && cp -r /tmp/rsfx/skill/real-sfx ~/.claude/skills/
    cd ~/.claude/skills/real-sfx && python scripts/get_sounds.py && python scripts/build_index.py
