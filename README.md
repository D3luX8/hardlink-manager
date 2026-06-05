# 🔗 HardLink Manager

**HardLink Manager** è un'applicazione desktop Windows con interfaccia grafica moderna che permette di creare **hardlink NTFS** (`mklink /H`) in modo semplice e visuale, senza dover usare la riga di comando.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)
![UI](https://img.shields.io/badge/UI-CustomTkinter-5b6ef5)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Funzionalità

- **Modalità Cartella** — scansione ricorsiva di una cartella sorgente con filtro per estensioni
- **Modalità File singoli** — selezione manuale dei file da collegare
- **Filtro estensioni** — chip selezionabili (mkv, mp4, avi, wmv, mov, ts…) con possibilità di aggiungerne di personalizzate
- **Esecuzione diretta** — lo script PowerShell viene generato ed eseguito internamente, senza file intermedi
- **Dry-run** — simula l'operazione senza creare nulla, per verificare prima
- **Log in tempo reale** — output colorato con avanzamento dell'operazione
- **Salva .ps1** — esporta lo script PowerShell generato per uso esterno
- **Tema scuro** — interfaccia moderna con CustomTkinter

---

## 📸 Screenshot

> *(aggiungi uno screenshot della GUI qui)*

---

## 🚀 Utilizzo

### Opzione A — Eseguibile standalone (consigliato)

Scarica `HardLink Manager.exe` dalla sezione [Releases](../../releases) ed eseguilo direttamente. Non richiede Python installato.

> ⚠️ Windows potrebbe mostrare un avviso SmartScreen al primo avvio — clicca **"Ulteriori informazioni" → "Esegui comunque"**.
> L'applicazione richiede privilegi di **Amministratore** per creare hardlink NTFS.

### Opzione B — Da sorgente

**Requisiti:**
- Python 3.10+
- `customtkinter`

```bash
git clone https://github.com/D3luX8/hardlink-manager.git
cd hardlink-manager
pip install -r requirements.txt
python hardlink_manager.py
```

---

## 🔨 Build dell'eseguibile

### Con Nuitka (consigliato)

```bash
pip install nuitka
python -m nuitka --onefile --windows-console-mode=disable --enable-plugin=tk-inter --include-package=customtkinter --include-package-data=customtkinter --output-filename="HardLink Manager.exe" hardlink_manager.py
```

> 💡 Prima della compilazione, aggiungi la cartella del progetto alle **esclusioni di Windows Defender** per evitare blocchi durante il post-processing.

### Con cx_Freeze (alternativa, cartella)

```bash
pip install cx_freeze
python setup.py build
```

L'eseguibile viene generato in `build/exe.win-amd64-3.10/`.

---

## 📁 Struttura del progetto

```
hardlink-manager/
├── hardlink_manager.py     # Applicazione principale (CustomTkinter)
├── setup.py                # Build script cx_Freeze
├── requirements.txt        # Dipendenze Python
├── .gitignore
├── LICENSE
├── README.md
└── docs/
    └── usage.md            # Guida d'uso dettagliata
```

---

## ⚙️ Come funzionano gli hardlink NTFS

Un **hardlink** è un collegamento diretto a livello filesystem che punta agli stessi dati fisici su disco di un file originale. A differenza dei collegamenti simbolici (shortcut), un hardlink:

- **Non occupa spazio aggiuntivo** — i dati sono condivisi tra i due percorsi
- **È indistinguibile dall'originale** — qualsiasi applicazione lo vede come un file normale
- **Sopravvive all'eliminazione del sorgente** — finché esiste almeno un hardlink, i dati rimangono

Questo lo rende ideale per esporre la stessa libreria video a più applicazioni (es. torrent client + Plex/Jellyfin) senza duplicare i file.

---

## 📋 Requisiti di sistema

| Requisito | Dettaglio |
|-----------|-----------|
| OS | Windows 10 / 11 |
| Filesystem | NTFS (hardlink non supportati su FAT32/exFAT) |
| Privilegi | Amministratore (richiesto da `mklink /H`) |
| Python | 3.10+ (solo se si esegue da sorgente) |

---

## 📄 Licenza

MIT — vedi [LICENSE](LICENSE)
