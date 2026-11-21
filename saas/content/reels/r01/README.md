# Reel R01: Claude × ReplyInbox setup (keyword SETUP)

Reference: @jayantcreates.ai (script kept, product swapped to ReplyInbox; changes listed in the chat). 42.7 s, 1080×1920.
Rebuild (see saas/REELS_HANDOFF.md): copy this folder into the Remotion workspace with `public/chars/` (poses from
content/characters/om, upscaled with the white + cobalt outline), then:
`ffmpeg -i vo_raw.mp3 -ac 1 -ar 48000 vo48.wav && python3 cut_silence.py vo48.wav vo_cut.wav 0.16 0.06`
`ffmpeg -i vo_cut.wav -af "atempo=1.24,loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -ac 1 public/vo.wav && python3 build_audio.py`
`npx remotion render src/index.ts Reel out/raw.mp4 --public-dir=$PWD/public ...` then loudnorm + 0.4 s fade (as in the handoff).
