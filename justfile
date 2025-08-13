all: checkvenv roll-logs
    just actor & just arena & just scheduler & wait

roll-log FILE ARCHIVE_DIR:
    if [ -f "{{FILE}}" ]; then \
        TIMESTAMP=$(date +%Y%m%d-%H%M%S); \
        mv "{{FILE}}" "{{ARCHIVE_DIR}}/{{FILE}}-${TIMESTAMP}"; \
        echo "Log rolled successfully: {{FILE}} moved to {{ARCHIVE_DIR}}/{{FILE}}-${TIMESTAMP}"; \
    else \
        echo "Error: File {{FILE}} does not exist."; \
    fi

roll-logs:
    just roll-log arena.log logs
    just roll-log scheduler.log logs
    just roll-log actor.log logs
    just roll-log control.log logs

actor:
    just roll-log actor.log logs
    PYTHONPATH=. python scripts/agentarena.actor

control:
    PYTHONPATH=. python scripts/agentarena.control

arena:
    just roll-log arena.log logs
    PYTHONPATH=. python scripts/agentarena.arena

scheduler:
    just roll-log scheduler.log logs
    PYTHONPATH=. python scripts/agentarena.scheduler

checkvenv:
    echo "If this fails, activate venv: $VIRTUAL_ENV"

kill:
    ps ax | grep python | grep agent | grep -v lsp | awk '{print $1}' | xargs kill -9

load:
    PYTHONPATH=. python scripts/load_fixtures.py etc/fixtures

test:
    PYTHONPATH=. pytest

lint:
    autoflake -r -v -i --remove-all-unused-imports agentarena/*
    isort --sl --gitignore agentarena
    black agentarena notebooks

model-backup:
    sqlite3 actor.db ".dump llmmodel" > etc/llmmodel.sql
    sqlite3 actor.db ".dump llmmodelprice" > etc/llmmodelprice.sql
    sqlite3 actor.db ".dump llmmodelstats" > etc/llmmodelstats.sql

model-restore:
    sqlite3 actor.db < etc/llmmodel.sql
    sqlite3 actor.db < etc/llmmodelprice.sql
    sqlite3 actor.db < etc/llmmodelstats.sql

clean:
    rm *.db

nats:
    nats-server -l logs/nats.log &

start:
    xh post :8000/api/contest/$ARENA_LAST_CONTEST/start

reset-contests:
    sqlite3 arena.db 'update contest set state="CREATED";'

