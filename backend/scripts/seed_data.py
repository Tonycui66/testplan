import asyncio
from uuid import uuid4

from sqlalchemy import text

from app.core.security import hash_password
from app.dependencies import get_database_engine


async def seed() -> None:
    engine = get_database_engine()
    async with engine.begin() as conn:
        role_ids = {}
        for name in ("owner", "member", "viewer"):
            result = await conn.execute(
                text(
                    "INSERT INTO iam.roles (id, name, is_system) VALUES (:id, :name, true) "
                    "ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id"
                ),
                {"id": uuid4(), "name": name},
            )
            role_ids[name] = result.scalar_one()

        result = await conn.execute(
            text(
                "INSERT INTO iam.users (id, email, password_hash, name, is_active, is_superadmin) "
                "VALUES (:id, :email, :password_hash, :name, true, true) "
                "ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email RETURNING id"
            ),
            {
                "id": uuid4(),
                "email": "admin@example.com",
                "password_hash": hash_password("Admin123!"),
                "name": "Admin",
            },
        )
        admin_id = result.scalar_one()
        await conn.execute(
            text(
                "INSERT INTO iam.user_roles (id, user_id, role_id) VALUES (:id, :user_id, :role_id) "
                "ON CONFLICT (user_id, role_id) DO NOTHING"
            ),
            {"id": uuid4(), "user_id": admin_id, "role_id": role_ids["owner"]},
        )


if __name__ == "__main__":
    asyncio.run(seed())
