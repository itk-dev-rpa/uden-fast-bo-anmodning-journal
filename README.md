# Uden fast bopæl – journalisering

An RPA robot for [OpenOrchestrator](https://github.com/itk-dev-rpa/OpenOrchestrator) that
automatically journalizes citizen self-service requests for *"Uden fast bopæl i en midlertidig
periode"* in KMD Nova.

## What it does

The robot runs nightly. It reads new request mails from a shared Outlook folder and, for each
mail, creates and populates a case in KMD Nova:

1. Read mails from the folder `Selvbetjening UA og UFB` in the shared mailbox (oldest first).
2. Keep only mails from `selvbetjening.aarhuskommune.dk` with a valid "Uden fast bopæl" subject
   (the folder also holds unrelated UA mails).
3. Extract the citizen's CPR number from the mail body.
4. Create a case `Folkeregistrering i almindelighed` (KLE `23.05.00`) on the citizen.
5. Journalize the mail on the case as an incoming document.
6. Create a task on the case.
7. Move the mail to the folder `Slettetmappen 6`.

If there are no matching mails the run stops without doing anything.

## Systems

Both integrations use [itk_dev_shared_components](https://github.com/itk-dev-rpa/itk_dev_shared_components):

- **Microsoft Graph** – read and move mail in the shared mailbox.
- **KMD Nova** – create cases, documents and tasks.

## Framework

This robot uses the **linear** framework (the mail folder acts as the work queue, so no
OpenOrchestrator queue is needed). The choice is made in `robot_framework/__main__.py`. The core
logic lives in `robot_framework/process.py`; `initialize.py` and `reset.py` are minimal since the
robot only talks to APIs (no desktop applications).

## Configuration

Process settings live in `robot_framework/config.py` (mailbox, folders, sender/subject filters,
case title, KLE number, proceeding facet, departments, caseworker, document and task settings).

Credentials and constants are stored in OpenOrchestrator and referenced by name:

| Name | Type | Notes |
|------|------|-------|
| `Nova API` | Credential | `username` = client id, `password` = client secret |
| `Graph API` | Credential | `username` = login user, `password` = JSON with `password`, `client_id`, `tenant_id` |
| `Error Email` | Constant | Recipient for error screenshots |

### Open items

Two values still need confirmation from the business owner and are marked with `# TODO` in
`config.py`. The `fixme` warnings **intentionally keep CI red** until they are filled in:

- `MAILBOX` – the mailbox that actually holds the `Selvbetjening UA og UFB` folder.
- `DOCUMENT_CATEGORY_UUID` – Nova only accepts the document category `Ansøgning` by UUID. Until
  it is set, the mail is journalized without a category.

## Running

In production the robot is started by OpenOrchestrator, which runs `main.py`. This changes the
working directory, sets up a virtual environment with `uv`, and runs `python -m robot_framework`
with the connection arguments from the Scheduler.

### Process arguments

The robot accepts an optional JSON object as its process arguments:

| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `dry_run` | bool | `false` | If `true`, make no changes: only read-only Nova lookups and logging of intended actions. |
| `max_mails` | int | no limit | Process at most this many mails. |

## Local development and debugging

1. Create the environment: `uv venv --python 3.11` then `uv pip install -e ".[dev]"`.
2. Copy `.env.example` to `.env` and fill in the OpenOrchestrator connection settings.
3. Debug with the VS Code launch configs (or run the scripts directly):
   - **`local_debug.py`** – runs the process once against the connection in `.env`, bypassing the
     retry loop and error screenshots. Set `OO_PROCESS_ARGS={"dry_run": true}` to test safely.
   - **`debug_parse_eml.py`** – parses a saved `.eml` file and runs the sender/subject filter and
     CPR extraction offline, with no network, Nova or Graph access.

### Testing against production

There is no test environment, so all testing hits production KMD Nova and the real mailbox. Test
in careful, staged steps:

1. **Offline** – `debug_parse_eml.py` against saved `.eml` files (zero risk).
2. **Dry-run** – `local_debug.py` with `{"dry_run": true}`: verifies the full chain (auth → read
   mail → filter → CPR → read-only Nova lookup) without writing anything.
3. **One live mail** – `{"dry_run": false, "max_mails": 1}`: create one real case and verify it in
   KMD Nova, then confirm the mail moved to `Slettetmappen 6`.
4. **Full run** – no `max_mails`, `dry_run` off.

## Linting

`flake8` and `pylint` run in GitHub Actions on every pull request
(`.github/workflows/Linting.yml`). A version bump (`Version_Check.yml`) and a `changelog.md`
update (`Changelog.yml`) are also required to merge.

## Requirements

Python 3.11+.

## See also

`RPA-PLAYBOOK.md` – the reusable standard process for building a new RPA from a PDD.
