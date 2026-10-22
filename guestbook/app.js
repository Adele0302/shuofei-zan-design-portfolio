/* Leave a Trace — no credentials and no external runtime dependencies. */
(() => {
  'use strict';
  const REPO = 'Adele0302/shuofei-zan-design-portfolio';
  const API = `https://api.github.com/repos/${REPO}/issues?state=open&per_page=100&sort=created&direction=desc`;
  const ISSUE_PREFIX = '[Guestbook]';
  const board = document.querySelector('#note-board');
  const count = document.querySelector('#note-count');
  const filters = [...document.querySelectorAll('[data-filter]')];
  const shuffleButton = document.querySelector('#shuffle-button');
  const DEMO = new URLSearchParams(window.location.search).get('demo') === '1';
  const DEMO_NOTES = [
    { id: 1, message: 'What is one material detail that changed the way you see an object?', theme: 'Question', author: 'Sample prompt', date: '', url: '', demo: true },
    { id: 2, message: 'Interesting ideas often start with a conversation between unexpected disciplines.', theme: 'Thought', author: 'Sample prompt', date: '', url: '', demo: true },
    { id: 3, message: 'A little hello from the other side of the screen. ✳', theme: 'Hello', author: 'Sample prompt', date: '', url: '', demo: true },
    { id: 4, message: 'How do we make computational tools more understandable to the people using them?', theme: 'Question', author: 'Sample prompt', date: '', url: '', demo: true },
    { id: 5, message: 'A beautifully simple idea can be a powerful research question.', theme: 'Thought', author: 'Sample prompt', date: '', url: '', demo: true },
    { id: 6, message: 'Leave a trace; begin a conversation.', theme: 'Hello', author: 'Sample prompt', date: '', url: '', demo: true }
  ];
  let notes = [];
  let currentFilter = 'all';
  let displayOrder = [];

  function parseBody(body = '') {
    // GitHub's Issue Forms convert each field into a Markdown heading.
    const section = (name) => {
      const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const match = body.match(new RegExp(`(?:^|\\n)### ${escaped}\\s*\\n([\\s\\S]*?)(?=\\n### |$)`, 'i'));
      return match ? match[1].trim() : '';
    };
    const rawTheme = section('Note type');
    const rawNote = section('Your note');
    const theme = /question/i.test(rawTheme) ? 'Question' : /thought/i.test(rawTheme) ? 'Thought' : /hello/i.test(rawTheme) ? 'Hello' : 'Other';
    return { theme, message: rawNote.replace(/\r/g, '').slice(0, 450).trim() };
  }

  function isValidIssue(issue) {
    // Do not expose unrelated repository Issues or pull requests.
    return issue && !issue.pull_request && typeof issue.title === 'string' && issue.title.startsWith(ISSUE_PREFIX);
  }

  function fromIssue(issue) {
    const parsed = parseBody(issue.body || '');
    if (!parsed.message) return null;
    const author = (issue.user && issue.user.login) || 'GitHub visitor';
    return {
      id: issue.number, theme: parsed.theme, message: parsed.message,
      author, date: issue.created_at, url: issue.html_url,
      avatar: issue.user && /^https:\/\/avatars\.githubusercontent\.com\//.test(issue.user.avatar_url || '') ? issue.user.avatar_url : ''
    };
  }

  function formatDate(value) {
    if (!value) return '';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? '' : new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(date);
  }

  function empty(kind) {
    board.replaceChildren();
    const wrap = document.createElement('div'); wrap.className = 'empty-state';
    const icon = document.createElement('span'); icon.className = 'empty-icon'; icon.setAttribute('aria-hidden', 'true'); icon.textContent = '✳';
    const title = document.createElement('h3');
    const body = document.createElement('p');
    const link = document.createElement('a'); link.target = '_blank'; link.rel = 'noopener noreferrer';
    link.href = `https://github.com/${REPO}/issues/new?template=guestbook.yml`;
    if (kind === 'error') {
      title.textContent = 'The wall is taking a moment.';
      body.textContent = 'Live notes could not be loaded right now. You can still leave a message through GitHub.';
      link.textContent = 'Open the guestbook on GitHub ↗';
    } else if (kind === 'filtered') {
      title.textContent = 'A little quiet in here.';
      body.textContent = 'No notes of this kind yet. Maybe yours can be the first.';
      link.textContent = 'Be the first ↗';
    } else {
      title.textContent = 'The first trace could be yours.';
      body.textContent = 'An empty wall is full of possibility. Drop a hello, a research question, or something worth thinking about.';
      link.textContent = 'Leave the first note ↗';
    }
    wrap.append(icon, title, body, link); board.append(wrap);
  }

  function buildNote(note, index) {
    const card = document.createElement('a');
    card.className = 'note-card'; card.dataset.theme = note.theme;
    card.style.setProperty('--rot', `${[-1.6, 1.1, -.8, 1.8, -1.2, .7][index % 6]}deg`);
    if (note.demo) {
      card.href = `https://github.com/${REPO}/issues/new?template=guestbook.yml`;
    } else {
      card.href = note.url;
    }
    card.rel = 'noopener noreferrer'; card.target = '_blank';
    card.setAttribute('aria-label', `${note.theme} note by ${note.author}: ${note.message.slice(0,100)}`);
    const kind = document.createElement('span'); kind.className = 'note-kind';
    kind.textContent = `${({Thought:'✳',Question:'?',Hello:'♡'})[note.theme] || '·'} ${note.theme} ${note.demo ? '· demo' : ''}`;
    const text = document.createElement('p'); text.className = 'note-text'; text.textContent = note.message;
    const meta = document.createElement('span'); meta.className = 'note-meta';
    if (note.avatar) {
      const img = document.createElement('img'); img.src = note.avatar; img.alt = '';
      img.width = 23; img.height = 23; img.loading = 'lazy'; img.referrerPolicy = 'no-referrer'; img.className = 'note-avatar'; meta.append(img);
    } else {
      const avatar = document.createElement('span'); avatar.className = 'note-avatar'; avatar.textContent = '◦'; avatar.setAttribute('aria-hidden', 'true');
      avatar.style.display = 'grid'; avatar.style.placeItems = 'center'; meta.append(avatar);
    }
    const who = document.createElement('span'); who.className = 'note-person'; who.textContent = `@${note.author}`;
    const date = document.createElement('time'); date.className = 'note-date'; date.textContent = formatDate(note.date);
    if (note.date) date.dateTime = note.date;
    meta.append(who, date); card.append(kind, text, meta);
    return card;
  }

  function render() {
    board.setAttribute('aria-busy', 'false');
    const selected = displayOrder.map(i => notes[i]).filter(n => currentFilter === 'all' || n.theme === currentFilter);
    if (!selected.length) { empty(notes.length ? 'filtered' : 'empty'); return; }
    const fragment = document.createDocumentFragment();
    if (DEMO) {
      const warning = document.createElement('p'); warning.className = 'demo-banner'; warning.textContent = 'Preview mode · these are example prompts, not visitor messages'; fragment.append(warning);
    }
    selected.forEach((note, idx) => fragment.append(buildNote(note, idx)));
    board.replaceChildren(fragment);
  }

  for (const btn of filters) btn.addEventListener('click', () => {
    currentFilter = btn.dataset.filter;
    for (const item of filters) {
      const active = item === btn; item.classList.toggle('is-active', active); item.setAttribute('aria-pressed', String(active));
    }
    render();
  });
  shuffleButton.addEventListener('click', () => {
    // Fisher–Yates: layout changes locally; never writes to GitHub.
    for (let i = displayOrder.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [displayOrder[i], displayOrder[j]] = [displayOrder[j], displayOrder[i]];
    }
    render();
  });
  document.querySelector('#year').textContent = String(new Date().getFullYear());

  async function start() {
    if (DEMO) {
      notes = DEMO_NOTES; count.textContent = '06'; displayOrder = notes.map((_, i) => i); render(); return;
    }
    try {
      const response = await fetch(API, { headers: { Accept: 'application/vnd.github+json' } });
      if (!response.ok) throw new Error(`GitHub API HTTP ${response.status}`);
      const issues = await response.json();
      if (!Array.isArray(issues)) throw new Error('Unexpected API response');
      notes = issues.filter(isValidIssue).map(fromIssue).filter(Boolean).slice(0, 60);
      count.textContent = String(notes.length).padStart(2, '0');
      displayOrder = notes.map((_, i) => i); render();
    } catch (error) {
      console.warn('Guestbook:', error.message); count.textContent = '—';
      board.setAttribute('aria-busy', 'false'); empty('error');
    }
  }
  start();
})();
