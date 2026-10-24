#!/usr/bin/env python3
import json
import re
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

ROOT = Path(__file__).resolve().parent
COUNTRIES_DIR = ROOT / "data" / "countries"

I18N = {
    "en": {
        "title": "Constitution Search",
        "tab_search": "Search",
        "tab_browse": "Browse",
        "tab_options": "Options",
        "query": "Query (topic / country):",
        "search_btn": "Search",
        "open_browser": "Open official page in browser",
        "results": "Results",
        "no_results": "Nothing found in local data.",
        "country": "Country:",
        "load": "Load",
        "language": "Language",
        "theme": "Theme",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "theme_system": "System",
        "save": "Apply",
        "saved": "Settings applied",
        "pick_country": "Select a country",
        "matches": "score",
        "no_data": "No country files in data/countries/",
    },
    "ru": {
        "title": "Поиск по конституциям",
        "tab_search": "Поиск",
        "tab_browse": "Читать",
        "tab_options": "Настройки",
        "query": "Запрос (тема / страна):",
        "search_btn": "Искать",
        "open_browser": "Открыть официальную страницу в браузере",
        "results": "Результаты",
        "no_results": "В локальных данных ничего не найдено.",
        "country": "Страна:",
        "load": "Открыть",
        "language": "Язык",
        "theme": "Тема",
        "theme_light": "Светлая",
        "theme_dark": "Тёмная",
        "theme_system": "Системная",
        "save": "Применить",
        "saved": "Настройки применены",
        "pick_country": "Выберите страну",
        "matches": "балл",
        "no_data": "Нет файлов в data/countries/",
    },
}

