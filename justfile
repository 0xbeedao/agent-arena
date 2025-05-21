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
    just roll-log agentarena-scheduler.log logs

[working-directory: "src"]
server: checkvenv
    python scripts/agentarena.server | tee agentarena-core.log

[working-directory: "src"]
scheduler: checkvenv
    python scripts/agentarena.scheduler | tee agentarena-scheduler.log

checkvenv:
    echo "If this fails, activate venv: $VIRTUAL_ENV"

[working-directory: "src"]
load: checkvenv
    python scripts/load_fixtures.py etc/fixtures

test: checkvenv
    PYTHONPATH=src pytest

[working-directory: "src"]
lint:
    autoflake -r -v -i --remove-all-unused-imports ./*
    isort --sl .
    black .

clean:
    rm arena.db

nats:
    nats-server -l logs/nats.log &
    
