# Glaze Notes — interactive academic guestbook

A lightweight, porcelain-inspired guestbook for Shuofei Zan's public design research portfolio. Implemented as a static HTML/CSS/JavaScript page with GitHub Issues as the message store. No secrets, databases, tracking scripts, or third-party commenting service are needed.

## Publish to GitHub Pages

1. Merge the guestbook feature pull request into `main`.
2. Open repository **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**.
4. Select **main** and the **/docs** directory, then **Save**.
5. Once GitHub finishes publishing, open:

   https://adele0302.github.io/shuofei-zan-design-portfolio/guestbook/

The `docs/index.html` page is a simple research-portfolio gateway, while `docs/guestbook/index.html` is the actual guestbook.

## How guestbook notes work

- Visitors choose one of four glaze colors, optionally add a name and write a message (up to 280 characters).
- Clicking **Sign the guestbook** opens a new GitHub Issue with prefilled content.
- **The visitor must be signed in to GitHub and explicitly submit the Issue.** Filling the form alone does not publish anything.
- The site loads public **open** Issues from the repository and displays only those beginning with `[Guestbook] ` and containing the versioned guestbook marker.
- Notes are text-only and rendered with `textContent`, not HTML; this prevents arbitrary user content from becoming executable page markup.
- A signed-in repository maintainer can hide an unwanted note from the site by **closing its Issue**. Reopening it makes the note visible again.
- The page displays the most recent 24 matching entries from the latest 100 open Issues; large-volume use would require pagination. Anonymous submissions without GitHub sign-in are not supported.

## Practical limitations

This is a public **Issue-backed** guestbook, not a private inbox. Usernames, the Issue body, and the publication timestamp are public on GitHub. Notes generally show when refreshed after GitHub has accepted a new Issue. The unauthenticated GitHub REST API has rate limits, and visitors may occasionally see an availability warning until the limit resets. The site does not add a moderation queue; public open messages become visible automatically. For an approval-before-display workflow, a separate reviewed content feed would be needed.

The visual style is original; the GitHub Issues storage approach draws on [utterances](https://github.com/utterance/utterances). [giscus](https://github.com/giscus/giscus) is an alternative for threaded Discussion comments and reactions but requires enabling GitHub Discussions and installing the giscus app.

## Files

- `docs/index.html` — compact portfolio landing page with a guestbook entry.
- `docs/guestbook/index.html` — responsive, accessible static guestbook.
- `docs/guestbook/README.md` — deployment and moderation instructions.

Author: Shuofei Zan.