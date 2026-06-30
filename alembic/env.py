import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config

from alembic import context

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings
from app.database import Base

# Import models to ensure they are registered with SQLAlchemy's metadata
from app.modules.users.models import User
from app.modules.workspaces.models import Workspace, WorkspaceMember
from app.modules.projects.models import Project
from app.modules.tasks.models import Task, Label, TaskLabel, TaskComment


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Hàm thực thi chạy migration chính."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(connectable: AsyncEngine) -> None:
    """Tạo connection và liên kết context một cách async."""
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    # Lấy cấu hình mặc định từ file alembic.ini
    configuration = config.get_section(config.config_ini_section, {})
    
    # Ghi đè URL mặc định bằng URL lấy từ file .env qua Pydantic
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    if isinstance(connectable, AsyncEngine):
        # Chạy vòng lặp sự kiện async chuẩn hóa
        asyncio.run(run_async_migrations(connectable))
    else:
        with connectable.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata
            )
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()