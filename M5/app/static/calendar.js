
const pad = (n) => String(n).padStart(2, "0");
const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const parseIso = (s) => {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, m - 1, d);
};
const addDays = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined && text !== null) n.textContent = text;
  return n;
}

function color(category = "") {
  let h = 0;
  for (const c of String(category)) h = (h * 31 + c.charCodeAt(0)) % 360;
  return `hsl(${h} 55% 36%)`;
}

export function mountCalendar(container, options = {}) {
  if (!container) {
    throw new Error("Brak kontenera kalendarza.");
  }

  const {
    apiBase = "",
    initialView = "MONTH",
    timeZone = "Europe/Warsaw",
  } = options;

  const base = apiBase.replace(/\/+$/, "");
  const t = new Date();
  const state = {
    view: initialView,
    date: new Date(t.getFullYear(), t.getMonth(), t.getDate()),
  };
  const todayIso = iso(state.date);
  let seq = 0;
  let controller = null;

  // ---------- formatowanie (czas wyświetlany w strefie timeZone) ----------
  const wDate = (s) => new Date(s).toLocaleDateString("sv-SE", { timeZone });
  const fmtTime = (s) =>
    new Date(s).toLocaleTimeString("pl-PL", {
      timeZone,
      hour: "2-digit",
      minute: "2-digit",
    });
  const fmtFull = (s) =>
    new Date(s).toLocaleString("pl-PL", {
      timeZone,
      day: "numeric",
      month: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  const fmtDay = (s) =>
    parseIso(s).toLocaleDateString("pl-PL", {
      weekday: "long",
      day: "numeric",
      month: "long",
    });
  const fmtRange = (ev) =>
    wDate(ev.start) === wDate(ev.end)
      ? `${fmtTime(ev.start)}–${fmtTime(ev.end)}`
      : `${fmtFull(ev.start)} – ${fmtFull(ev.end)}`;

  // ---------- szkielet w podanym kontenerze ----------
  const root = el("div", "edu-cal");
  const button = (text, label) => {
    const b = el("button", "edu-cal-btn", text);
    b.type = "button";
    if (label) b.setAttribute("aria-label", label);
    return b;
  };
  const prev = button("‹", "Poprzedni okres");
  const next = button("›", "Następny okres");
  const todayBtn = button("Dziś");
  const title = el("h2", "edu-cal-title", "Ładowanie…");
  title.setAttribute("aria-live", "polite");

  const views = el("div", "edu-cal-views");
  const viewBtns = [
    ["DAY", "Dzień"],
    ["WEEK", "Tydzień"],
    ["MONTH", "Miesiąc"],
  ].map(([key, label]) => {
    const b = button(label);
    b.dataset.view = key;
    b.onclick = () => {
      state.view = key;
      load();
    };
    views.append(b);
    return b;
  });

  const bar = el("div", "edu-cal-bar");
  bar.append(prev, todayBtn, next, title, views);
  const message = el("div");
  const content = el("div");
  root.append(bar, message, content);
  container.replaceChildren(root);

  // ---------- pobieranie danych ----------
  async function fetchView(view, date, signal) {
    const url = `${base}/api/calendar/${view.toLowerCase()}?date=${iso(date)}`;
    let res;
    try {
      res = await fetch(url, {
        headers: { Accept: "application/json" },
        signal,
      });
    } catch (err) {
      if (err?.name === "AbortError") throw err;
      throw new Error("Nie można połączyć się z serwerem kalendarza.");
    }
    const body = await res.json().catch(() => null);
    if (!res.ok) {
      throw new Error(body?.error?.message ?? `Błąd serwera (${res.status}).`);
    }
    return body;
  }

  // ---------- renderowanie ----------
  function renderMonth(data) {
    const grid = el("div", "edu-cal-grid");
    for (const n of ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]) {
      grid.append(el("div", "edu-cal-dow", n));
    }

    const days = Array.isArray(data?.days) ? data.days : [];
    if (!days.length) {
      grid.append(el("p", "edu-cal-empty", "Brak danych dla wybranego okresu."));
      return grid;
    }

    const offset = (parseIso(days[0].date).getDay() + 6) % 7; // poniedziałek = 0
    for (let i = 0; i < offset; i++) {
      grid.append(el("div", "edu-cal-cell is-out"));
    }

    for (const day of days) {
      const events = Array.isArray(day.events) ? day.events : [];
      const cell = el(
        "div",
        "edu-cal-cell" + (day.date === todayIso ? " is-today" : "")
      );
      cell.append(el("div", "edu-cal-num", String(parseIso(day.date).getDate())));

      for (const ev of events.slice(0, 3)) {
        const chip = el("span", "edu-cal-chip", `${fmtTime(ev.start)} ${ev.title}`);
        chip.style.background = color(ev.category);
        chip.title = ev.title ?? "";
        cell.append(chip);
      }

      if (events.length > 3) {
        cell.append(el("div", "edu-cal-more", `+${events.length - 3} więcej`));
      }

      const open = () => {
        state.view = "DAY";
        state.date = parseIso(day.date);
        load();
      };
      cell.tabIndex = 0;
      cell.setAttribute("role", "button");
      cell.onclick = open;
      cell.onkeydown = (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          open();
        }
      };
      grid.append(cell);
    }
    return grid;
  }

  function renderList(data) {
    // widok dzienny i tygodniowy
    const wrap = el("div");
    const days = Array.isArray(data?.days) ? data.days : [];
    for (const day of days) {
      const events = Array.isArray(day.events) ? day.events : [];
      const sec = el(
        "section",
        "edu-cal-day" + (day.date === todayIso ? " is-today" : "")
      );
      sec.append(el("h3", null, fmtDay(day.date)));
      if (!events.length) {
        sec.append(el("p", "edu-cal-empty", "Brak wydarzeń tego dnia."));
      }
      for (const ev of events) {
        const row = el("div", "edu-cal-event");
        row.append(el("div", "edu-cal-time", fmtRange(ev)));

        const info = el("div");
        info.append(
          el("strong", null, ev.title),
          el("div", "edu-cal-meta", ev.location),
          el("div", "edu-cal-meta", `Prowadzący: ${ev.host ?? ""}`)
        );

        const tags = el("div", "edu-cal-tags");
        if (ev.category) {
          const cat = el("span", "edu-cal-tag", ev.category);
          cat.style.background = color(ev.category);
          tags.append(cat);
        }
        if (ev.status) {
          tags.append(el("span", "edu-cal-tag edu-cal-tag-status", ev.status));
        }

        row.append(info, tags);
        sec.append(row);
      }
      wrap.append(sec);
    }
    return wrap;
  }

  function setTitle(data) {
    const s = parseIso(data.start);
    const e = parseIso(data.end);
    const f = (d, o) => d.toLocaleDateString("pl-PL", o);
    title.textContent =
      data.type === "MONTH"
        ? f(s, { month: "long", year: "numeric" })
        : data.type === "WEEK"
          ? `${f(s, { day: "numeric", month: "short" })} – ${f(e, {
              day: "numeric",
              month: "short",
              year: "numeric",
            })}`
          : f(s, {
              weekday: "long",
              day: "numeric",
              month: "long",
              year: "numeric",
            });
  }

  function showMessage(text, cls) {
    message.replaceChildren();
    if (!text) return;
    const n = el("div", cls, text);
    if (cls === "edu-cal-error") n.setAttribute("role", "alert");
    message.append(n);
  }

  async function load() {
    const mine = ++seq;
    controller?.abort();
    controller = new AbortController();

    viewBtns.forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.view === state.view))
    );
    showMessage("", "edu-cal-notice");

    try {
      const data = await fetchView(state.view, state.date, controller.signal);
      if (mine !== seq) return;
      showMessage("", "edu-cal-notice");
      setTitle(data);
      content.replaceChildren(
        data.type === "MONTH" ? renderMonth(data) : renderList(data)
      );
    } catch (err) {
      if (err?.name === "AbortError" || mine !== seq) return;
      showMessage(err.message, "edu-cal-error");
      content.replaceChildren();
    }
  }

  // ---------- nawigacja ----------
  function shift(dir) {
    const d = state.date;
    if (state.view === "DAY") state.date = addDays(d, dir);
    else if (state.view === "WEEK") state.date = addDays(d, 7 * dir);
    else state.date = new Date(d.getFullYear(), d.getMonth() + dir, 1);
    load();
  }

  prev.onclick = () => shift(-1);
  next.onclick = () => shift(1);
  todayBtn.onclick = () => {
    state.date = parseIso(todayIso);
    load();
  };

  load();

  return {
    refresh: load,
    destroy() {
      seq++;
      controller?.abort();
      root.remove();
    },
  };
}