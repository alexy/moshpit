# Moshpit announcement textpack

`post.md` is the canonical Ghost/Markdown announcement. Build the portable
TextBundle with the First Pair Press packager:

```sh
python /Users/alexy/src/firstpair/publishing/scripts/textpack.py post.md \
  --name moshpit-guide \
  --blog firstpair.press \
  --slug moshpit-guide \
  --tags "agent development,terminals,mosh,tmux,Ghostty" \
  --excerpt "A new First Pair Press field guide to persistent remote agent development." \
  --out dist/moshpit-guide.textpack
```

