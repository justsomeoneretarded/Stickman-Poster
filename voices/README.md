# Public character voice profiles

Published with the user's explicit authorization on 19 October 2026.
These are reusable Chatterbox speaker-conditioning profiles configured for Turbo. They can be
downloaded and used to synthesize speech resembling the supplied speakers.
Original reference MP3s are not included. No API key or decryption key is required.

`cast-profiles.json` maps female, male1, and male2 to their profile directories.
Each `profile.json` records the model source revision and conditioning SHA-256.
The application verifies that checksum before loading the conditioning.
The fictional character names are configured by the story writer, not these files.

The tensors were originally enrolled with Nano. Migration to pinned Turbo retains
them because both versions use identical voice encoder, decoder and tokenizer
files, and the same conditioning extraction API. Metadata records this origin;
the Turbo text-to-speech checkpoint is separate. No stock-voice fallback is used.
