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
claude --bg --remote-control --resume <session-id>
```

I.e. a background session on the remote, running in a daemon.

Note: Be signed in to Claude on the remote

## Known limits

Staged and unstaged changes arrive merged, because the patch is a single `git diff HEAD`. Ignored
files do not travel at all — `.venv`, `node_modules`, build output, `.env` are yours to recreate.
And both machines end up holding the same session id, so once you have thrown, only one side can be
typed into; they do not merge back.

## License

No licenses, no masters.
