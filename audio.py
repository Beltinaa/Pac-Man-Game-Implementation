"""Background music, and the on/off switch behind the HUD sound button.

Everything here degrades to silence rather than crashing: if the mixer will
not initialise (no audio device -- common over SSH, in CI, or on a machine
with no sound card) or the music file is missing, `available` stays False,
the game runs exactly as before, and the HUD button shows the muted icon.

Supply your own audio file at the path in config.MUSIC_FILE. pygame's mixer
reads .ogg and .wav everywhere; .mp3 support depends on the SDL_mixer build,
so .ogg is the safe choice.
"""

import os

import pygame

from config import MUSIC_FILE, MUSIC_VOLUME
import state

available = False
_load_error = None


def init():
    """Start the mixer and load the music track. Safe to call once at
    startup; failures are recorded, not raised."""
    global available, _load_error

    try:
        pygame.mixer.init()
    except pygame.error as exc:
        _load_error = "no audio device (%s)" % exc
        return

    if not os.path.exists(MUSIC_FILE):
        _load_error = "no music file at %s" % MUSIC_FILE
        return

    try:
        pygame.mixer.music.load(MUSIC_FILE)
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
    except pygame.error as exc:
        _load_error = "could not load %s (%s)" % (MUSIC_FILE, exc)
        return

    available = True
    if state.sound_enabled:
        start()


def start():
    """Play on a loop from the beginning."""
    if available:
        pygame.mixer.music.play(-1)


def toggle():
    """Flip sound on/off and start or stop the music to match.

    The flag flips even when no music is loaded, so the HUD button still
    responds and the preference is remembered if audio appears later.
    """
    state.sound_enabled = not state.sound_enabled
    if not available:
        return
    if state.sound_enabled:
        pygame.mixer.music.unpause()
        if not pygame.mixer.music.get_busy():
            start()
    else:
        pygame.mixer.music.pause()


def status_text():
    """Why audio is silent, for the instructions screen. Empty when fine."""
    return "" if available else (_load_error or "audio not initialised")
