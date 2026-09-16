# Bitfont
`mkfont.sh` converts printable ASCII characters of a pixel outline TTF font into the 1bpp character ROM used by
LLR textmode routines (`build/bitfont.gray`).

## Font attribution
`Px437_IBM_VGA_8x16.ttf` is taken from [The Ultimate Oldschool PC Font Pack](https://int10h.org/oldschool-pc-fonts/)
v2.2, (c) 2016-2020 VileR, and is licensed under the
[Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).

The character ROM generated from it (`build/bitfont.gray`) is an adaptation of this font (rendered into 8x16 1bpp
bitmaps) and is distributed under the same license.
