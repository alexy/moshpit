#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
book_root="$repo_root/book"
dist="$book_root/dist"
build="$book_root/build"
stem="moshpit-guide"
mkdir -p "$dist" "$build"

pandoc_common=(
  --from markdown+smart
  --metadata-file "$book_root/metadata.yaml"
  --resource-path "$book_root:$repo_root"
  --toc
  --toc-depth=2
)

pandoc "$book_root/manuscript.md" \
  -o "$build/$stem-body.pdf" \
  --pdf-engine=typst \
  "${pandoc_common[@]}"

typst compile --root "$book_root" "$book_root/cover.typ" "$build/$stem-cover.pdf"
pdfunite "$build/$stem-cover.pdf" "$build/$stem-body.pdf" "$dist/$stem.pdf"

pandoc "$book_root/manuscript.md" \
  -o "$dist/$stem.epub" \
  --to epub3 \
  --css "$book_root/epub.css" \
  --epub-cover-image "$book_root/assets/moshpit-cover.png" \
  --epub-title-page=false \
  "${pandoc_common[@]}"

pandoc "$book_root/manuscript.md" \
  -o "$dist/$stem.html" \
  --standalone \
  --embed-resources \
  --css "$book_root/epub.css" \
  "${pandoc_common[@]}"

chunk_zip="$build/$stem-chapters.zip"
chunk_dir="$dist/$stem-chapters"
mkdir -p "$build/chunk-work" "$chunk_dir"
find "$chunk_dir" -mindepth 1 -delete
(
  cd "$build/chunk-work"
  pandoc "$book_root/manuscript.md" \
    --from markdown+smart \
    --to chunkedhtml \
    --standalone \
    --toc \
    --toc-depth=2 \
    --metadata-file "$book_root/metadata.yaml" \
    --resource-path "$book_root:$repo_root" \
    --split-level=1 \
    --chunk-template=chapter-%n.html \
    --embed-resources \
    --output "$chunk_zip"
)
unzip -q -o "$chunk_zip" -d "$chunk_dir"

cp "$book_root/assets/moshpit-cover.png" "$dist/$stem-cover.png"
cp "$book_root/assets/moshpit-headboard.png" "$dist/$stem-headboard.png"
cp "$book_root/VERSION.md" "$dist/VERSION.md"
find "$dist" -maxdepth 1 -type f ! -name SHA256SUMS -print0 \
  | sort -z \
  | xargs -0 shasum -a 256 > "$dist/SHA256SUMS"