THEMES = {
    "light": {"bg": "#f4f4f4", "fg": "#1a1a1a", "text_bg": "#ffffff", "text_fg": "#111111"},
    "dark": {"bg": "#1e1e1e", "fg": "#e8e8e8", "text_bg": "#2d2d2d", "text_fg": "#f0f0f0"},
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def load_countries():
    items = []
    if not COUNTRIES_DIR.is_dir():
        return items
    for path in sorted(COUNTRIES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"Skip {path.name}: {e}")
            continue
        if not isinstance(data, dict):
            continue
        data["_file"] = path.name
        data.setdefault("id", path.stem.lower())
        data.setdefault("name_en", path.stem)
        data.setdefault("name_ru", path.stem)
        data.setdefault("language", "en")
        data.setdefault("official_url", "")
        data.setdefault("text", "")
        items.append(data)
    return items


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = "ru"
        self.theme_name = "dark"
        self.countries = load_countries()
        self.title("Constitution Search")
        self.geometry("920x620")
        self.minsize(720, 480)

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self._build()
        self.apply_theme()
        self.refresh_texts()

        if not self.countries:
            messagebox.showwarning("Constitution Search", I18N["ru"]["no_data"])

    def t(self, key):
        return I18N[self.lang].get(key, key)

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.nb = ttk.Notebook(self)
        self.nb.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self.tab_s = ttk.Frame(self.nb)
        self.tab_b = ttk.Frame(self.nb)
        self.tab_o = ttk.Frame(self.nb)
        self.nb.add(self.tab_s, text="Search")
        self.nb.add(self.tab_b, text="Browse")
        self.nb.add(self.tab_o, text="Options")

        self._build_search()
        self._build_browse()
        self._build_options()

    def _build_search(self):
        f = self.tab_s
        f.columnconfigure(0, weight=1)
        f.rowconfigure(3, weight=1)

        self.lbl_q = ttk.Label(f, text="")
        self.lbl_q.grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))

        self.ent_q = ttk.Entry(f)
        self.ent_q.grid(row=1, column=0, sticky="ew", padx=8)
        self.ent_q.bind("<Return>", lambda e: self.do_search())

        bar = ttk.Frame(f)
        bar.grid(row=2, column=0, sticky="ew", padx=8, pady=6)
        self.btn_s = ttk.Button(bar, text="", command=self.do_search)
        self.btn_s.pack(side="left")
        self.var_browser = tk.BooleanVar(value=False)
        self.chk_br = ttk.Checkbutton(bar, text="", variable=self.var_browser)
        self.chk_br.pack(side="left", padx=12)

        self.txt_s = scrolledtext.ScrolledText(f, wrap="word", font=("Consolas", 11))
        self.txt_s.grid(row=3, column=0, sticky="nsew", padx=8, pady=8)

    def _build_browse(self):
        f = self.tab_b
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)

        top = ttk.Frame(f)
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.lbl_c = ttk.Label(top, text="")
        self.lbl_c.pack(side="left")
        self.cmb = ttk.Combobox(top, state="readonly", width=42)
        self.cmb.pack(side="left", padx=8)
        self.btn_load = ttk.Button(top, text="", command=self.load_country)
        self.btn_load.pack(side="left")

        self.txt_b = scrolledtext.ScrolledText(f, wrap="word", font=("Consolas", 11))
        self.txt_b.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self._fill_combo()

    def _build_options(self):
        f = self.tab_o
        pad = {"padx": 12, "pady": 6}

        self.lbl_lang = ttk.Label(f, text="")
        self.lbl_lang.grid(row=0, column=0, sticky="w", **pad)
        self.var_lang = tk.StringVar(value=self.lang)
        box = ttk.Frame(f)
        box.grid(row=1, column=0, sticky="w", **pad)
        ttk.Radiobutton(box, text="Русский", variable=self.var_lang, value="ru").pack(side="left")
        ttk.Radiobutton(box, text="English", variable=self.var_lang, value="en").pack(side="left", padx=8)

        self.lbl_theme = ttk.Label(f, text="")
        self.lbl_theme.grid(row=2, column=0, sticky="w", **pad)
        self.var_theme = tk.StringVar(value=self.theme_name)
        tbox = ttk.Frame(f)
        tbox.grid(row=3, column=0, sticky="w", **pad)
        self.rb_l = ttk.Radiobutton(tbox, text="", variable=self.var_theme, value="light")
        self.rb_d = ttk.Radiobutton(tbox, text="", variable=self.var_theme, value="dark")
        self.rb_sys = ttk.Radiobutton(tbox, text="", variable=self.var_theme, value="system")
        self.rb_l.pack(side="left")
        self.rb_d.pack(side="left", padx=8)
        self.rb_sys.pack(side="left")

        self.btn_apply = ttk.Button(f, text="", command=self.apply_settings)
        self.btn_apply.grid(row=4, column=0, sticky="w", **pad)

    def _fill_combo(self):
        labels = []
        self._by_label = {}
        for c in self.countries:
            label = f"{c.get('name_ru')} / {c.get('name_en')} [{c.get('id')}]"
            labels.append(label)
            self._by_label[label] = c
        self.cmb["values"] = labels
        if labels:
            self.cmb.current(0)

    def _aliases(self, c):
        s = {
            norm(c.get("id", "")),
            norm(c.get("name_en", "")),
            norm(c.get("name_ru", "")),
        }
        extra = {
            "russia": {"рф", "россия", "russian"},
            "usa": {"сша", "us", "united states", "america"},
        }
        s |= extra.get(norm(c.get("id", "")), set())
        return {x for x in s if x}

    def do_search(self):
        q = norm(self.ent_q.get())
        self.txt_s.delete("1.0", "end")
        if not q:
            return
        tokens = [t for t in re.split(r"[,\s]+", q) if t]
        hits = []

        for c in self.countries:
            text = c.get("text") or ""
            low = text.lower()
            aliases = self._aliases(c)
            score = 0
            snippets = []

            for token in tokens:
                if token in aliases:
                    score += 5
                    continue
                if len(token) < 2:
                    continue
                if token in low:
                    score += 2
                    for m in re.finditer(re.escape(token), text, flags=re.IGNORECASE):
                        a = max(0, m.start() - 70)
                        b = min(len(text), m.end() + 100)
                        snippets.append("..." + text[a:b].replace("\n", " ") + "...")
                        if len(snippets) >= 3:
                            break

            if score > 0 and not snippets and text:
                snippets.append(text[:350].replace("\n", " ") + "...")

            if score > 0 or snippets:
                hits.append((score, c, snippets))

        hits.sort(key=lambda x: -x[0])
        if not hits:
            self.txt_s.insert("end", self.t("no_results"))
            return

        for score, c, snippets in hits:
            self.txt_s.insert(
                "end",
                f"{c.get('name_ru')} / {c.get('name_en')} [{c.get('id')}] — {score} {self.t('matches')}\n",
            )
            self.txt_s.insert("end", "-" * 56 + "\n")
            for sn in snippets[:3]:
                self.txt_s.insert("end", sn + "\n\n")
            self.txt_s.insert("end", "\n")
            if self.var_browser.get() and c.get("official_url"):
                try:
                    webbrowser.open(c["official_url"])
                except Exception:
                    pass

    def load_country(self):
        label = self.cmb.get()
        c = self._by_label.get(label)
        if not c:
            messagebox.showinfo(self.t("title"), self.t("pick_country"))
            return
        self.txt_b.delete("1.0", "end")
        self.txt_b.insert("end", c.get("text") or self.t("no_results"))

    def apply_settings(self):
        self.lang = self.var_lang.get()
        th = self.var_theme.get()
        self.theme_name = "dark" if th == "system" else th
        self.refresh_texts()
        self.apply_theme()
        messagebox.showinfo(self.t("title"), self.t("saved"))

    def refresh_texts(self):
        self.title(self.t("title"))
        self.nb.tab(0, text=self.t("tab_search"))
        self.nb.tab(1, text=self.t("tab_browse"))
        self.nb.tab(2, text=self.t("tab_options"))
        self.lbl_q.config(text=self.t("query"))
        self.btn_s.config(text=self.t("search_btn"))
        self.chk_br.config(text=self.t("open_browser"))
        self.lbl_c.config(text=self.t("country"))
        self.btn_load.config(text=self.t("load"))
        self.lbl_lang.config(text=self.t("language"))
        self.lbl_theme.config(text=self.t("theme"))
        self.rb_l.config(text=self.t("theme_light"))
        self.rb_d.config(text=self.t("theme_dark"))
        self.rb_sys.config(text=self.t("theme_system"))
        self.btn_apply.config(text=self.t("save"))

    def apply_theme(self):
        th = THEMES.get(self.theme_name, THEMES["dark"])
        self.configure(bg=th["bg"])
        for w in (self.txt_s, self.txt_b):
            w.configure(bg=th["text_bg"], fg=th["text_fg"], insertbackground=th["fg"])


if __name__ == "__main__":
    if not (COUNTRIES_DIR.is_dir()):
        raise SystemExit(f"Create folder: {COUNTRIES_DIR}")
    App().mainloop()
