# CathedralOS — Audio Foundry v6.1

Automation recommends. Human decides. Reality has the final vote.

Release reference: 32400a834866b0b5806a0ec8720641a26ab4db19

## Architecture

| Branch | Harmonic Center | Tuning | Sponsor |
|---|---|---|---|
| A | Bb | 432 / 420 Hz | Electric Chartreuse #DFFF00 |
| Bridge | F#7 | 432 Hz | Tritone Pivot |
| B | Dm9 -> G13 -> Cmaj9 | 432 Hz | Mystic Burgundy #4A0E2E |

## Synthesis Engine

- Tempo: 94 BPM
- Slapback delay: 159 ms
- Feedback: 0.38
- Rhythm: 3 / 6 / 9
- Glitch chirps: 369 Hz
- Random generator: random.Random(SEED)
- Configured seed: 369

## Dependencies

Python 3 standard library:
- wave
- math
- struct
- random

No third-party dependencies.

## Demo Audio

File: cathedralos_v6_1_demo.wav

- PCM WAV
- 44,100 Hz
- 16-bit
- Mono
- Duration: 10.213 seconds

## Reproduction

Run from the repository root:

    python3 audio_foundry/render.py

Output:

    audio_foundry/cathedralos_v6_1_demo.wav

Bit-for-bit reproducibility should be verified by comparing SHA-256 hashes from two separate renders.

## Release Integrity

Original release reference:
32400a834866b0b5806a0ec8720641a26ab4db19

Future changes should be committed separately.

Where ritual becomes architecture. Where code becomes meaning.
