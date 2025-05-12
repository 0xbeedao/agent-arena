all: roll-logs
    just server & just poller & wait

[working-directory: "frontend"]
web:
    pnpm run dev

roll-log FILE ARCHIVE_DIR:
    if [ -f "{{FILE}}" ]; then \
        TIMESTAMP=$(date +%Y%m%d-%H%M%S); \
        mv "{{FILE}}" "{{ARCHIVE_DIR}}/{{FILE}}-${TIMESTAMP}"; \
        echo "Log rolled successfully: {{FILE}} moved to {{ARCHIVE_DIR}}/{{FILE}}-${TIMESTAMP}"; \
    else \
        echo "Error: File {{FILE}} does not exist."; \
    fi

roll-logs:
    just roll-log agentarena-core.log logs
    just roll-log agentarena-poller.log logs

server: checkvenv
    BETTER_EXCEPTIONS=1 python etc/bin/agentarena.server | tee agentarena-core.log

poller: checkvenv
    BETTER_EXCEPTIONS=1 python etc/bin/agentarena.poller | tee agentarena-poller.log

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
