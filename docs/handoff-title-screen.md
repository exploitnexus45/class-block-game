# Feature handoff

Student/team: (write your name and team here)
Starting version: Class Block World v0.1 (latest commit: "Document Mac verification and texture quest markers")
Task card: (write your task card here; this was made as a graphics proposal)
Changed files: none of the existing files. One new file: `title_screen.py`.

## What changed

A title screen and loading screen for the game, named **Glocinshmeel io**. The game itself is not connected yet; I will attach it later.

- The title is written in big, thick letters in gold, green, and blue, with a blocky, stair-stepped dark outline and a blocky shadow. Every letter is the same width so they line up evenly. Each letter drops in and bounces into place, then the whole title floats gently up and down together. A white sparkle twinkles on the letters.
- Tagline: "Dig. Build. Explore." and a hint: "Catch the ball to play!"
- The **PLAY** button is a glossy red bouncy ball with PLAY written on it. It bounces all around the screen, squishes when it hits the bottom, and PLAY spins as it flies. Clicking (catching) the ball makes the screen fill with colored blocks.
- Then a **loading screen** appears. It types out `1...2......4......8.....16......32.......64........128........256.....512.....1024!` a little at a time, shows the newest number big in the middle, and fills a bar with one colored slot for each number. When it reaches 1024! it waits a moment and then goes back to the title screen (until the game is attached).
- The background is a sunny day: a blue sky with a pixel sun and drifting clouds, and three rows of rolling green hills with trees and flowers.
- The front hill is cut open to show what is underneath: dirt, then stone, deepslate, and bedrock with gold, green, and blue ore. A lit-up mine shaft runs through the stone with wooden beams, rails, a minecart, cobwebs, and two torches. Two miner dogs in yellow helmets with lamps swing pickaxes at the ore walls, wag their tails, and knock out rock chips.
- A red dog runs along the front hill chasing the bouncy PLAY ball. It runs whichever way the ball goes, jumps for it when it comes close, and stands wagging its tail once the ball is caught.
- Five more dogs play on the hills. A golden dog runs along the front hill while a black-and-white dog chases it. A white dog plays fetch, running back and forth under a red ball and jumping to catch it. A brown dog sits on the middle hill wagging its tail and hopping, and a gray dog trots along the middle hill.
- Uses only Ursina and Pillow, which are already in requirements.txt. No new packages. All artwork is drawn by the code, so there are no image files to credit.
- It never reads or changes world data.

## Tests I actually ran and their results

Run on a Linux test computer with the exact versions in requirements.txt (Python 3.13):

1. `python title_screen.py --screenshot` ran without errors and saved `artifacts/title.png`. The picture looked right.
2. A test script watched the ball bounce for a few seconds, then caught it: the colored blocks appeared, the loading screen counted all the way to 1024!, and then the title screen came back with the ball bouncing again.
3. `python -m pytest tests/test_game.py`: 8 passed (no existing files were changed).

Not tested: a real Mac or Windows computer, a real mouse click (clicks were done by code), and sound.

## Known issues

- The game is not attached yet, so the loading screen goes back to the title when it finishes.
- The background picture is made once when the screen opens. If the window is resized while the title screen is showing, the picture stretches.
- The picture from `--screenshot` goes into `artifacts/`, like the smoke test.

## Requested changes outside my assigned files (for the instructor)

None right now. When the game is ready to attach, the title screen takes a function to run after loading finishes:

```python
from title_screen import TitleScreen
TitleScreen(on_loaded=start_the_game)
```

The tagline and hint are easy to change in `build_title()`, and the counting text is `COUNT_TEXT` near the top of the file.

## One piece of Python I can explain

`FONT` is a dictionary. Each key is a letter or number, like `'P'` or `'4'`, and each value is a list of 9 strings. In each string, `#` means "this part of the letter is filled in" and `.` means "leave it empty". Because every letter uses the same 7-wide grid, all the letters are the same width. The function `letter_texture()` fills in every `#`, smooths the corners, and adds color, an outline, and a shadow to make one smooth letter picture.
