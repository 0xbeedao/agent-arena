[working-directory: "frontend"]
web:
    pnpm run dev

[working-directory: "src"]
server: checkvenv
    python ../etc/bin/agentarena.server

[working-directory: "src"]
poller: checkvenv
    python ../etc/bin/agentarena.poller


checkvenv:
    echo "If this fails, activate venv: $VIRTUAL_ENV"

load: checkvenv
    python etc/bin/load_fixtures.py etc/fixtures

test: checkvenv
    PYTHONPATH=src pytest

[working-directory: "src"]
lint:
    autoflake -r -v -i --remove-all-unused-imports ./*
    isort --sl .
    black .

clean:
    rm arena.db
