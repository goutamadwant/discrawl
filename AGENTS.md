# Discrawl checkout ownership

Use one canonical development checkout for this repository and use branches for
task isolation. Read [the checkout workflow](docs/guides/development-checkout.md)
before preparing an isolated build, another checkout, or end-of-task cleanup.

- Create another worktree only for an explicit user request. Record its owner,
  purpose, path, retained work, and end-of-task cleanup obligation.
- Preserve unrelated edits, held capture preparation, `tempplan.md`, and frozen
  evidence. Use a temporary Git index when a task-only commit must leave the
  active checkout and its real index unchanged.
- Place new build exports, deployment artifacts, evidence, and rollback custody
  in task-specific application storage outside the development-projects tree.
  Keep existing pinned runtime paths stable until their owner authorizes a
  separate deployment change.
- At closeout, inspect `git worktree list --porcelain`. Remove each completed
  exception through Git after verifying custody and live references, or record
  its named owner and concrete reason to remain.
- Treat native services, credentials, archives, WAL/SHM, cursors, and explicit
  capture/cleanup holds as separately owned operational state.
