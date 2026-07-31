# FirstPair Library Contract

slug: moshpit-guide
shelf: technology
default_edition: full

This source directory owns the Moshpit manuscript, build configuration,
version metadata, cover and headboard art, and canonical book artifacts.
The First Pair repository owns catalog delivery, Blob uploads, hosted readers,
iCloud copies, and production deployment.

## FirstPair Deployment

Inspect the resolved publication plan before any public action:

```sh
cd "$HOME/src/firstpair"
npm run library:publish -- "$HOME/src/moshpit/book" --full --dry-run
```

Publish only after the plan resolves the full edition, stable PDF/EPUB/HTML,
cover, headboard, source URL, and the `technology` shelf correctly.

