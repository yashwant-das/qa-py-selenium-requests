# Pytest Web & API Testing Framework

[![Python CI Tests](https://github.com/yashwant-das/qa-py-selenium-requests/actions/workflows/ci.yml/badge.svg)](https://github.com/yashwant-das/qa-py-selenium-requests/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Python test framework using Pytest, Selenium, and Requests. It demonstrates web login tests for
[SauceDemo](https://www.saucedemo.com/) and booking API tests for
[Restful-booker](https://restful-booker.herokuapp.com/).

Page objects, API clients, fixtures, and configuration keep test cases separate from reusable framework code.

## Prerequisites

- Python 3.11 or newer. CI covers Python 3.11, 3.13, and 3.15.
- Git and [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.13.4 or newer.
- Chrome, Firefox, or Edge for web tests; Chrome is the default.
- Internet access for the public demo services and Selenium Manager driver downloads.
- Node.js 24 or newer for the Markdown lint hook and the optional Allure command-line tool.
- Java when generating Allure 2 reports.

Dependencies are declared in [pyproject.toml](pyproject.toml), with exact versions and hashes
for direct and transitive dependencies recorded in [uv.lock](uv.lock). The Python 3.11 minimum
supports the current test and development toolchain. Selenium Manager handles driver resolution; the
`webdriver-manager` package is not required.

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yashwant-das/qa-py-selenium-requests.git
   cd qa-py-selenium-requests
   ```

2. Install the project and development tools from the lockfile:

   ```bash
   uv sync --locked
   ```

   uv creates `.venv` automatically. You do not need to activate it; use `uv run` for project commands.
   The default `dev` group includes tests, Ruff, and pre-commit. To choose a Python version explicitly,
   use `uv sync --locked --python 3.15`.

3. Create the local environment file.

   On macOS or Linux:

   ```bash
   cp config/.env.example config/.env
   ```

   On Windows PowerShell:

   ```powershell
   Copy-Item config/.env.example config/.env
   ```

   The copy command normally succeeds silently. `.env` is a hidden file; `ls -la config` shows it on
   macOS and Linux. Copy only during initial setup, since repeating it replaces your local settings.
   The template includes these public demo credentials:

   | Variable | Demo value | Used by |
   | --- | --- | --- |
   | `SAUCE_USERNAME` | `standard_user` | SauceDemo |
   | `SAUCE_PASSWORD` | `secret_sauce` | SauceDemo |
   | `BOOKER_USERNAME` | `admin` | Restful-booker |
   | `BOOKER_PASSWORD` | `password123` | Restful-booker |

   Existing shell environment variables take precedence over `config/.env`. Older templates used
   names such as `API_KEY` and `WEB_USERNAME`; the demo tests do not read those variables.
   Local `.env` files are ignored by Git.

## Run Tests

Run commands from the repository root. `uv run --locked` uses the project environment
and refuses to change an outdated lockfile.

```bash
# All tests, including the public API and browser tests
uv run --locked pytest

# Offline framework regression tests
uv run --locked pytest -m unit

# API tests
uv run --locked pytest -m api

# Browser tests
uv run --locked pytest -m web

# Smoke tests, or just API smoke tests
uv run --locked pytest -m smoke
uv run --locked pytest -m "api and smoke"

# API regression tests
uv run --locked pytest -m regression

# A single test, with verbose output
uv run --locked pytest tests/api/test_booking_api.py::TestBookingAPI::test_update_booking -v

# Parallel execution (pytest-xdist is included)
uv run --locked pytest -n 4
```

API tests create their own bookings and clean them up in fixture teardown, so tests can run individually
or in parallel. Missing API credentials and authentication failures fail the affected tests rather than
silently skipping them. The public demo services may be unavailable or modified by other users.

All browser cases currently have the `web` and `smoke` markers. API cases have `api` and `regression`;
health, authentication, and booking creation also have `smoke`. Framework regressions have `unit`.

### Headless Execution

Set `TEST_ENV=ci` to use headless Chrome locally.

On macOS or Linux:

```bash
TEST_ENV=ci uv run --locked pytest
```

On Windows PowerShell:

```powershell
$env:TEST_ENV = "ci"
uv run --locked pytest
```

## Configuration

The shared fixtures in [conftest.py](conftest.py) load configuration as follows:

1. Load `config/.env` without overriding existing shell environment variables.
2. Read `TEST_ENV`, defaulting to `dev`.
3. Read `config/config.json` relative to the repository, regardless of the working directory.
4. Apply `config/config_<TEST_ENV>.json`, if present. Overrides replace whole top-level values;
   nested dictionaries are not recursively merged.
5. Resolve each credential's `username_env` and `password_env` variable names from the environment.

`config_dev.json` points to the public demos. `config_ci.json` enables headless execution.
`config_staging.json` contains example URLs; replace them before using `TEST_ENV=staging`.
Malformed configuration files raise an error rather than being silently ignored.

Set `browser` in the selected JSON configuration to `chrome`, `firefox`, or `edge`.
Use `LOG_LEVEL` to change framework logging; the default is `INFO`.

## Reports

### HTML Report

```bash
uv run --locked pytest --html=reports/pytest_report.html --self-contained-html
```

Open `reports/pytest_report.html` in your browser.

### Allure Report

Install the Allure 2 command-line tool separately; `allure-pytest` generates results but does not include it.
With Node.js and Java installed, one option is:

```bash
npm install -g allure-commandline@2
uv run --locked pytest --alluredir=reports/allure-results --clean-alluredir
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

`--clean-alluredir` clears previous results before the run so old and new results do not mix.
The framework writes `environment.properties` into the directory supplied by `--alluredir`.

### CI Reports

[GitHub Actions](.github/workflows/ci.yml) runs tests on Python 3.11, 3.13, and 3.15 using headless Chrome
and the public demo credentials. It also checks Python code style and Markdown formatting.

Lint and Markdown checks run once in a separate job. Tests run across the Python matrix with only
framework and test dependencies installed. Each matrix job uploads its Allure results.
A separate publishing job uses Python 3.15 results and carries forward history from `gh-pages`.
Only that publishing job has repository write permission, and publishing jobs run one at a time.
It runs on pushes to `main`, including failed test runs with available Python 3.15 results.
Pull requests upload results without publishing.

Published reports are available on [GitHub Pages](https://yashwant-das.github.io/qa-py-selenium-requests/)
when Pages is configured to serve the `gh-pages` branch.

## Project Structure

```text
qa-py-selenium-requests/
├── .github/
│   ├── dependabot.yml
│   └── workflows/ci.yml
├── .pre-commit-config.yaml
├── .markdownlint-cli2.jsonc
├── config/
│   ├── .env.example
│   ├── .env                 # Local, ignored by Git
│   ├── config.json
│   ├── config_dev.json
│   ├── config_staging.json
│   └── config_ci.json
├── src/
│   ├── api_clients/         # Booking operations
│   ├── base/                # Requests client and Selenium helpers
│   ├── pages/               # SauceDemo page objects
│   └── utils/               # Data generation and logging
├── tests/
│   ├── api/                 # Live Restful-booker tests
│   ├── web/                 # Live SauceDemo tests
│   └── unit/                # Offline framework regressions
├── conftest.py              # Configuration and shared fixtures
├── pytest.ini               # Pytest discovery, markers, logging
├── pyproject.toml           # Package metadata and Ruff settings
├── uv.lock                  # Locked direct and transitive dependencies
└── reports/                 # Generated test reports
```

## Code Quality

Ruff handles Python linting, import sorting, and formatting using `pyproject.toml`.
Markdownlint reads `.markdownlint-cli2.jsonc`.

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
npx --yes markdownlint-cli2@0.24.0
```

To apply safe lint fixes and sort imports, run `uv run --locked ruff check --fix .`.
To format Python code, run `uv run --locked ruff format .`.
Install the optional Git hooks after installing the dependencies:

```bash
uv run --locked pre-commit install
uv run --locked pre-commit run --all-files
```

The hooks check whitespace, file endings, YAML, TOML, Python style, and Markdown.
Ruff hooks use the project lockfile through uv, so they share the same version as CI.
Other hook revisions are pinned in `.pre-commit-config.yaml`.

## Dependency Management

`pyproject.toml` separates framework dependencies from the `test`, `lint`, and `dev` groups.
The `dev` group includes both `test` and `lint`. CI installs only the group it needs:

```bash
# Framework and tests, without lint or pre-commit
uv sync --locked --no-default-groups --group test
uv run --no-sync pytest

# Ruff only, without the framework or tests
uv sync --locked --only-group lint
uv run --no-sync ruff check .

# Restore the complete development environment
uv sync --locked
```

`uv sync` replaces the environment to match the selected groups. After a targeted sync, use
`uv run --no-sync` to keep that selection; ordinary `uv run --locked` restores the default `dev` group.

For intentional dependency changes, edit `pyproject.toml` (or use `uv add`), then run `uv lock`,
`uv sync --locked`, and the checks. Commit `pyproject.toml` and `uv.lock` together.
`uv lock --upgrade` refreshes dependencies within the declared constraints; exact direct pins must
be changed explicitly before those packages can upgrade.

Dependabot checks uv dependencies and GitHub Actions weekly. Minor and patch updates are grouped;
major updates get separate pull requests. No updates are merged automatically. Other pre-commit hooks can be updated with
`uv run --locked pre-commit autoupdate`.

The former `requirements.txt` setup is replaced by `uv sync --locked`. A plain `pip install .`
installs framework dependencies only and does not reproduce the locked test environment.

## Contributing

1. Create a branch for your change.
2. Add regression tests for behavior changes.
3. Run the relevant tests and code-quality checks above.
4. Run the full suite against the public demos before opening a pull request.
5. Push the branch and open a pull request with a description of the change and validation.

## License

[MIT](LICENSE).
