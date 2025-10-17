#!/usr/bin/env bash

# NOTE this must run before deskew
# beause my scanner leaves extra space at the bottom of pages
# with a horizontal edge which is not parallel to the page edge
# so that "false edge" would distort the deskew result

set -eu

cd "$(dirname "$0")"
src=045-crop-scan-area
dst=$(basename "$0" .sh)

if true; then
  source 030-measure-page-size.txt
  source 050-measure-crop-size.txt
else
  # 030-measure-page-size.txt
  num_pages=372
  scan_format=tiff

  # 050-measure-crop-size.txt
  # original size: 1748x2480
  do_rotate=true
  rotate_odd=090
  rotate_even=270

  do_crop=true
  crop_size=1580x2480
  crop_x=168
  crop_odd_expr='echo ${crop_size}+$crop_x+0'
  crop_even_expr='echo ${crop_size}+000+0'

  do_level=true
  lowthresh=20; highthresh=90
  level=${lowthresh}x${highthresh}%
fi

mkdir -p $dst

t1=$(date --utc +%s)
num_pages=0

for i in $src/*.$scan_format; do

  # FIXME use $num_pages and $scan_format
  page_number=${i%.tiff}
  page_number=${page_number##*/}
  page_number=${page_number#0}
  page_number=${page_number#0}

  o=$dst/${i##*/}

  [ -e "$o" ] && continue

  if ((page_number % 2 == 1)); then
    rot=$rotate_odd
    crop=$crop_odd
  else
    rot=$rotate_even
    crop=$crop_even
  fi

  # magick "$i" -rotate $rot -crop $crop -level $level "$o"
  magick_args=(magick "$i")
  if $do_rotate; then magick_args+=(-rotate $rot); fi
  if $do_crop; then magick_args+=(-crop $crop); fi
  if $do_level; then magick_args+=(-level $level); fi
  magick_args+=("$o")

  echo + "${magick_args[@]}"
  "${magick_args[@]}"

  num_pages=$((num_pages + 1))

  # [ "$page_number" = 20 ] && break # debug

  sleep 0.01 # let user kill

done

t2=$(date --utc +%s)
echo "done $num_pages pages in $((t2 - t1)) seconds"
