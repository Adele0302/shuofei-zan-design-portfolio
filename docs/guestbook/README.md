# Pixel Cat Guestbook — one-page website

This is Shuofei Zan's public guestbook, located at `docs/guestbook/index.html`.

The guestbook has a single page with original pixel-art cat mascots, a short name-and-message form, and a wall of public visitor messages. It is intentionally minimal: no cat selection, moods, petting minigames, multiple content pages, or external database.

## Publish on GitHub Pages

- Repository: `Adele0302/shuofei-zan-design-portfolio`
- Settings → Pages → Deploy from a branch → `main` and `/docs`
- Guestbook URL: https://adele0302.github.io/shuofei-zan-design-portfolio/guestbook/

The portfolio landing page at `docs/index.html` remains intact and links to the guestbook.

## Leave a message

1. Enter an optional name and a message (up to 280 characters).
2. Click **SEND LETTER**.
3. A new browser tab opens a **prefilled GitHub Issue**. Sign in to GitHub and submit the Issue to publish; completing this step is required. The form alone never uploads data.
4. Return to the guestbook and click **Refresh** to display the new note.

### Public data and moderation

Notes are public GitHub Issues. A visitor's submitted name, message, timestamp, and GitHub identity are public on GitHub. The website makes an unauthenticated call to GitHub's Issues API and displays public, open guestbook Issues. Close an unwanted Issue to hide it from the website; reopening reveals it again. This is not a moderation-before-display system.

### Compatibility and implementation

- New notes: Issue title starts with `[Pixel Catbook]` and body contains `zan-pixel-catbook:v3`.
- Older cat-book `zan-catbook:v2` and glaze guestbook `zan-guestbook:v1` Issues continue to display.
- Visitors' text is inserted with `textContent`; no user-supplied HTML is evaluated.
- The cats are original inline SVG pixel art rendered with integer-coordinate rectangles and `shape-rendering: crispEdges`.
- No Google Fonts, image CDNs, API tokens, cookies, local storage, analytics, or tracking are used.
- The GitHub API's unauthenticated rate limit applies. The feed reads the latest 100 open Issues and shows up to 24 matching messages; heavy usage would need pagination or an alternative backend.
- Keyboard interaction and `prefers-reduced-motion` are supported. The form uses a native GET submission to GitHub in a new tab, not a popup API.

If Github Pages has not yet completed publishing, source code can be viewed in `docs/guestbook/index.html`.
