Thanks for the write-up. Lore actually does have this and I confirmed the ignore file functionality on the current release.

But the only places it is described today are the system design doc and the glossary (links below). Nothing in the how-to guides, the CLI reference, or the quickstart mentions it.

## Where it is documented

- Ignore files: [System design, 12.3](https://epicgames.github.io/lore/explanation/system-design/#123-ignore-files-outbound-filtering). A gitignore-style `.loreignore` at the repository root. "Paths matching ignore rules are not staged, not committed, and not reported in status. Build artifacts, editor temporary files, machine-local configuration: all typical inhabitants."
- View filters: [System design, 12.4](https://epicgames.github.io/lore/explanation/system-design/#124-filtermode-which-filter-applies-when). A view limits which paths an instance sees at all, on disk and in the committed revision. For staging and status "the view limits what the operation sees on disk; the ignore file then further excludes things the user has declared shouldn't be staged." So if whole subtrees should never be part of this working copy, a view does that; `.loreignore` handles the locally generated junk inside what you do see.
- Glossary entries for both: [Ignore file](https://epicgames.github.io/lore/glossary/#ignore-file) and [View filter](https://epicgames.github.io/lore/glossary/#view-filter).

## Verified on v0.9.0 (`lore 0.9.0+783`)

- Platform: macOS 26.6, arm64
- Repository: created with `--offline`; tree of `Source/`, `Config/`, `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`, and a `Scratch.tmp`

Without an ignore file, `lore status --scan` lists everything, 17 entries. With this `.loreignore` at the root:

```
Binaries/
Intermediate/
Saved/
DerivedDataCache/
*.tmp
```

Output of `lore status --scan`:

```
Untracked files:
A Config/
A Source/
A .loreignore
A Config/DefaultGame.ini
A Source/Main.cpp
Tracked changes: 5 added
```

`lore stage --scan` then stages those five and nothing from the artifact folders.

Given the obvious documentation gap, I have retitled this and relabeled it as documentation, and I am keeping it open to cover how-tos on ignore files and view filters. 

That being said, the `--no-ignore` flag and a `config.toml` section you mention do not exist today. So if the current `.loreignore` functionality does not cover your case once you have tried it, let me know and we’ll get an enhancement request raised to track that as well. 
