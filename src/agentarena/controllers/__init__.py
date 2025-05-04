"""
Controllers package for the Agent Arena application.
"""

from .agent_controller import router as agent_router
from .arena_controller import router as arena_router
from .contest_controller import router as contest_router
from .feature_controller import router as feature_router
from .responder_controller import router as responder_router
from .roundstats_controller import router as roundstats_router
from .strategy_controller import router as strategy_router

routers = [
    agent_router,
    arena_router,
    contest_router,
    feature_router,
    responder_router,
    roundstats_router,
    strategy_router,
]
