# OG image fonts

The OpenGraph image generator (`app/routers/og.py`) renders TIL preview cards
using these fonts. The lookup chain in `og.py` tries each in order:

1. **`fraunces.ttf`** in this directory (drop the file here for pixel-perfect aesthetic)
2. **`jetbrains-mono.ttf`** in this directory (for the small mono labels)
3. **System Linux**: `/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf` / `DejaVuSansMono.ttf`
4. **System macOS**: Times / Menlo
5. **PIL bitmap fallback** (ugly but always renders)

## To upgrade to the real site fonts

```sh
cd backend/app/fonts
curl -L -o fraunces.ttf       "https://github.com/undercase/fraunces/raw/main/fonts/static/Fraunces/Fraunces-Medium.ttf"
curl -L -o jetbrains-mono.ttf "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Medium.ttf"
```

Both fonts are SIL OFL licensed (free to redistribute).

These TTF files are git-ignored by default; if you want them version-controlled,
remove the `*.ttf` line from this directory in `.gitignore`.
