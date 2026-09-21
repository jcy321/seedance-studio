from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    from app.models.base import Base
    import app.models.user  # noqa
    import app.models.user_settings  # noqa
    import app.models.project  # noqa
    import app.models.script  # noqa
    import app.models.character  # noqa
    import app.models.storyboard  # noqa
    import app.models.asset  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
