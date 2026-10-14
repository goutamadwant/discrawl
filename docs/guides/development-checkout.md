# One canonical checkout

Use one canonical Discrawl development checkout per machine. Use branches for
ordinary tasks. An additional worktree requires an explicit user request and a
record naming its owner, purpose, path, and cleanup obligation. Retain that record
with task evidence outside the development-projects tree.

## Work with an occupied checkout

Inspect the current branch, index, working tree, and existing holds before edits.
Preserve unrelated work in place. When held work prevents switching branches,
use a temporary `GIT_INDEX_FILE` to prepare a commit containing only the authorized
paths on the intended base. Retain the resulting commit on a named branch and
deliver it through the repository's normal review and push gates. Preserve the
real index and active branch. Document where the prepared commit lives.

For an isolated build, export an exact reviewed commit with `git archive` into a
task-specific directory under native application storage, outside Projects.
Record the commit and artifact hashes. An exported source directory is a build
input, not another development checkout; remove or archive it at task closeout
according to its evidence/rollback obligations. A helper that creates a worktree
is subject to the same explicit-request rule, including temporary worktrees.

Place new installed artifacts, build output, receipts, and rollback custody
outside Projects. Existing pinned installations keep their current paths until
their owner authorizes a separate deployment change. Source cleanup preserves
those installations and their service configuration.

## Close each exception

1. Inspect `git worktree list --porcelain`, the Git common directory, locks,
   branches, detached heads, local-only commits, and all dirty, untracked, and
   ignored contents. Resolve path aliases before classifying a directory.
2. Check active task/process working directories and runtime, service, skill,
   and dependency references. Retain the canonical checkout and Git common
   storage. Retain a secondary tree while a live dependency or hold requires it.
3. Preserve useful changes, unique commits, ignored evidence, and rollback
   material in private custody outside Projects. Verify archive contents and
   hashes, and verify the Git bundle or other retained refs before retirement.
4. Use `git worktree remove` for a positively stale tree. Investigate a refusal
   and preserve the reported work or lock before choosing a supported resolution.
   Keep branches and commit history unless their removal is separately authorized.
5. Recheck the canonical source/index/refs, installed identity, and ordinary
   native health using bounded local metadata. Record exact removed/retained
   paths, custody hashes, and each remaining exception's owner and reason.

End every task with this inventory, including tasks that created no worktree.
Use explicit owner cleanup rather than a destructive background cleanup job.
Report relocated/archive bytes separately from physically reclaimed disk space.
Keep native data, credentials, schedules, and capture/cleanup holds under their
existing ownership throughout.
