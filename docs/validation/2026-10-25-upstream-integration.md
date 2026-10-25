# Upstream integration

On 2026-10-25 upstream `376e931` was merged after local setup commit
`0330d02`. Nothing was pushed or published.

Upstream added model-use documentation, reopening an existing create project
(`b12bfd1`), and Vision accurate-to-fast text-reader recovery (`376e931`).
The merge preserves those changes alongside guarded creation resume and the
shared setup checks.

Ordinary `create` opens an existing project and never demonstrates over its
story. Without a successful run it can preview the saved story. A creation
paused before demonstration still requires explicit Continue creation or
`--resume`. Legacy projects without creation metadata receive a repeat-create
command instead of an invalid resume instruction. Completed creation keeps its
existing run.

Setup checks and doctor now retain upstream's Vision reader detection, identify
the fast reader when used, and report failure when neither reader works. Text
recognition probes preserve the configured backend. Scan reports retain the
upstream `text_reader` field, with face/person requests separate from text.

Verification: 251 fast tests passed, with 52 browser tests deselected. The
focused setup browser trial passed through missing-tool recovery into a real
synthetic notes preview. Regressions cover both Vision reader outcomes and
existing projects without overwriting or re-recording their story. These checks
are not owner media acceptance or independent usability testing.
