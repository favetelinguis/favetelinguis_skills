## Task files

Task files live outside the repository, never in it. Find the tasks directory and this worktree with:

```bash
common=$(git rev-parse --path-format=absolute --git-common-dir)
case "$(basename "$common")" in .git|.bare) common=$(dirname "$common") ;; esac
echo "tasks directory: ${XDG_STATE_HOME:-$HOME/.local/state}/agent-workflow/$(basename "$common" .git)"
echo "this worktree:   $(basename "$(git rev-parse --show-toplevel)") (branch $(git branch --show-current))"
```

All worktrees of a repository share one tasks directory. Outside a git repository, ask me where the task files go.

- One file per goal: `<NNN>-<slug>.md`, numbered with the next free three-digit number.
- A task's status is the bracket at the end of its heading: `[todo]` (requirements written), `[ready]` (sketch written, awaiting implementation), `[done]` (implemented and reviewed).
- A task belongs to the worktree on its `**Worktree:**` line. {{CMD:design}} writes that line when it takes the task up; {{CMD:impl}} and {{CMD:impl-review}} work only on tasks that belong to this worktree.
