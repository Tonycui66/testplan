import asyncio
import os
from uuid import uuid4

from sqlalchemy import text

from app.core.security import hash_password
from app.dependencies import get_database_engine


async def seed() -> None:
    admin_email = os.getenv("SEED_ADMIN_EMAIL")
    admin_password = os.getenv("SEED_ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        print("Skipping seed: SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD are required")
        return

    admin_name = os.getenv("SEED_ADMIN_NAME", "Admin")
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
                "email": admin_email,
                "password_hash": hash_password(admin_password),
                "name": admin_name,
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
