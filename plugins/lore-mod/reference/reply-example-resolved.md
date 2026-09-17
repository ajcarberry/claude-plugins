Thanks for the detailed report. I reproduced your panic on `0.8.3+201` (same trace, `FragmentStats::complete` -> `capacity overflow`) and confirmed it is fixed in the current release.

## Fix

Commit 9e3ff4c, shipped in v0.8.4. The `--stats` histogram divided by the largest bucket count, which was always zero, so the bar length overflowed on allocation. The fix guards that and wires up the fragment write events, so the stats now show real numbers.

## Verified on 0.9.0+783

- Platform: macOS 26.6, arm64
- Server: `loreserver 0.9.0`, zero-config, local

```
lore stage module1.cpp module2.cpp module3.cpp module4.cpp
lore commit "Update modules

Second line of the message, as in the report." --stats
```

Output, exit code 0:

```
Fragmenting files and updating tree hashes
Committing staged changes
Committed 1/1 directories, 4/4 files, 299.06 KiB/299.06 KiB (4 modified, 0 deleted)
Stored history for 4 nodes
Commit self
  Written fragments         : 6
  Written raw bytes         : 306433
  Written payload bytes     : 306433 (0% compression)
  Deduplicated fragments    : 0 (0%)
  Deduplicated raw bytes    : 0 (0%)
  Deduplicated payload bytes: 0 (0%)
  Written final bytes:      : 306433 (100%)
  Written list fragments    : 0
  Written state fragments   : 0
Chunk size distribution:
     0 -   4096: ******************************           (2     ) 33.33%
 73728 -  77824: **************************************** (4     ) 66.67%
Repository: 01a0aad8e3007411ab0c968165cdbcd7
Revision  : 2
Signature : f3229cb3e9bc0660b32534db4c3f2dfb6ca9d97cefa77f75027b06e5713db939
Parent    : dabfe687a73280a3ffdde8fd8e4748bbab103b616759562b8447f108a1bad2e8
Branch    : e726318bbc3fd75ac8733a7e030cc35b
Date      : Wed, 16 Sep 2026 15:32:16 +0000
    Update modules

    Second line of the message, as in the report.
Commit succeeded
```

I could not reproduce the `Resetting corrupt immutable bucket` warnings on macOS. They may be Windows-specific, or a side effect of where the abort landed on your run. If they are still present on 0.9.0, please open a separate issue with the log; that warning comes from a different code path than this panic.

Closing as fixed.