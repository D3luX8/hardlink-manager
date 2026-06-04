# Guida d'uso — HardLink Manager

## Modalità Cartella

Usa questa modalità quando vuoi collegare tutti i file video contenuti in una cartella (e relative sottocartelle) verso una destinazione.

1. Seleziona la **cartella sorgente** (es. `E:\DOWNLOAD\TORRENT\One Piece`)
2. Attiva o disattiva le **estensioni** desiderate cliccando sui chip (mkv, mp4, avi…)
3. Seleziona la **cartella di destinazione** (es. `E:\PLEX\ANIME\ONE PIECE`)
4. Clicca **▶ Esegui ora**

La struttura di sottocartelle viene ricreata nella destinazione. Ad esempio:

```
Sorgente:      E:\DOWNLOAD\TORRENT\One Piece\Season 1\ep01.mkv
Destinazione:  E:\PLEX\ANIME\ONE PIECE\Season 1\ep01.mkv  ← hardlink
```

## Modalità File singoli

Usa questa modalità per selezionare manualmente uno o più file specifici.

1. Clicca **+ Aggiungi file…** e seleziona i file
2. Rimuovi eventuali file indesiderati con il pulsante **✕**
3. Seleziona la **cartella di destinazione**
4. Clicca **▶ Esegui ora**

Tutti i file vengono collegati direttamente nella radice della cartella di destinazione (senza sottocartelle).

## Opzioni

| Opzione | Descrizione |
|---------|-------------|
| Salta file già esistenti | Non sovrascrive hardlink già presenti nella destinazione |
| Log dettagliato | Mostra ogni file processato nel pannello output |
| Dry-run | Simula l'operazione senza creare nulla — utile per verificare i percorsi prima di eseguire |
| Ricerca ricorsiva | (Modalità Cartella) Scansiona anche le sottocartelle |

## Salva .ps1

Il pulsante **💾 Salva .ps1** esporta lo script PowerShell generato internamente. Utile per:
- Schedulare l'operazione con Task Scheduler
- Riutilizzarla senza aprire l'interfaccia grafica
- Verificare esattamente cosa verrà eseguito

## Note importanti

- Gli hardlink funzionano **solo su NTFS** — sorgente e destinazione devono essere sullo **stesso volume** (stesso disco/partizione)
- L'applicazione richiede **privilegi di Amministratore** per eseguire `mklink /H`
- Un hardlink non è una copia: modificare o eliminare il file in un percorso non influenza l'altro percorso, ma i dati fisici su disco sono condivisi
