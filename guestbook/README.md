# Leave a Trace · Guestbook

An original, lightweight interactive guestbook for **Shuofei Zan's design and research portfolio**. The visual concept combines sky-green ceramic glaze, floating paper messages, and a tactile note wall. It is intentionally a separate optional component and does not change the research/CV files in this repository.

## References and original design

Inspiration: [GitComment](https://github.com/LISK819129/GitComment) (GitHub-native comments), [JamesIves guestbook](https://github.com/JamesIves/JamesIves) (README guestbook), [Scrapbook](https://github.com/OarisaR/Scrapbook) (movable tactile notes), [DeskFolio](https://github.com/mortspace/Deskfolio) (playful interaction). No assets or code are copied from these projects; the guestbook uses its own HTML, CSS and JavaScript.

## How the data actually works

- **Read:** the browser retrieves the most recent 100 **open GitHub Issues** using the public GitHub REST API. Only issues whose titles begin with `[Guestbook]` and whose body contains the expected `### Your note` field are displayed. Up to 60 matching notes are shown. New notes may not appear immediately due to GitHub API caching.
- **Write:** clicking "Write a little note" opens `.github/ISSUE_TEMPLATE/guestbook.yml` in GitHub; the visitor signs in and submits a public Issue. There is **no anonymous or inline message submission**, no server, no secret, and no additional authentication token.
- **Moderation:** close a GitHub Issue to hide it from the web wall (it will still exist publicly as a closed Issue); re-open it to show it again. Users who can edit their Issues can alter their messages; review the wall periodically.
- **Security:** messages are inserted using `textContent`, never `innerHTML`; unrelated Issues and Pull Requests are filtered out. The external avatar URL is restricted to GitHub's avatar host. Links open with `noopener noreferrer`.
- **Limitations:** unauthenticated GitHub REST API requests can be rate-limited; in that case the site displays a retry-friendly error state. The first page of 100 issues is scanned; old entries may fall outside this page if the repository receives many other Issues.

## Publish on GitHub Pages

1. Merge the guestbook pull request into the repository's default `main` branch.
2. In repository **Settings → Pages**, set **Build and deployment → Deploy from a branch → `main` → `/(root)`**, then Save. (If your repo already uses a different Pages publishing strategy, integrate the guestbook directory into that strategy instead of overwriting it.)
3. The expected address, **only after publishing is configured**, is: `https://adele0302.github.io/shuofei-zan-design-portfolio/guestbook/`.
4. The standard repository README links to the guestbook. The issue form works only after the template file exists on the default branch and Issues are enabled in repository settings.

The demo-only view is `guestbook/index.html?demo=1` (or append `?demo=1` to the hosted URL). Demo prompts are **labeled and not actual visitor messages**. It is used only for checking layouts before the first real post.

## Local preview

Because API requests may fail on `file://` pages, use a local static server:

```bash
python -m http.server 8000
# http://localhost:8000/guestbook/?demo=1
```

No npm installation or build step is required. The page is responsive and honors `prefers-reduced-motion`.
