background music here as `music.ogg` (path set by MUSIC_FILE in
config.py). .ogg is safest -- pygame reads .ogg and .wav on every platform,
while .mp3 support depends on the SDL_mixer build.

If this file is absent the game still runs; it just starts silent and the
HUD sound button shows as muted.

