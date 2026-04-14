# Git Branching Workflow for NOVUS Library

## Branch Structure

```
main (production-ready, stable code)
  │
  └── develop (active development, integration branch)
        │
        ├── feature/xxx  (new features)
        ├── fix/xxx      (bug fixes)
        └── ui/xxx       (UI improvements)
```

## Branches Explained

| Branch      | Purpose                                 | Merges Into |
| ----------- | --------------------------------------- | ----------- |
| `main`      | Production-ready code, always stable    | -           |
| `develop`   | Active development, integration testing | `main`      |
| `feature/*` | New features                            | `develop`   |
| `fix/*`     | Bug fixes                               | `develop`   |
| `ui/*`      | UI/design changes                       | `develop`   |

---

## Daily Workflow

### Starting a New Feature

```bash
# Make sure you're on develop and it's up to date
git checkout develop
git pull origin develop

# Create a new feature branch
git checkout -b feature/my-new-feature

# Work on your feature...
# Make commits as you go
git add -A
git commit -m "feat: Add awesome feature"
```

### Finishing a Feature

```bash
# Push your feature branch
git push origin feature/my-new-feature

# Switch to develop and merge
git checkout develop
git merge feature/my-new-feature
git push origin develop

# Delete the feature branch (optional)
git branch -d feature/my-new-feature
```

### Releasing to Production

```bash
# When develop is stable and tested
git checkout main
git merge develop
git push origin main

# Tag the release (optional)
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

---

## Quick Commands Reference

| Action              | Command                          |
| ------------------- | -------------------------------- |
| See all branches    | `git branch -a`                  |
| Create new branch   | `git checkout -b branch-name`    |
| Switch branches     | `git checkout branch-name`       |
| Merge branch        | `git merge branch-name`          |
| Delete local branch | `git branch -d branch-name`      |
| Push new branch     | `git push -u origin branch-name` |

---

## Naming Conventions

- **Features**: `feature/user-authentication`, `feature/payment-gateway`
- **Bug Fixes**: `fix/login-error`, `fix/image-upload-crash`
- **UI Changes**: `ui/dark-mode`, `ui/responsive-navbar`
- **Hotfixes**: `hotfix/critical-security-patch`

---

## Current Branches

- `main` - Production (stable)
- `develop` - Development (active work)
- `feature/user-dashboard` - Existing feature branch
