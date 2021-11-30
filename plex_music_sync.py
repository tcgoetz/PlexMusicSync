#!/usr/bin/env python3

"""
A script that synchronizes playlists, music file ratings and tags between a local directory and a Plex server.
"""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"
__version__ = "0.0.1"


import sys
import os
import logging
import argparse
from plexapi.myplex import MyPlexAccount
from plexapi.exceptions import NotFound
import mutagen
import m3u8


fatal = False
sync_count = 0
clear_count = 0


logging.basicConfig(filename='sync.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


def _log_fatal(*args):
    logger.fatal(*args)
    root_logger.fatal(*args)
    if fatal:
        exit()


def login(hostname, username, password):
    """Log in to a Plex server."""
    account = MyPlexAccount(username, password)
    plex = account.resource(hostname).connect()
    return plex


def _normalize_name(name):
    # Plex drops prefixes like 'The' and 'A ' from the beginning of song titles, album names and band names some times.
    for prefix in ['the ', 'a ', 'el ', 'der ', '(']:
        if name.lower().startswith(prefix):
            return name[len(prefix):].strip()
    return name


def _find_media(music, artist, album, title):
    try:
        albums = []
        plex_songs = music.searchTracks(title=_normalize_name(title))
        for plex_song in plex_songs:
            plex_song_album = plex_song.album()
            albums.append(plex_song_album.title)
            if plex_song_album.title == album or plex_song_album.title == _normalize_name(album):
                plex_artist = plex_song.artist()
                plex_album = plex_song_album
                root_logger.debug("Found song '%s' and '%s' '%s' on Plex!", plex_song.title, plex_artist.title, plex_album.title)
                return plex_song, plex_album, plex_artist
        logger.error("Song '%s' album not matched '%s' not in '%s' not found on Plex!", title, album, albums)
    except NotFound:    
        logger.error("Song '%s' '%s' '%s' not found on Plex!", artist, album, title)
    return None, None, None


def _genre_names(obj):
    return [genre.tag for genre in obj.genres]


def _mood_names(obj):
    return [genre.tag for genre in obj.moods]


def _sync_song(plex_song, title, genre, rating, explicit):
    if rating is not None:
        rounded_rating = float(round(rating, 1))
        if rounded_rating != plex_song.userRating:
            root_logger.info("Updating rating for song %s from %s to %f", title, plex_song.userRating, rounded_rating)
            plex_song.rate(rounded_rating)
    # Since Plex doesn't have a per song genre, the genre is sunk to mood
    moods = _mood_names(plex_song)
    if genre is not None and genre not in moods:
        root_logger.info("Updating mood for song %s from %s to %s", title, moods, genre)
        plex_song.addMood(genre)
    if explicit:
        root_logger.info("Updating mood for song %s to include Explicit", title)
        plex_song.addMood('Explicit')


def _sync_artist(plex_artist, genre):
    if genre is not None:
        genre_names = _genre_names(plex_artist)
        if genre not in genre_names:
            root_logger.info("Updating genres for artist %s from %s to %s", plex_artist.title, genre_names, genre)
            plex_artist.addGenre(genre)


def _sync_album(plex_album, genre):
    if genre is not None:
        genre_names = _genre_names(plex_album)
        if genre not in genre_names:
            root_logger.info("Updating genre for album '%s' from %s to %s", plex_album.title, genre_names, genre)
            plex_album.addGenre(genre)


def _sync_media(music, type, artist, album, title, genre, rating, explicit):
    global sync_count
    sync_count += 1
    root_logger.info("Syncing %d %s '%s' '%s' '%s' '%s' rating '%s' explicit %s", sync_count, type, artist, album, title, genre, rating, explicit)
    plex_song, plex_album, plex_artist = _find_media(music, artist, album, title)
    if plex_song and plex_album and plex_artist:
        _sync_song(plex_song, title, genre, rating, explicit)
        _sync_artist(plex_artist, genre)
        _sync_album(plex_album, genre)
    else:
        _log_fatal("Song '%s' '%s' '%s' not found on Plex!", title, album, artist)


def _get_mp3_tag(song, tag, tagtype):
    tagvalue = song.tags.get(tag)
    if tagvalue:
        return tagvalue.text[0]
    root_logger.info("MP3 %s has no %s", song.filename, tagtype)


def _get_first_mp3_tag(song, tag, tagtype):
    tagvalues = song.tags.getall(tag)
    if tagvalues and len(tagvalues) > 0:
        return tagvalues[0]
    root_logger.info("MP3 %s has no %s", song.filename, tagtype)


def _get_first_mp3_tag_element(song, tag, tagtype, element):
    tagvalue = _get_first_mp3_tag(song, tag, tagtype)
    if tagvalue:
        return getattr(tagvalue, element)


def get_mp3_artist(song):
    return _get_mp3_tag(song, 'TPE1', 'artist')


def get_mp3_album(song):
    return _get_mp3_tag(song, 'TALB', 'album')


def _get_mp3_title(song):
    title = _get_mp3_tag(song, 'TIT2', 'title')
    if not title:
        logger.error("Missing title for %s in tags %r", song.filename, song.tags)
    return title


def get_mp3_genre(song):
    return _get_mp3_tag(song, 'TCON', 'genre')


def get_mp3_rating(song):
    raw_rating = _get_first_mp3_tag_element(song, 'POPM', 'rating', 'rating')
    if raw_rating:
        return raw_rating / 25.5


def get_mp3_comment(song):
    comments = _get_first_mp3_tag_element(song, 'COMM', 'comment', 'text')
    if comments and len(comments):
        return comments[0]


def _sync_mp3(music, filename):
    song = mutagen.File(filename)
    if song:
        artist = get_mp3_artist(song)
        album = get_mp3_album(song)
        title = _get_mp3_title(song)
        genre = get_mp3_genre(song)
        rating = get_mp3_rating(song)
        comment = get_mp3_comment(song)
        if artist and album and title:
            _sync_media(music, 'mp3', artist, album, title, genre, rating, comment and 'explicit' in comment.lower())
        else:
            _log_fatal("Missing required elements for %s: %s %s %s", filename, artist, album, title)
    else:
        _log_fatal("Failed to load %s", filename)


def _get_mp4_tag(song, tag, tagtype):
    tagvalues = song.tags.get(tag)
    if tagvalues and len(tagvalues) > 0:
        return tagvalues[0]
    root_logger.info("MP4 %s has no tag %s", song.filename, tagtype)


def _get_mp4_artist(song):
    return _get_mp4_tag(song, '©ART', 'artist')


def _get_mp4_album(song):
    return _get_mp4_tag(song, '©alb', 'album')


def _get_mp4_title(song):
    return _get_mp4_tag(song, '©nam', 'title')


def _get_mp4_genre(song):
    return _get_mp4_tag(song, '©gen', 'genre')


def _get_mp4_rating(song):
    for tag in ['rate', 'rtng']:
        tagvalues = song.tags.get(tag)
        if tagvalues and len(tagvalues) > 0:
            rating = int(tagvalues[0])
            if rating > 0:
                return rating / 10.0
    root_logger.info("MP4 %s has no rating", song.filename)


def _get_mp4_comment(song):
    return _get_mp4_tag(song, '©cmt', 'comment')


def _sync_mp4(music, filename):
    song = mutagen.File(filename)
    if song:
        artist = _get_mp4_artist(song)
        album = _get_mp4_album(song)
        title = _get_mp4_title(song)
        genre = _get_mp4_genre(song)
        rating = _get_mp4_rating(song)
        comment = _get_mp4_comment(song)
        if artist and album and title:
            _sync_media(music, 'mp4', artist, album, title, genre, rating, comment and 'explicit' in comment.lower())
        else:
            _log_fatal("Missing required elements for %s: %s %s %s", filename, artist, album, title)
    else:
        _log_fatal("Failed to load %s", filename)


def _sync_m3u(music, root, filename, sync_special_playlists):
    playlist_name = os.path.splitext(os.path.basename(filename))[0]
    # Delete any existing playlist with the same name.
    try:
        music.playlist(playlist_name).delete()
    except NotFound:
        root_logger.info("No existing playlist '%s'", playlist_name)
    playlist = m3u8.load(filename)
    root_logger.info("Syncing playlist '%s': %r", playlist_name, playlist.files)
    tracks = []
    for file in playlist.files:
        filepath = os.path.join(root, file)
        song = mutagen.File(filepath)
        artist = None
        album = None
        title = None
        if file.endswith('.mp3'):
            artist = get_mp3_artist(song)
            album = get_mp3_album(song)
            title = _get_mp3_title(song)
        elif file.endswith(".m4a"):
            artist = _get_mp4_artist(song)
            album = _get_mp4_album(song)
            title = _get_mp4_title(song)
        plex_song, plex_album, plex_artist = _find_media(music, artist, album, title)
        if plex_song:
            # Treat a playlist named 'Unchecked' as special. Tag all songs in that playlist with 'Unchecked'
            if playlist_name == 'Unchecked':
                root_logger.info("Updating mood for unchecked song %s to include 'Unchecked'", title)
                plex_song.addMood('Unchecked')
            if playlist_name == 'Explicit':
                root_logger.info("Updating mood for explicit song %s to include 'Explicit'", title)
                plex_song.addMood('Explicit')
            tracks.append(plex_song)
        else:
            logger.error("Playlist song '%s' '%s' '%s' not found!", artist, album, title)
    root_logger.info("Creating playlist '%s' with %r", playlist_name, tracks)
    logger.info("Creating playlist '%s'", playlist_name)
    if (playlist_name != 'Unchecked' and playlist_name != 'Explicit') or sync_special_playlists:
        music.createPlaylist(playlist_name, tracks)


def sync(plex, directory, sync_special_playlists):
    """Sync metadata from local song media files to a Plex server."""
    music = plex.library.section('Music')
    logger.info("Syncing songs in directory %s to Plex %s with %s songs", directory, plex.friendlyName, len(music.searchTracks()))
    for root, subdirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.mp3'):
                _sync_mp3(music, os.path.join(root, file))
            elif file.endswith(".m4a"):
                _sync_mp4(music, os.path.join(root, file))
            elif file.endswith(".m3u") or file.endswith(".m3u8"):
                _sync_m3u(music, root, os.path.join(root, file), sync_special_playlists)

def _clear_song(plex_song):
    for mood in plex_song.moods:
        root_logger.info("Removing mood %s for %s from %s", mood.tag, plex_song.title, plex_song.moods)
        plex_song.removeMood(mood.tag)


def _clear_artist(plex_artist):
    for genre in plex_artist.genres:
        root_logger.info("Removing genre %s for %s from %s", genre.tag, plex_artist.title, plex_artist.genres)
        plex_artist.removeGenre(genre.tag)
    for style in plex_artist.styles:
        root_logger.info("Removing style %s for %s from %s", style.tag, plex_artist.title, plex_artist.styles)
        plex_artist.removeStyle(style.tag)


def _clear_album(plex_album):
    for genre in plex_album.genres:
        root_logger.info("Updating genre %s for %s from %s", genre.tag, plex_album.title, plex_album.genres)
        plex_album.removeGenre(genre.tag)
    for style in plex_album.styles:
        root_logger.info("Removing style %s for %s from %s", style.tag, plex_album.title, plex_album.genres)
        plex_album.removeStyle(style.tag)


def _clear_tags(music, type, artist, album, title):
    global clear_count
    clear_count += 1
    root_logger.info("Clearing tags %d %s '%s' '%s' '%s'", clear_count, type, artist, album, title)
    plex_song, plex_album, plex_artist = _find_media(music, artist, album, title)
    if plex_song and plex_album and plex_artist:
        _clear_song(plex_song)
        _clear_artist(plex_artist)
        _clear_album(plex_album)
    else:
        _log_fatal("Song '%s' '%s' '%s' not found on Plex!", title, album, artist)


def _clear_tags_mp3(music, filename):
    song = mutagen.File(filename)
    if song:
        artist = get_mp3_artist(song)
        album = get_mp3_album(song)
        title = _get_mp3_title(song)
        if artist and album:
            _clear_tags(music, 'mp3', artist, album, title)
        else:
            _log_fatal("Missing required elements for %s: %s %s %s", filename, artist, album, title)
    else:
        logger.error("Failed to load %s", filename)


def _clear_tags_mp4(music, filename):
    song = mutagen.File(filename)
    if song:
        artist = _get_mp4_artist(song)
        album = _get_mp4_album(song)
        title = _get_mp4_title(song)
        if artist and album:
            _clear_tags(music, 'mp4', artist, album, title)
        else:
            _log_fatal("Missing required elements for %s: %s %s %s", filename, artist, album, title)
    else:
        _log_fatal("Failed to load %s", filename)


def clear(plex, directory):
    """Clear genre and mood from Artists, Albums, and tracks."""
    music = plex.library.section('Music')
    logger.info("Clearing tags from songs in directory %s on Plex %s with %s songs", directory, plex.friendlyName, len(music.searchTracks()))
    for root, subdirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.mp3'):
                _clear_tags_mp3(music, os.path.join(root, file))
            elif file.endswith(".m4a"):
                _clear_tags_mp4(music, os.path.join(root, file))


def main(argv):
    """Sync playlists and music file ratings and genres to a Plex server."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="Print the program's version", action='version', version=f"{__file__} {__version__}")
    parser.add_argument("-s", "--server", help="Hostname of the Plex server")
    parser.add_argument("-u", "--username", help="Username of the Plex server")
    parser.add_argument("-p", "--password", help="Password of the Plex server")
    parser.add_argument("-d", "--directory", help="Directory that contains the music files")
    parser.add_argument("-S", "--sync", help="Sync genres, ratings, and playlists to Plex", action="store_true")
    parser.add_argument("-P", "--specialplaylists", help="Sync special playlists as playlists. Don't just tag the songs in them.", action="store_true")
    parser.add_argument("-c", "--clear", help="Clear ratings and genre on Plex", action="store_true")
    parser.add_argument("-D", "--debug", help="Log more error messages", action="store_true")
    parser.add_argument("-f", "--fatal", help="Exit with an error message if song data is missing.", action="store_true")

    args = parser.parse_args()

    global fatal
    fatal = args.fatal

    if args.debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    plex = login(args.server, args.username, args.password)
    if args.clear:
        clear(plex, args.directory)
    if args.sync:
        sync(plex, args.directory, args.specialplaylists)


if __name__ == "__main__":
    main(sys.argv[1:])
