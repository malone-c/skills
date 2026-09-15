# trebuchet

Move your Claude Code session and relevant files onto another machine, and pick up where you left off.

## `/trebuchet`

```
/trebuchet <ssh host> [remote repo path]
```

Copies the session transcript out of `~/.claude/projects/`, with local paths rewritten to remote equivalents.

Copies code with `git fetch` or `git bundle` depending on whether it's already on origin + tracked changes as a patch + untracked files over `rsync`.

Then resumes the session on the far side with native Claude Code:

```
claude --bg --remote-control --fork-session --resume <session-id>
```

I.e. a background session on the remote, running in a daemon. `--fork-session` gives the far side a
new session id carrying the full history, so the VM and your laptop don't share an id and step on
each other.

Note: Be signed in to Claude on the remote

## Known limits

Staged and unstaged changes arrive merged, because the patch is a single `git diff HEAD`. Ignored
files do not travel at all — `.venv`, `node_modules`, build output, `.env` are yours to recreate.
The throw forks: the VM session shares history up to the throw and diverges after it, so the two
never merge back.

## License

No licenses, no masters.
