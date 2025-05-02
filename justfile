[working-directory: "frontend"]
web:
    pnpm run dev

[working-directory: "src"]
server: checkvenv
    python -m agentarena.server

checkvenv:
    echo "If this fails, activate venv: $VIRTUAL_ENV"

load:
    python etc/bin/load_fixtures.py etc/fixtures
    