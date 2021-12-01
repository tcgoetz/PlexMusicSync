# PlexMusicSync
Synchronize a local directory of songs' (MP3, MP4) metadata (genre, ratings) and playlists (m3u, m3u8) with a Plex server. The song files must already be present in Plex.

I'm a long time Plex user, but until recently I've only used Plex for Movies and TV shows because I found Plex music support to be lacking. I have a large music library and need smart playlists based on track rating, track genre, track explicit lyrics, disabling of duplicate tracks (from compilations), track years, etc. None of this metadata was present in Plex or supported by the Plex import. This script fills that gap by syncing that metadata from song files and playlists.

Syncing tags:
- MP3 or MP4 file genre to.
    - Song artist genre on Plex.
    - Song album genre on Plex.
    - Song mood on Plex (since Plex doesn't have per-song genre).
- MP3 or MP4 song rating to song rating on Plex.
- If MP3 or MP4 file comment contains the word explicit, then 'Explicit' is added to the Plex song mood tags.

Syncing Playlists
- Sync m3u and m3u8 files found locally to music playlists on Plex.
    - If a playlist named 'Unchecked' is found it is considered special and is assumed to be a list of songs that are NOT checked in Apple Music. Songs in this playlist are tgged with a mood value 'Unchecked'.
    - If a playlist named 'Explicit' is found it is considered special and is assumed to be a list of songs that contain explciti lyrics. Songs in this playlist are tgged with a mood value 'Explicit'.

Clearing tags:
- For each MP3 or MP4 file.
    - Clear all song artist genre tags on Plex.
    - Clear all song album genre tags on Plex.
    - Clear all song mood tags on Plex.

## Usage
Install required Python modules with

```pip3 install -r requirements.txt```

then run the script as follows:

```
usage: plex_music_sync.py [-h] [-v] [-s SERVER] [-u USERNAME] [-p PASSWORD] [-d DIRECTORY] [-S] [-P] [-c] [-D] [-f]

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         Print the program's version
  -s SERVER, --server SERVER
                        Hostname of the Plex server
  -u USERNAME, --username USERNAME
                        Username of the Plex server
  -p PASSWORD, --password PASSWORD
                        Password of the Plex server
  -d DIRECTORY, --directory DIRECTORY
                        Directory that contains the music files
  -S, --sync            Sync genres, ratings, and playlists to Plex
  -P, --specialplaylists
                        Sync special playlists as playlists. Don't just tag the songs in them.
  -c, --clear           Clear ratings and genre on Plex
  -D, --debug           Log more error messages
```

Todo:
- Token based Plex server login.
- Some way of handling track year.
