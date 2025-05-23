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

control: checkvenv
    PYTHONPATH=. python scripts/agentarena.controlpanel

server: checkvenv
    just roll-log agentarena-arena.log logs
    PYTHONPATH=. python scripts/agentarena.server | tee agentarena-arena.log

scheduler: checkvenv
    just roll-log agentarena-scheduler.log logs
    PYTHONPATH=. python scripts/agentarena.scheduler | tee agentarena-scheduler.log

checkvenv:
    echo "If this fails, activate venv: $VIRTUAL_ENV"

load: checkvenv
    PYTHONPATH=. python scripts/load_fixtures.py etc/fixtures

test: checkvenv
    PYTHONPATH=. pytest

lint:
    autoflake -r -v -i --remove-all-unused-imports agentarena/*
    isort --sl --gitignore agentarena
    black agentarena notebooks

clean:
    rm *.db

nats:
    nats-server -l logs/nats.log &

