#!/bin/bash

# Tool that converts all printable ASCII characters of a provided TTF font file into character ROM suitable for VGI.
# Individial characters are rendered as 8x16 black&white, 32bpp bitmaps (no antialiasing) and are then combined back-to-back 
#   into a single binary file (in the same order as they appear in ASCII code set, so that the first bitmap is ASCII+32).

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <font file> <output file>"
  exit 1
fi

POINT_SIZE=16
BITMAP_SIZE="8x16"
TMP_FILE="tmp.gray"

touch $2

for ((i=32; i<=126; i++)); do
    printf "\x$(printf %x $i)" > $TMP_FILE
    cat $TMP_FILE
    magick -font $1 -pointsize $POINT_SIZE -size $BITMAP_SIZE -background black -fill white -stroke white \
      -gravity center +antialias label:@$TMP_FILE -colorspace gray -depth 32 $TMP_FILE
    
    cat $TMP_FILE >> $2
done

rm $TMP_FILE
