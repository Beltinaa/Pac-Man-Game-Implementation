Background music.

Each theme has its own track, named in theme.py:

    classic.ogg      the classic theme
    spiderman.ogg    the web-slinger theme

Switching THEME_NAME in config.py switches the music with it. If a theme's
track is missing, MUSIC_FILE in config.py is tried next, and after that any
audio file in this folder -- so the game still plays something rather than
falling silent.

.ogg is the safest format: pygame reads .ogg and .wav on every platform,
while .mp3 support depends on how SDL_mixer was built.

If no audio file is here at all the game still runs; it just starts silent
and the HUD sound button shows as muted.

Use audio you have the right to distribute with the project, and consider
keeping large audio files out of the committed repo (.gitignore) rather than
pushing them.
