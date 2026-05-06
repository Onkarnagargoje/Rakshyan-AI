"""
Python automatically imports `sitecustomize` (if present on sys.path) during interpreter startup.

We use it to ensure Windows async compatibility for psycopg in SQLAlchemy async mode.
This must run BEFORE Uvicorn creates the event loop.
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

