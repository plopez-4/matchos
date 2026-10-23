# Retired scenario-review checkout

Archived 23 October 2026 before removing the old linked checkout.

The Git branch `fix/scenario-review` is retained in the active MatchOS repository at commit `dee269fbfd6350aaa127271f0011d0a455239091`. Its six commits outside the current branch's history remain reachable through that branch.

`review-vite.config.js` is an exact copy of the only untracked source/configuration file in the old checkout. It pointed the temporary review frontend at backend port 8002. Ignored files were limited to reproducible frontend dependencies and build output; those need not be archived.

To recreate the old checkout from the active repository, run:

```cmd
git worktree add "..\matchos-scenarios-fixes" fix/scenario-review
```

If needed, copy the saved configuration into the recreated checkout's `frontend/.review-vite.config.js`. It is not used by the current app.

The old node_modules directory was a junction into the active checkout. Only that link was detached before Git removal; the active dependency directory and its React package were preserved and verified.
