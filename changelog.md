# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-09

### Added

- Journalisering af "Uden fast bopæl"-anmodninger: linear framework der hver nat
  læser selvbetjenings-mails fra Outlook-mappen "Selvbetjening UA og UFB", opretter
  en sag i KMD Nova, journaliserer mailen, opretter en opgave og flytter mailen til
  "Slettetmappen 6". Bruger itk_dev_shared_components til Nova og Graph.
- `RPA-PLAYBOOK.md` med genbrugelig standardproces for, hvordan en ny PDD samles op
  og implementeres som RPA.
- `local_debug.py` + `.env.example`: lokalt debug-setup der kører processen direkte
  mod en test-OpenOrchestrator (uden retry-loop og fejl-screenshots).
- `debug_parse_eml.py` + eksempel-mail: offline-test af mail-filter og CPR-udtræk
  fra en gemt `.eml`-fil (uden netværk/Nova/Graph).
- Dry-run-tilstand styret via process arguments (`{"dry_run": true}`) samt en
  `max_mails`-grænse, så robotten kan testes mod produktion uden at oprette sager
  eller flytte mails.

### Kendte mangler

- To værdier afventer fagperson og er markeret med `TODO` i `robot_framework/config.py`
  (postkasse-adresse + UUID for dokumentkategori "Ansøgning"). De holder bevidst
  linting/CI rød, indtil de udfyldes.
