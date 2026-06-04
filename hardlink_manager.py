"""
HardLink Manager — CustomTkinter GUI
Crea hardlink NTFS (mklink /H) con interfaccia grafica moderna.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
import threading
import queue
import sys
from pathlib import Path

# ── Tema ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT   = "#5b6ef5"
ACCENT2  = "#3bf0c2"
SUCCESS  = "#2ecc71"
WARN     = "#f5a623"
DANGER   = "#e74c3c"
BG       = "#0d0f14"
SURFACE  = "#141720"
SURFACE2 = "#1a1e2e"
BORDER   = "#252a3d"
TEXT     = "#e8eaf6"
TEXT2    = "#8891b5"

EXTENSIONS_DEFAULT = ["mkv", "mp4", "avi"]
EXTENSIONS_EXTRA   = ["wmv", "mov", "ts", "m4v", "flv"]

# ── Utilità ─────────────────────────────────────────────────────────────────
def format_bytes(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


# ── App principale ───────────────────────────────────────────────────────────
class HardLinkManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HardLink Manager")
        self.geometry("920x760")
        self.minsize(760, 600)
        self.configure(fg_color=BG)

        # State
        self.mode          = tk.StringVar(value="folder")   # folder | files
        self.src_folder    = tk.StringVar()
        self.dst_folder    = tk.StringVar()
        self.active_exts   = set(EXTENSIONS_DEFAULT)
        self.selected_files: list[str] = []
        self.opt_skip      = tk.BooleanVar(value=True)
        self.opt_log       = tk.BooleanVar(value=True)
        self.opt_dryrun    = tk.BooleanVar(value=False)
        self.opt_recurse   = tk.BooleanVar(value=True)
        self._log_queue    = queue.Queue()
        self._running      = False

        self._build_ui()
        self._poll_log_queue()

    # ── Build UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="🔗  HardLink Manager",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=TEXT
        ).pack(side="left", padx=24, pady=0)
        ctk.CTkLabel(
            hdr, text="mklink /H · NTFS · Windows",
            font=ctk.CTkFont("Consolas", 12),
            text_color=TEXT2
        ).pack(side="left", padx=4)

        # Scrollable body
        body = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=BORDER)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        self._section_source(body)
        self._section_dest(body)
        self._section_options(body)
        self._section_log(body)
        self._section_actions(body)

    # ── Section helpers ───────────────────────────────────────────────────────
    def _card(self, parent, title: str) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER)
        outer.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(
            outer, text=title.upper(),
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color=TEXT2
        ).pack(anchor="w", padx=20, pady=(14, 6))
        sep = ctk.CTkFrame(outer, fg_color=BORDER, height=1)
        sep.pack(fill="x", padx=20)
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=14)
        return inner

    def _path_row(self, parent, label: str, var: tk.StringVar, browse_cmd, placeholder: str):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont("Segoe UI", 12), text_color=TEXT2).pack(anchor="w", pady=(0, 4))
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        entry = ctk.CTkEntry(
            row, textvariable=var, placeholder_text=placeholder,
            font=ctk.CTkFont("Consolas", 12),
            fg_color=SURFACE2, border_color=BORDER,
            text_color=TEXT, height=38
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            row, text="Sfoglia…", command=browse_cmd,
            width=90, height=38,
            fg_color=SURFACE2, hover_color=BORDER,
            border_color=BORDER, border_width=1,
            text_color=TEXT2, font=ctk.CTkFont("Segoe UI", 12)
        ).pack(side="left")

    # ── Section: Sorgente ─────────────────────────────────────────────────────
    def _section_source(self, parent):
        inner = self._card(parent, "01 — Sorgente")

        # Mode toggle
        seg = ctk.CTkSegmentedButton(
            inner,
            values=["📁  Cartella", "📄  File singoli"],
            command=self._on_mode_change,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            selected_color=ACCENT, selected_hover_color="#6f80f7",
            unselected_color=SURFACE2, unselected_hover_color=BORDER,
            fg_color=SURFACE2, height=36
        )
        seg.set("📁  Cartella")
        seg.pack(fill="x", pady=(0, 14))
        self._seg = seg

        # ─ Folder mode ─
        self._folder_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self._folder_frame.pack(fill="x")

        self._path_row(
            self._folder_frame, "Cartella sorgente:",
            self.src_folder, self._browse_src_folder,
            "Es: E:\\DOWNLOAD\\TORRENT\\One Piece"
        )

        ctk.CTkCheckBox(
            self._folder_frame, text="Ricerca ricorsiva nelle sottocartelle",
            variable=self.opt_recurse,
            font=ctk.CTkFont("Segoe UI", 12), text_color=TEXT2,
            checkbox_width=18, checkbox_height=18,
            checkmark_color="white", hover_color=ACCENT,
            fg_color=ACCENT, border_color=BORDER
        ).pack(anchor="w", pady=(0, 12))

        # Extensions
        ctk.CTkLabel(
            self._folder_frame, text="Estensioni da includere:",
            font=ctk.CTkFont("Segoe UI", 12), text_color=TEXT2
        ).pack(anchor="w", pady=(0, 6))

        self._ext_frame = ctk.CTkFrame(self._folder_frame, fg_color="transparent")
        self._ext_frame.pack(fill="x", pady=(0, 8))
        self._render_ext_chips()

        add_row = ctk.CTkFrame(self._folder_frame, fg_color="transparent")
        add_row.pack(fill="x")
        self._new_ext_var = tk.StringVar()
        ctk.CTkEntry(
            add_row, textvariable=self._new_ext_var,
            placeholder_text=".wmv", width=100, height=32,
            font=ctk.CTkFont("Consolas", 12),
            fg_color=SURFACE2, border_color=BORDER, text_color=TEXT
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            add_row, text="+ Aggiungi", command=self._add_ext,
            height=32, width=100,
            fg_color=SURFACE2, hover_color=BORDER,
            border_color=BORDER, border_width=1,
            text_color=TEXT2, font=ctk.CTkFont("Segoe UI", 11)
        ).pack(side="left")

        # ─ Files mode ─
        self._files_frame = ctk.CTkFrame(inner, fg_color="transparent")
        # (non packed inizialmente)

        ctk.CTkButton(
            self._files_frame, text="+ Aggiungi file…",
            command=self._browse_files,
            height=38, fg_color=ACCENT, hover_color="#6f80f7",
            font=ctk.CTkFont("Segoe UI", 13, "bold")
        ).pack(anchor="w", pady=(0, 10))

        self._file_list_frame = ctk.CTkScrollableFrame(
            self._files_frame, fg_color=SURFACE2,
            corner_radius=8, height=180,
            scrollbar_button_color=BORDER
        )
        self._file_list_frame.pack(fill="x")

        self._empty_label = ctk.CTkLabel(
            self._file_list_frame,
            text="📭  Nessun file selezionato",
            font=ctk.CTkFont("Segoe UI", 13), text_color=TEXT2
        )
        self._empty_label.pack(pady=30)

        self._stats_label = ctk.CTkLabel(
            self._files_frame, text="",
            font=ctk.CTkFont("Consolas", 11), text_color=TEXT2
        )
        self._stats_label.pack(anchor="w", pady=(6, 0))

    def _render_ext_chips(self):
        for w in self._ext_frame.winfo_children():
            w.destroy()
        all_exts = EXTENSIONS_DEFAULT + [e for e in EXTENSIONS_EXTRA if e not in EXTENSIONS_DEFAULT]
        # also include any custom ones
        for e in self.active_exts:
            if e not in all_exts:
                all_exts.append(e)

        row = None
        for i, ext in enumerate(all_exts):
            if i % 6 == 0:
                row = ctk.CTkFrame(self._ext_frame, fg_color="transparent")
                row.pack(anchor="w", pady=2)
            active = ext in self.active_exts
            btn = ctk.CTkButton(
                row, text=f".{ext}",
                width=68, height=30,
                fg_color=ACCENT if active else SURFACE2,
                hover_color="#6f80f7" if active else BORDER,
                border_color=ACCENT2 if active else BORDER,
                border_width=1,
                text_color="white" if active else TEXT2,
                font=ctk.CTkFont("Consolas", 12),
                corner_radius=6,
                command=lambda e=ext: self._toggle_ext(e)
            )
            btn.pack(side="left", padx=3)

    def _toggle_ext(self, ext: str):
        if ext in self.active_exts:
            if len(self.active_exts) <= 1:
                self._toast("Almeno un'estensione richiesta", WARN)
                return
            self.active_exts.discard(ext)
        else:
            self.active_exts.add(ext)
        self._render_ext_chips()

    def _add_ext(self):
        val = self._new_ext_var.get().strip().lstrip(".").lower()
        if val:
            self.active_exts.add(val)
            self._new_ext_var.set("")
            self._render_ext_chips()

    def _on_mode_change(self, val: str):
        if "Cartella" in val:
            self._files_frame.pack_forget()
            self._folder_frame.pack(fill="x")
            self.mode.set("folder")
        else:
            self._folder_frame.pack_forget()
            self._files_frame.pack(fill="x")
            self.mode.set("files")

    # ── Section: Destinazione ─────────────────────────────────────────────────
    def _section_dest(self, parent):
        inner = self._card(parent, "02 — Destinazione hardlink")
        self._path_row(
            inner, "Cartella di destinazione:",
            self.dst_folder, self._browse_dst_folder,
            "Es: E:\\PLEX\\ANIME\\ONE PIECE"
        )
        ctk.CTkLabel(
            inner,
            text="ℹ  La struttura di sottocartelle verrà ricreata nella destinazione",
            font=ctk.CTkFont("Segoe UI", 11), text_color=TEXT2
        ).pack(anchor="w")

    # ── Section: Opzioni ──────────────────────────────────────────────────────
    def _section_options(self, parent):
        inner = self._card(parent, "03 — Opzioni")
        opts = [
            (self.opt_skip,   "Salta file già esistenti (evita duplicati)"),
            (self.opt_log,    "Mostra log dettagliato durante l'esecuzione"),
            (self.opt_dryrun, "Dry-run: simula senza creare nulla  ⚠"),
        ]
        for var, label in opts:
            ctk.CTkCheckBox(
                inner, text=label, variable=var,
                font=ctk.CTkFont("Segoe UI", 12), text_color=TEXT2,
                checkbox_width=18, checkbox_height=18,
                checkmark_color="white", hover_color=ACCENT,
                fg_color=ACCENT, border_color=BORDER
            ).pack(anchor="w", pady=4)

    # ── Section: Log ──────────────────────────────────────────────────────────
    def _section_log(self, parent):
        inner = self._card(parent, "04 — Output")
        self._log_box = ctk.CTkTextbox(
            inner, height=200,
            font=ctk.CTkFont("Consolas", 12),
            fg_color="#080a10", text_color="#c8cfe8",
            border_color=BORDER, border_width=1,
            corner_radius=8, state="disabled",
            wrap="none"
        )
        self._log_box.pack(fill="x")

        # Tag colors (configure after widget creation)
        self._log_box._textbox.tag_configure("cyan",   foreground="#3bf0c2")
        self._log_box._textbox.tag_configure("yellow", foreground="#f5a623")
        self._log_box._textbox.tag_configure("green",  foreground="#2ecc71")
        self._log_box._textbox.tag_configure("red",    foreground="#e74c3c")
        self._log_box._textbox.tag_configure("gray",   foreground="#4e5678")
        self._log_box._textbox.tag_configure("white",  foreground="#e8eaf6")

        # Progress bar
        self._progress = ctk.CTkProgressBar(
            inner, mode="indeterminate",
            progress_color=ACCENT, fg_color=SURFACE2, height=4
        )
        self._progress.pack(fill="x", pady=(8, 0))
        self._progress.set(0)

        self._status_label = ctk.CTkLabel(
            inner, text="In attesa…",
            font=ctk.CTkFont("Consolas", 11), text_color=TEXT2
        )
        self._status_label.pack(anchor="w", pady=(4, 0))

    # ── Section: Azioni ──────────────────────────────────────────────────────
    def _section_actions(self, parent):
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="x", pady=(0, 20))

        self._run_btn = ctk.CTkButton(
            inner, text="▶  Esegui ora",
            command=self._run,
            height=46, font=ctk.CTkFont("Segoe UI", 14, "bold"),
            fg_color=ACCENT, hover_color="#6f80f7",
            corner_radius=10
        )
        self._run_btn.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            inner, text="💾  Salva .ps1",
            command=self._save_ps1,
            height=46, font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=SURFACE2, hover_color=BORDER,
            border_color=BORDER, border_width=1,
            text_color=TEXT2, corner_radius=10
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            inner, text="🗑  Pulisci log",
            command=self._clear_log,
            height=46, font=ctk.CTkFont("Segoe UI", 13),
            fg_color=SURFACE2, hover_color=BORDER,
            border_color=BORDER, border_width=1,
            text_color=TEXT2, corner_radius=10
        ).pack(side="left")

        self._stop_btn = ctk.CTkButton(
            inner, text="⏹  Stop",
            command=self._stop,
            height=46, font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=DANGER, hover_color="#c0392b",
            corner_radius=10
        )
        # pack solo durante esecuzione

    # ── Browse ───────────────────────────────────────────────────────────────
    def _browse_src_folder(self):
        d = filedialog.askdirectory(title="Seleziona cartella sorgente")
        if d:
            self.src_folder.set(d.replace("/", "\\"))

    def _browse_dst_folder(self):
        d = filedialog.askdirectory(title="Seleziona cartella di destinazione")
        if d:
            self.dst_folder.set(d.replace("/", "\\"))

    def _browse_files(self):
        files = filedialog.askopenfilenames(
            title="Seleziona file video",
            filetypes=[("File video", "*.mkv *.mp4 *.avi *.wmv *.mov *.ts *.m4v"), ("Tutti", "*.*")]
        )
        for f in files:
            f = f.replace("/", "\\")
            if f not in self.selected_files:
                self.selected_files.append(f)
        self._render_file_list()

    def _render_file_list(self):
        for w in self._file_list_frame.winfo_children():
            w.destroy()
        if not self.selected_files:
            self._empty_label = ctk.CTkLabel(
                self._file_list_frame,
                text="📭  Nessun file selezionato",
                font=ctk.CTkFont("Segoe UI", 13), text_color=TEXT2
            )
            self._empty_label.pack(pady=30)
            self._stats_label.configure(text="")
            return

        for idx, fp in enumerate(self.selected_files):
            row = ctk.CTkFrame(self._file_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            size = os.path.getsize(fp) if os.path.exists(fp) else 0
            ext = Path(fp).suffix.lstrip(".").lower()
            icons = {"mkv": "🎞", "mp4": "🎬", "avi": "📹"}
            icon = icons.get(ext, "📄")
            ctk.CTkLabel(
                row, text=icon, width=24,
                font=ctk.CTkFont("Segoe UI", 14)
            ).pack(side="left", padx=(4, 6))
            ctk.CTkLabel(
                row, text=Path(fp).name,
                font=ctk.CTkFont("Consolas", 11), text_color=TEXT,
                anchor="w"
            ).pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(
                row, text=format_bytes(size),
                font=ctk.CTkFont("Consolas", 11), text_color=TEXT2,
                width=80
            ).pack(side="left")
            ctk.CTkButton(
                row, text="✕", width=28, height=24,
                fg_color="transparent", hover_color=DANGER,
                text_color=TEXT2, font=ctk.CTkFont("Segoe UI", 12),
                command=lambda i=idx: self._remove_file(i)
            ).pack(side="left", padx=4)

        total = sum(os.path.getsize(f) for f in self.selected_files if os.path.exists(f))
        self._stats_label.configure(
            text=f"{len(self.selected_files)} file  •  {format_bytes(total)} totali"
        )

    def _remove_file(self, idx: int):
        self.selected_files.pop(idx)
        self._render_file_list()

    # ── Script generation ────────────────────────────────────────────────────
    def _build_script(self) -> str | None:
        dst = self.dst_folder.get().strip()
        if not dst:
            self._toast("Inserisci la cartella di destinazione", DANGER)
            return None

        skip   = self.opt_skip.get()
        dryrun = self.opt_dryrun.get()
        log    = self.opt_log.get()

        lines = [
            "# HardLink Manager — generato automaticamente",
            f'$destinazione = "{dst}"',
            "",
            "if (!(Test-Path $destinazione)) {",
        ]
        if dryrun:
            lines.append('    Write-Host "[DRY-RUN] Creerebbe: $destinazione" -ForegroundColor DarkCyan')
        else:
            lines.append("    New-Item -ItemType Directory -Path $destinazione -Force | Out-Null")
        lines.append("}")
        lines.append("")

        if self.mode.get() == "folder":
            src = self.src_folder.get().strip()
            if not src:
                self._toast("Inserisci la cartella sorgente", DANGER)
                return None
            exts = " ".join(f"*.{e}" for e in sorted(self.active_exts))
            recurse = "-Recurse" if self.opt_recurse.get() else ""
            lines += [
                f'$origine    = "{src}"',
                f'$estensioni = "{", ".join(f"*.{e}" for e in sorted(self.active_exts))}"',
                "",
                f"$fileVideo = Get-ChildItem -Path $origine -Include $estensioni {recurse}",
                "",
                "foreach ($file in $fileVideo) {",
                "    $percorsoRelativo     = $file.DirectoryName.Substring($origine.Length)",
                "    $cartellaDestinazione = Join-Path $destinazione $percorsoRelativo",
                "    $targetPath           = Join-Path $cartellaDestinazione $file.Name",
                "",
                "    if (!(Test-Path $cartellaDestinazione)) {",
            ]
            if dryrun:
                lines.append('        Write-Host "[DRY-RUN] Cartella: $cartellaDestinazione" -ForegroundColor DarkCyan')
            else:
                lines.append("        New-Item -ItemType Directory -Path $cartellaDestinazione -Force | Out-Null")
            lines += [
                "    }",
                "",
                "    if (!(Test-Path $targetPath)) {",
            ]
            if log:
                lines.append('        Write-Host "  + $($file.Name)" -ForegroundColor Cyan')
            if dryrun:
                lines.append('        Write-Host "[DRY-RUN] Link: $targetPath" -ForegroundColor DarkGray')
            else:
                lines.append('        cmd /c mklink /H "`"$targetPath`"" "`"$($file.FullName)`"" | Out-Null')
            if skip:
                lines += [
                    "    } else {",
                ]
                if log:
                    lines.append('        Write-Host "  ~ $($file.Name) (già esistente)" -ForegroundColor Yellow')
                lines.append("    }")
            else:
                lines.append("    }")
            lines.append("}")

        else:
            # files mode
            if not self.selected_files:
                self._toast("Seleziona almeno un file", DANGER)
                return None
            lines.append("$fileList = @(")
            for f in self.selected_files:
                lines.append(f'    "{f}"')
            lines += [
                ")",
                "",
                "foreach ($sorgente in $fileList) {",
                "    $nomeFile   = [System.IO.Path]::GetFileName($sorgente)",
                "    $targetPath = Join-Path $destinazione $nomeFile",
                "",
                "    if (!(Test-Path $targetPath)) {",
            ]
            if log:
                lines.append('        Write-Host "  + $nomeFile" -ForegroundColor Cyan')
            if dryrun:
                lines.append('        Write-Host "[DRY-RUN] Link: $targetPath" -ForegroundColor DarkGray')
            else:
                lines.append('        cmd /c mklink /H "`"$targetPath`"" "`"$sorgente`"" | Out-Null')
            if skip:
                lines += [
                    "    } else {",
                ]
                if log:
                    lines.append('        Write-Host "  ~ $nomeFile (già esistente)" -ForegroundColor Yellow')
                lines.append("    }")
            else:
                lines.append("    }")
            lines.append("}")

        if log:
            lines += ["", 'Write-Host "`n✔ Completato!" -ForegroundColor Green']

        return "\n".join(lines)

    # ── Execution ────────────────────────────────────────────────────────────
    def _run(self):
        if self._running:
            return
        script = self._build_script()
        if script is None:
            return

        self._running = True
        self._run_btn.configure(state="disabled", text="⏳  In esecuzione…")
        self._stop_btn.pack(side="left", padx=(10, 0))
        self._progress.configure(mode="indeterminate")
        self._progress.start()
        self._status_label.configure(text="Esecuzione in corso…")
        self._log("▶ Avvio esecuzione\n", "cyan")
        if self.opt_dryrun.get():
            self._log("⚠  MODALITÀ DRY-RUN — nessun file verrà creato\n", "yellow")

        self._process = None
        threading.Thread(target=self._run_thread, args=(script,), daemon=True).start()

    def _run_thread(self, script: str):
        try:
            self._process = subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in self._process.stdout:
                line = line.rstrip()
                if not line:
                    continue
                tag = "white"
                if "+" in line:
                    tag = "cyan"
                elif "~" in line or "già esistente" in line.lower():
                    tag = "yellow"
                elif "DRY-RUN" in line:
                    tag = "gray"
                elif "✔" in line or "Completato" in line:
                    tag = "green"
                self._log_queue.put((line + "\n", tag))

            err = self._process.stderr.read().strip()
            self._process.wait()
            rc = self._process.returncode

            if err:
                self._log_queue.put((f"\n⚠ STDERR:\n{err}\n", "red"))
            if rc == 0:
                self._log_queue.put(("✔ Processo terminato correttamente\n", "green"))
            else:
                self._log_queue.put((f"✘ Processo terminato con codice {rc}\n", "red"))

        except FileNotFoundError:
            self._log_queue.put(("✘ PowerShell non trovato. Questo tool richiede Windows.\n", "red"))
        except Exception as e:
            self._log_queue.put((f"✘ Errore: {e}\n", "red"))
        finally:
            self._log_queue.put(("__DONE__", ""))

    def _stop(self):
        if self._process:
            self._process.terminate()
            self._log("\n⏹ Esecuzione interrotta dall'utente\n", "yellow")

    def _poll_log_queue(self):
        try:
            while True:
                msg, tag = self._log_queue.get_nowait()
                if msg == "__DONE__":
                    self._on_done()
                else:
                    self._log(msg, tag)
        except queue.Empty:
            pass
        self.after(50, self._poll_log_queue)

    def _on_done(self):
        self._running = False
        self._process = None
        self._run_btn.configure(state="normal", text="▶  Esegui ora")
        self._stop_btn.pack_forget()
        self._progress.stop()
        self._progress.set(1 if not self.opt_dryrun.get() else 0)
        self._status_label.configure(text="Completato")

    # ── Log ──────────────────────────────────────────────────────────────────
    def _log(self, msg: str, tag: str = "white"):
        self._log_box.configure(state="normal")
        self._log_box._textbox.insert("end", msg, (tag,))
        self._log_box._textbox.see("end")
        self._log_box.configure(state="disabled")

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")
        self._status_label.configure(text="In attesa…")
        self._progress.set(0)

    # ── Save PS1 ─────────────────────────────────────────────────────────────
    def _save_ps1(self):
        script = self._build_script()
        if script is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".ps1",
            filetypes=[("PowerShell script", "*.ps1")],
            initialfile="HardLink_Manager.ps1"
        )
        if path:
            Path(path).write_text(script, encoding="utf-8")
            self._toast(f"Salvato: {Path(path).name}", SUCCESS)

    # ── Toast ─────────────────────────────────────────────────────────────────
    def _toast(self, msg: str, color: str = ACCENT2):
        win = ctk.CTkToplevel(self)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(fg_color=SURFACE)
        lbl = ctk.CTkLabel(
            win, text=msg,
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=color,
            fg_color=SURFACE,
            corner_radius=8,
            padx=20, pady=12
        )
        lbl.pack()
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - win.winfo_width()) // 2
        y = self.winfo_y() + self.winfo_height() - 80
        win.geometry(f"+{x}+{y}")
        win.after(2500, win.destroy)


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = HardLinkManagerApp()
    app.mainloop()
