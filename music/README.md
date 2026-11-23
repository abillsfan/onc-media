# Reel music

Royalty-free tracks from Pixabay (Pixabay Content License: free for commercial use, no attribution required).
Each one was checked on Nov 23 2026 and is **not** "Content ID Registered" on Pixabay, so Facebook shouldn't flag or mute reels that use it.
Never use tracks marked Content ID Registered, and never commercial songs (Carl asked for "How You Like Me Now"-style music;
these are the free stand-ins).

| file | track | artist | page |
|---|---|---|---|
| stomp-clap-rock.mp3 | Time to Stomp Clap and Rock | DouglasRicketts | https://pixabay.com/music/rock-time-to-stomp-clap-and-rock-369734/ |
| stomp-percussion.mp3 | Stomp Clap Percussion (Free Music) | MiroMaxMusic | https://pixabay.com/music/percussion-stomp-clap-percussion-free-music-512505/ |
| blues-rock-12.mp3 | Blues Rock Instrumental 12 | alanajordan | https://pixabay.com/music/blues-blues-rock-instrumental-12-442495/ |
| blues-rock-09.mp3 | Blues Rock Instrumental 09 | alanajordan | https://pixabay.com/music/rock-blues-rock-instrumental-09-441089/ |
| trap-hype.mp3 | Trap Hype | jonasblakewood | https://pixabay.com/music/trap-trap-trap-hype-623044/ |
| trap-action.mp3 | Trap Action | jonasblakewood | https://pixabay.com/music/trap-trap-action-623046/ |
| action-sport-rock.mp3 | Action Sport Rock | jonasblakewood | https://pixabay.com/music/rock-action-sport-rock-626834/ |

Use in a hit reel spec: `"audio_file": "music/<file>"`. `tools/hit_reel.py` finds the track's biggest beat drop and lines it up
with the moment the card appears (override with `"audio_start": <seconds>`).
