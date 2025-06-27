# Plan Publikacji: Claude Session Monitor

## Cele
Opublikować prosty skrypt do monitorowania sesji Claude na GitHub jako narzędzie open-source dla użytkowników macOS.

**Inspiracja:** https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor - pomysł mi się podobał, ale technicznie projekt nie spełniał moich wymogów, więc stworzyłem własną implementację.

## Co trzeba zrobić

### 1. Przygotowanie struktury (30 min)
```
claude-session-monitor/
├── README.md
├── LICENSE  
├── claude_monitor.py
└── pyproject.toml (opcjonalnie)
```

### 2. README.md (1 godz)
**Sekcje:**
- Opis (2-3 zdania o tym co robi)
- Wymagania (macOS, Python 3.9+, ccusage)
- Instalacja:
  ```markdown
  1. Install ccusage following: https://github.com/ryoppippi/ccusage
  2. Download: curl -O https://raw.githubusercontent.com/USER/claude-session-monitor/main/claude_monitor.py
  3. Run: python claude_monitor.py
  ```
- Co pokazuje (aktualne tokeny, maksimum, procent wykorzystania, powiadomienia)
- Użycie i opcje:
  ```
  python3 claude_monitor.py --help
  usage: claude_monitor.py [-h] [--start-day START_DAY] [--recalculate] [--test-alert]

  Claude Session Monitor - Monitor Claude API token and cost usage.

  options:
    -h, --help            show this help message and exit
    --start-day START_DAY
                          Day of the month the billing period starts.
    --recalculate         Forces re-scanning of history to update 
                          stored values (max tokens and costs).
    --test-alert          Sends a test system notification (macOS only) and exits.
  ```
- Konfiguracja (plik ~/.config/claude-monitor/config.json)
- Licencja & Credits (inspiracja: https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor)

### 3. Licencja (5 min)
- MIT License z Twoim imieniem

### 4. Cleanup kodu (30 min)
- Dodać `--version`
- Sprawdzić czy działa po skopiowaniu do nowego folderu
- Ewentualnie przetłumaczyć komentarze na angielski

### 5. Publikacja (15 min)
- Utworzyć repo na GitHub
- Pierwsza publikacja
- Dodać topics: `claude`, `monitoring`, `macos`

## Czas realizacji: 2-3 godziny

## Co NIE robić
- ❌ Osobny INSTALLATION.md (wystarczy sekcja w README)
- ❌ Katalog docs/ z podkatalogami
- ❌ .github/workflows (brak testów do uruchomienia)
- ❌ Issue templates (prosty projekt)
- ❌ Screenshoty (tekst wystarczy)
- ❌ Testy kompatybilności na różnych wersjach
- ❌ Przykłady konfiguracji (dokumentacja w README wystarcza)
