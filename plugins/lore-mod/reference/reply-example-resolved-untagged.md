Thanks for the clear repro. I confirmed the phantom `D` entries are gone on the current main.

## Fix

Commit 929fa91. The fix is @lehuan5062's PR #104, which was folded into, and landed with, PR #89. A reverted uncommitted directory is now discarded as a whole on the next `status --scan` instead of leaving delete entries for files that were never committed. Not in a tagged release yet; it will ship with the next release after v0.9.0.

## Verified on main (34238aa, `lore 0.9.1-nightly+0`)

- Platform: macOS 26.6, arm64
- Repository: created with `--offline`, one committed file

```
mkdir newfolder
echo one > newfolder/a.txt
echo two > newfolder/b.txt
lore status --scan
```

Output:

```
On branch main revision 1 -> cb780c78...
Untracked files:
A newfolder/
A newfolder/b.txt
A newfolder/a.txt
Tracked changes: 3 added
```

```
rm -rf newfolder
lore status --scan
```

Output:

```
On branch main revision 1 -> cb780c78...
No tracked changes
```

The entries clear on the first scan after the delete; `--reset` is no longer needed.

Closing as fixed.
