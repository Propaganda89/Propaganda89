# Publish this GitHub profile README

Your public GitHub username is `Propaganda89`, so GitHub displays this README on your profile
when it lives in a public repository with that exact name.

1. Create a public repository named `Propaganda89`.
2. Upload `README.md` and the whole `assets` folder.
3. Visit `https://github.com/Propaganda89`.
4. In profile settings, enable private contribution visibility if you want private activity
   reflected in your contribution graph.

## Assets

| File | Used for |
| :-- | :-- |
| `assets/hero-dark.svg` | Masthead shown on GitHub's dark theme |
| `assets/hero-light.svg` | Masthead shown on GitHub's light theme |
| `assets/logo.png` | Source logo; also the signature mark above the closing links |

The README references these with relative paths, so keep the folder structure unchanged.

## How the masthead works

`README.md` opens with a `<picture>` element that swaps the masthead on
`prefers-color-scheme`. Each file's background is exactly GitHub's own canvas for that theme
(`#0d1117` dark, `#ffffff` light), so the masthead is seamless with the page rather than
sitting on it as a visible rectangle.

Two things make the SVGs safe to serve from GitHub:

- **All type is outlined to `<path>`.** Web fonts never load inside an SVG referenced by an
  `<img>` (the raw host sends `default-src 'none'`, so `font-src` is blocked), and system font
  stacks have different metrics per OS. Outlining is the only way to guarantee the typography
  renders identically for everyone.
- **The HM monogram is a vector trace of `logo.png`,** not an embedded raster. A
  `data:` URI inside a raw-served SVG is blocked by the same policy.

## Editing the masthead

Because the type is outlined, the words in the masthead are vector shapes, not editable text —
changing "HCINI MOEZ" or the role line means regenerating both SVGs from the source artwork
rather than editing the file by hand. Colours, spacing and the accent rule can still be edited
directly in the SVG.

If you regenerate at different proportions, update the `width` and `height` on the `<img>`
inside the `<picture>` block in `README.md` so they match the new `viewBox` — otherwise the
browser reserves the wrong space while the image loads.

## Colour rules worth keeping

The brand green `#04F404` is 12.6:1 against GitHub's dark canvas but only **1.5:1 against
white**, so it can never be text or a thin line on the light theme. That is why the monogram
always sits on a black tile: on its own ground it stays at full brand strength in both themes.
For anything green on a light background, use `#00713C` (6.1:1) instead.
