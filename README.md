# PlexMusicSync
Synchonzie a local directory of songs (genre, tags)  and playlists with a Plex server.

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
