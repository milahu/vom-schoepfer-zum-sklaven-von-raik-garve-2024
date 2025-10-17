#!/usr/bin/env bash

src=065-remove-page-borders

dst=$(basename "$0" .sh)

mkdir -p $dst

t1=$(date --utc +%s)
num_pages=0

for i in $src/*; do

  # FIXME use $num_pages and $scan_format
  page_number=${i%.tiff}
  page_number=${page_number##*/}
  page_number=${page_number#0}
  page_number=${page_number#0}
  page_number=${page_number#0}
  page_number=${page_number#0}

  if ! lightness=$(magick "$i" -colorspace gray -format "%[fx:mean*100]" info:); then
    # echo "error: failed to get lightness of image $i" >&2
    lightness="-1"
  fi

  # echo "$(LC_ALL=C printf '%08.4f' $lightness) ${i##*/}"
  echo "$(LC_ALL=C printf '%08.4f' $lightness) $page_number"

  num_pages=$((num_pages + 1))

  # [ "$page_number" = 10 ] && break # debug

done |
tee -a /dev/stderr |
sort -r -g \
>$dst.txt

t2=$(date --utc +%s)
echo "done $num_pages pages in $((t2 - t1)) seconds"
