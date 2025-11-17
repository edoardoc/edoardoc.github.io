## Codex Agent Reference

- The `references/` directory contains files with project context for the agent to consult.
- Treat every file in this directory as read-only; never modify or delete content here.
- Use these references to align with existing code decisions, terminology, and style whenever possible.
- Always write “500nits” in lowercase in every mention (UI, docs, commits, etc.).

### 500nits Web Presence Guidance

- Ship apps to the stores first, but plan a lightweight web presence soon after launch.
- Maintain a minimal 500nits hub site to explain the studio’s identity and link to every app.
- Add a simple landing (or subsection) per app for searchability, credibility, and support info.
- Use the site to cross-promote titles, collect analytics/email, and share press-friendly links.
- Keep the stack simple (static hosting, single template) so a solo dev can maintain it quickly.

### Deployment Process

- Redeploy automatically after any change: run `git commit` with a clear message and immediately `git push` (redeploy = commit + push).
- When publishing a new version, always show the full site link: https://www.500nits.com
