# trebuchet

A Claude Code skill for stopping work on one machine and picking the same conversation up on
another. You are mid-session on a laptop, the job wants a GPU or a fast disk or a network you do not
have, and starting over on the VM means re-explaining everything you just explained.

Not published yet.

## `/trebuchet`

```
/trebuchet <ssh host> [remote repo path]
```

Carries two things to the VM and starts Claude there:

- **The conversation.** The session transcript out of `~/.claude/projects/`, with local paths
  rewritten to their remote equivalents so the history's file references still resolve.
- **The code.** The commit — over `git fetch` when it is already on origin, over `git bundle` when
  it is not — plus tracked changes as a patch and untracked files over rsync.

Then it creates a Herdr workspace on the far side and starts `claude --resume` in its root pane, so
the session is waiting in a real terminal you can attach to from the Herdr machine switcher.

Nothing local is destroyed. The transcript is copied, the repo is untouched, and a throw that fails
halfway costs an unused workspace on the VM.

## What it will not do

- **Install Herdr on the VM.** `herdr machine add` does that, and it needs an interactive terminal
  for its approval prompts. The skill checks for a running remote server and stops if there is none.
- **Answer the folder-trust prompt.** A first throw to a directory Claude has not seen leaves the
  agent blocked on it. The skill reports that and leaves the decision to you.
- **Reset over uncommitted work in the remote checkout.** It shows you what is there and stops.
- **Push to origin without asking.** Unpushed commits go across as a bundle by default.

## Known limits

Staged and unstaged changes arrive merged, because the patch is a single `git diff HEAD`. Ignored
files do not travel at all — `.venv`, `node_modules`, build output, `.env` are yours to recreate.
And both machines end up holding the same session id, so once you have thrown, only one side can be
typed into; they do not merge back.

## License

MIT
