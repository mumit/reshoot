# Portable workshop distribution

After the owner pushed the workshop source, the next preparation step was a
portable download and upload descriptions. No GitHub release, tag or video
upload was created.

`examples/tutorial/package.py --attempt ATTEMPT` prepares a new distribution
directory. It checks the two MP4 hashes against the completed audit before
copying them. The ZIP includes the videos, SRT/VTT captions, chapter JSON,
timestamped transcript, preview images, a portable chapter player, viewing
instructions and a manifest. Raw captures, model weights and internal review
sheets are excluded. Draft release notes, upload descriptions and a ZIP
checksum remain beside the archive.

The final artifact is under ignored
`takes/tutorial/attempt-8e8e4eff040e/distribution-ready/`:

- `reshoot-workshop-heart.zip`: 32,750,228 bytes, 14 files.
- SHA256: `140ab6b09a90b630db7feed41f8b2a60c355e21f2875ca1bea1211b1b5d064f3`.
- Both upload descriptions contain chapter/navigation timestamps and source
  links pinned to the publicly pushed `24be94a` commit.

## Verification

- Three packaging tests and two documentation tests passed. The tests cover
  unchanged video bytes, manifest hashes, relative archive paths, checksums
  and rejection of changed or missing exports before creating a destination.
- Every ZIP member passed its integrity check and matched the manifest hash.
- A real headless Chrome page loaded both videos, the two preview images and
  the caption track. All 11 chapter controls were present; seeking decoded a
  frame at the selected workshop chapter. The final page was captured under
  the ignored distribution directory. Only synthetic notes footage was used.
- The public follow-along guide and rebuild README were fetched from GitHub
  at `24be94a` and matched `git show` byte for byte.
- `git diff --check` passed.

The rebuild README now leads with a fresh recording, explicitly identifies
the audit step that generates the transcript, and documents packaging.
Publishing drafts note that standalone video releases should use a
`workshop-*` tag. Existing `v*` tags trigger the repository's Python package
release workflow.

The source media remains pending complete owner review. Preparing the bundle
does not accept the recordings or authorize publication.
