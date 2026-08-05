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

No music plays on the main menu: a character has not been picked there yet,
so there is no theme and therefore no soundtrack to choose. play_theme() is
called once the player picks one.

The track is chosen in three steps, first hit wins:

  1. the active theme's own music (Theme.music), so picking a character
     picks its soundtrack with it;
  2. config.MUSIC_FILE, for overriding both themes at once;
  3. any audio file sitting in that folder, so dropping a track into
     assets/sounds/ works whatever it happens to be called.

Supply your own audio file at the path in config.MUSIC_FILE. pygame's mixer
reads .ogg and .wav everywhere; .mp3 support depends on the SDL_mixer build,
so .ogg is the safe choice.
"""

import os

import pygame

from config import MUSIC_FILE, MUSIC_VOLUME
import state
import theme as theme_module

available = False
_load_error = None
track = None


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


def _resolve_track():
    """The music file to play: the theme's own track, else
    config.MUSIC_FILE, else the first audio file in that folder. The last
    step saves having to rename a downloaded track, which is otherwise a
    silent and near-invisible failure."""
    if theme_module.ACTIVE is not None:
        themed = theme_module.image_path(theme_module.ACTIVE.music)
        if themed is not None:
            return themed

    if os.path.exists(MUSIC_FILE):
        return MUSIC_FILE

    folder = os.path.dirname(MUSIC_FILE) or "."
    if not os.path.isdir(folder):
        return None
    playable = sorted(
        name for name in os.listdir(folder)
        if name.lower().endswith((".ogg", ".wav", ".mp3", ".flac"))
    )
    if not playable:
        return None
    return os.path.join(folder, playable[0])


def init():
    """Start the mixer and load the music track. Safe to call once at
    startup; failures are reported on stdout and recorded, never raised."""
    global available, _load_error, track

    mixer = _mixer()
    if mixer is None:
        _load_error = "this pygame build has no mixer module"
        return _report()

    try:
        mixer.init()
    except Exception as exc:
        _load_error = "no audio device (%s)" % exc
        return _report()

    if theme_module.ACTIVE is None:
        # Menu: mixer is up and usable, but there is no theme yet, so there
        # is nothing to load. play_theme() finishes the job later.
        available = True
        return

    track = _resolve_track()
    if track is None:
        _load_error = "no audio file in %s" % (os.path.dirname(MUSIC_FILE) or ".")
        return _report()

    try:
        mixer.music.load(track)
        mixer.music.set_volume(MUSIC_VOLUME)
    except Exception as exc:
        _load_error = "could not load %s (%s)" % (track, exc)
        return _report()

    available = True
    print("[audio] playing %s" % track)
    if state.sound_enabled:
        start()


def play_theme():
    """Load and start the active theme's music. Called when a character is
    picked, so the menu itself stays silent."""
    if _mixer() is None:
        return
    init()


def stop():
    """Silence the music, e.g. on returning to the main menu."""
    if available and _mixer() is not None:
        _mixer().music.stop()


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


def _report():
    """Say once why there will be no sound, so a silent game is not a
    mystery. The HUD button shows the state; this explains it."""
    if not available:
        print("[audio] no music: %s" % status_text())


def status_text():
    """Why audio is silent, for the instructions screen. Empty when fine."""
    return "" if available else (_load_error or "audio not initialised")