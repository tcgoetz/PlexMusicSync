# PlexMusicSync
Synchronize a local directory of songs' (MP3, MP4) metadata (genre, ratings) and playlists (m3u, m3u8) with a Plex server. The song files must already be present in Plex.

Syncing tags:
- MP3 or MP4 file genre to.
    - Song artist genre on Plex.
    - Song album genre on Plex.
    - Song mood on Plex (since Plex doesn't have per-song genre).
- MP3 or MP4 song rating to song rating on Plex.
- If MP3 or MP4 file comment contains the word explicit, then 'Explicit' is added to the Plex song mood tags.

Syncing Playlists
- Sync m3u files found to music playlists on Plex.

Clearing tags:
- For each MP3 or MP4 file.
    - Clear all song artist genre tags on Plex.
    - Clear all song album genre tags on Plex.
    - Clear all song mood tags on Plex.

Usage:

Install required Python modules with

pip3 install -r requirements.txt

then run the script as follows:

```
orion:PlexMusicSync tgoetz$ ./plex_music_sync.py -h
usage: plex_music_sync.py [-h] [-v] [-s SERVER] [-u USERNAME] [-p PASSWORD] [-d DIRECTORY] [-S] [-c] [-D] [-f]

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
  -S, --sync            Sync genres and ratings to Plex
  -c, --clear           Clear ratings and genre on Plex
  -D, --debug           Log more error messages
  -f, --fatal           Exit with an error message if song data is missing.
```

Todo:
- Token based Plex server login.
- Create a special playlist of songs that are checked (enabled) in iTunes and sync that to Plex in a way that can be used in smart playlists.
