all: roll-logs
    just server & just poller & wait

roll-log FILE ARCHIVE_DIR:
    if [ -f "{{FILE}}" ]; then \
        TIMESTAMP=$(date +%Y%m%d-%H%M%S); \
        mv "{{FILE}}" "{{ARCHIVE_DIR}}/{{FILE}}-${TIMESTAMP}"; \
        echo "Log rolled successfully: {{FILE}} moved to {{ARCHIVE_DIR}}/{{FILE}}-${TIMESTAMP}"; \
    else \
        echo "Error: File {{FILE}} does not exist."; \
    fi

roll-logs:
    just roll-log agentarena-arena.log logs
    just roll-log agentarena-scheduler.log logs

[working-directory: "src"]
server: checkvenv
    just roll-log agentarena-arena.log logs
    python scripts/agentarena.server | tee agentarena-arena.log

[working-directory: "src"]
scheduler: checkvenv
    just roll-log agentarena-scheduler.log logs
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

