#!/usr/bin/env bash

cd "$(dirname "$0")"
src=065-remove-page-borders
dst=$(basename "$0" .sh)

# empty pages:
# 100.0000
# 099.9999
# 099.9997
# ...
src_empty_pages_txt=067-find-empty-pages.txt
src_empty_pages_pattern='^(099\.999|100\.0000)'

mkdir -p $dst

t1=$(date --utc +%s)
num_pages=0

# array
empty_pages=(
  $(grep -E "$src_empty_pages_pattern" "$src_empty_pages_txt" | cut -c10- | sort -n)
)

if [ ${#empty_pages[@]} != 0 ]; then
  echo skipping deskew on empty pages: ${empty_pages[@]}
fi

# dict
declare -A is_empty_page
for page_number in ${empty_pages[@]}; do is_empty_page[$page_number]=1; done

for i in $src/*; do

  # FIXME use $num_pages and $scan_format
  page_number=${i%.tiff}
  page_number=${page_number##*/}
  page_number=${page_number#0}
  page_number=${page_number#0}
  page_number=${page_number#0}
  page_number=${page_number#0}

  o=$dst/${i##*/}

  [ -e "$o" ] && continue

  # dont deskew empty pages
  # workaround: deskew fails on empty pages
  # https://github.com/galfar/deskew/issues/71
  if [ "${is_empty_page[$page_number]}" = 1 ]; then
    echo skipping deskew on empty page $page_number
    cp "$i" "$o"
    continue
  fi

  deskew_args=(deskew -o "$o")

  # add white background
  deskew_args+=(-b FFFFFF)

  # -a angle:      Maximal expected skew angle (both directions) in degrees (default: 10)
  # expected angle is -0.5 or +0.5
  # deskew_args+=(-a 1)

  deskew_args+=("$i")

  echo + "${deskew_args[@]}"
  "${deskew_args[@]}"

  num_pages=$((num_pages + 1))

  # [ "$page_number" = 10 ] && break # debug

done

t2=$(date --utc +%s)
echo "done $num_pages pages in $((t2 - t1)) seconds"
