#!/bin/bash

# Tool that converts all printable ASCII characters of a provided TTF font file into character ROM suitable for VGI.
# Individial characters are rendered as 8x16 black&white, 1bpp bitmaps (no antialiasing) and are then combined back-to-back 
#   into a single binary file (in the same order as they appear in ASCII code set, so that the first bitmap is ASCII+32).
#
# Bitmaps are laid out as expected by vgi_blit_1bpp(): pixels go row by row, left to right, MSB first; set bits are white.
#   Note that ImageMagick pads each row to a whole byte, so bitmap width has to be a multiple of 8, and the whole bitmap
#   has to take a whole number of 32-bit words (8x16 = 128 bits = 4 words).
#
# The font is expected to be a pixel outline font with 8x16 cell at POINT_SIZE (e.g. Px437 fonts from The Ultimate Oldschool
#   PC Font Pack): glyphs are drawn without antialiasing or stroke on an explicit baseline, so that every pixel of the outline
#   maps exactly to one pixel of the bitmap.

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <font file> <output file>"
  exit 1
fi

POINT_SIZE=16
BITMAP_SIZE="8x16"
BITMAP_BYTES=16
BASELINE=12
TMP_FILE="tmp.gray"

: > $2

for ((i=32; i<=126; i++)); do
    printf "\x$(printf %x $i)" > $TMP_FILE
    cat $TMP_FILE
    magick -size $BITMAP_SIZE xc:black -font $1 -pointsize $POINT_SIZE -fill white +antialias \
      -annotate +0+$BASELINE @$TMP_FILE -colorspace gray -depth 1 $TMP_FILE

    if [ "$(wc -c < $TMP_FILE)" -ne $BITMAP_BYTES ]; then
      echo "Error: bitmap of character $i is not $BITMAP_BYTES bytes long"
      rm $TMP_FILE
      exit 1
    fi

    magick -size $BITMAP_SIZE -depth 1 $TMP_FILE $2.$i.png
    
    cat $TMP_FILE >> $2
done

rm $TMP_FILE
