# The Cat Mail Club — interactive cat guestbook

A playful, accessible cat-themed guestbook for Shuofei Zan's design and research portfolio, with original inline SVG cat illustrations and GitHub Issues as the public message store.

## Publish on GitHub Pages

This repository currently stores the static website in `docs/`. To publish:

1. Open **Settings → Pages** in `Adele0302/shuofei-zan-design-portfolio`.
2. Select **Deploy from a branch**.
3. Select branch **main** and folder **/docs**, then save.
4. After the Pages deployment succeeds, the URL is:

   https://adele0302.github.io/shuofei-zan-design-portfolio/guestbook/

The welcome page lives at `docs/index.html`. This guestbook is at `docs/guestbook/index.html`. The site's Figma portfolio and research links are unchanged.

## Visitor workflow

1. Choose one of six original cat coats: ginger, tuxedo, calico, silver, cream or lilac.
2. Choose a mood: happy, sleepy or curious. See a live illustrated cat preview.
3. Add an optional visitor name and cat name, plus a message (up to 280 characters).
4. Click **Send my cat-letter**. The browser opens a **prefilled new GitHub Issue**. Visitors must sign in to GitHub and **explicitly publish** their Issue; no message is submitted by the static website.
5. Return to the wall and refresh. Each open, matching Issue appears as a cat card. Opening a card displays a readable letter, public author attribution, date and Issue link.

A visit to the website does not require a GitHub account. **Posting does require a GitHub account.** Comments and names are publicly visible on GitHub.

## Moderation and compatibility

- The live wall displays only matching, currently **open** Issues. To hide a public letter, close the corresponding Issue. This is not an approval-before-display queue.
- New entries use an explicit `[Catbook]` Issue title plus a `zan-catbook:v2` comment marker and structured text fields.
- Legacy `[Guestbook]` entries marked `zan-guestbook:v1` remain displayable as cats, so upgrading does not silently discard older notes.
- The list uses the latest 100 open Issues from GitHub's public API, and shows up to 30 matching cats. It would require pagination for heavy traffic.
- All visitor-controlled strings are rendered with `textContent`. SVG palettes and moods are selected from fixed whitelists.
- The **pet the cat** animation is local-only and not persisted. No audio auto-play, visitor tracking, private tokens or external image services.
- The design respects `prefers-reduced-motion`, supports keyboard navigation, and opens messages with the native dialog element.

## Design inspiration and independence

The illustrative cat art and page layout are original SVG/CSS drawn for this project; no artwork or code is copied from the references. Useful patterns:

- [homepage-cat](https://github.com/AsleepX/homepage-cat): lightweight draggable SVG character and reduced-motion considerations.
- [Interactive-Cat-Pet-App](https://github.com/sulthonkk/Interactive-Cat-Pet-App): cat click feedback.
- [utterances](https://github.com/utterance/utterances): GitHub Issues-backed public comments.
- [giscus](https://github.com/giscus/giscus): alternative based on GitHub Discussions, should threading and reactions be required.

## Limitations

GitHub API rate limits may temporarily prevent unauthenticated reads, in which case visitors can refresh later. Links open in a separate tab, and publishing is completed on GitHub (not inline). Malicious content is displayed as plain text, but unwanted legitimate messages can still appear until manually closed. For anonymous writing, an external hosted forms service and abuse-prevention system would be necessary.

This static site has no backend and can run on GitHub Pages without build tooling.