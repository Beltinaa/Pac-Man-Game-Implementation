"""Background music, and the on/off switch behind the HUD sound button.

Everything here degrades to silence rather than crashing. Any of these
leaves `available` False, the game running exactly as before, and the HUD
button showing the muted icon:

  * pygame built without SDL_mixer, so there is no `pygame.mixer` at all.
    Touching the attribute then raises NotImplementedError rather than
    ImportError, which is why every access below goes through `_mixer()`
    instead of naming `pygame.mixer` directly.
  * no audio device -- common over SSH, in CI, or on a machine with no
    sound card.
  * a missing or unreadable music file.

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


def _mixer():
    """The mixer module, or None when this pygame build has no audio.

    A pygame compiled without SDL_mixer keeps a stub in place of the module
    that raises NotImplementedError on attribute access, so this cannot be a
    plain `import pygame.mixer` or a hasattr check -- it has to catch
    whatever comes out of touching the name.
    """
    try:
        return pygame.mixer
    except Exception:
        return None


def init():
    """Start the mixer and load the music track. Safe to call once at
    startup; failures are recorded, not raised."""
    global available, _load_error

    mixer = _mixer()
    if mixer is None:
        _load_error = "this pygame build has no mixer module"
        return

    try:
        mixer.init()
    except Exception as exc:
        _load_error = "no audio device (%s)" % exc
        return

    if not os.path.exists(MUSIC_FILE):
        _load_error = "no music file at %s" % MUSIC_FILE
        return

    try:
        mixer.music.load(MUSIC_FILE)
        mixer.music.set_volume(MUSIC_VOLUME)
    except Exception as exc:
        _load_error = "could not load %s (%s)" % (MUSIC_FILE, exc)
        return

    available = True
    if state.sound_enabled:
        start()


def start():
    """Play on a loop from the beginning."""
    if available:
        _mixer().music.play(-1)


def toggle():
    """Flip sound on/off and start or stop the music to match.

    The flag flips even when no music is loaded, so the HUD button still
    responds and the preference is remembered if audio appears later.
    """
    state.sound_enabled = not state.sound_enabled
    if not available:
        return

    music = _mixer().music
    if state.sound_enabled:
        music.unpause()
        if not music.get_busy():
            start()
    else:
        music.pause()


def status_text():
    """Why audio is silent, for the instructions screen. Empty when fine."""
    return "" if available else (_load_error or "audio not initialised")