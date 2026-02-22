"""
芯片失效分析AI Agent系统 - RBAC初始化脚本
创建默认角色、权限和超级管理员用户
"""

import asyncio
from datetime import datetime
from loguru import logger

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import get_db_manager
from src.database.rbac_models import (
    User, Role, Permission,
    SystemRoles, SystemPermissions,
    user_role_association,
    role_permission_association
)


async def init_rbac():
    """初始化RBAC系统"""
    logger.info("开始初始化RBAC系统...")

    db_manager = get_db_manager()
    await db_manager.initialize()

    async with db_manager.get_session() as session:
        # ============================================
        # 1. 创建权限
        # ============================================
        logger.info("创建系统权限...")

        existing_permissions = {}
        stmt = select(Permission)
        result = await session.execute(stmt)
        for perm in result.scalars().all():
            existing_permissions[perm.name] = perm

        permissions_to_create = []
        for perm_config in SystemPermissions.get_default_permissions():
            if perm_config["name"] not in existing_permissions:
                perm = Permission(**perm_config)
                permissions_to_create.append(perm)

        if permissions_to_create:
            session.add_all(permissions_to_create)
            await session.commit()
            logger.info(f"创建 {len(permissions_to_create)} 个权限")
        else:
            logger.info("权限已存在，跳过创建")

        # 重新加载权限
        stmt = select(Permission)
        result = await session.execute(stmt)
        all_permissions = {p.name: p for p in result.scalars().all()}

        # ============================================
        # 2. 创建角色
        # ============================================
        logger.info("创建系统角色...")

        existing_roles = {}
        stmt = select(Role)
        result = await session.execute(stmt)
        for role in result.scalars().all():
            existing_roles[role.name] = role

        roles_to_create = []
        for role_config in SystemRoles.get_default_roles():
            if role_config["name"] not in existing_roles:
                role = Role(**role_config)
                roles_to_create.append(role)

        if roles_to_create:
            session.add_all(roles_to_create)
            await session.commit()
            logger.info(f"创建 {len(roles_to_create)} 个角色")
        else:
            logger.info("角色已存在，跳过创建")

        # 重新加载角色
        stmt = select(Role)
        result = await session.execute(stmt)
        all_roles = {r.name: r for r in result.scalars().all()}

        # ============================================
        # 3. 分配权限给角色
        # ============================================
        logger.info("分配权限给角色...")

        role_permissions_map = SystemPermissions.get_role_permissions()

        for role_name, permission_names in role_permissions_map.items():
            role = all_roles.get(role_name)
            if not role:
                continue

            # 获取角色当前权限
            current_perm_names = {p.name for p in role.permissions}

            # 添加缺失的权限
            for perm_name in permission_names:
                if perm_name not in current_perm_names:
                    perm = all_permissions.get(perm_name)
                    if perm:
                        role.permissions.append(perm)

        await session.commit()
        logger.info("角色权限分配完成")

        # ============================================
        # 4. 创建超级管理员用户
        # ============================================
        logger.info("创建超级管理员用户...")

        # 检查超级管理员是否存在
        stmt = select(User).where(User.username == "admin")
        result = await session.execute(stmt)
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            # 创建超级管理员
            from src.auth.service import AuthService
            admin_user = User(
                user_id=AuthService.generate_user_id("admin"),
                username="admin",
                email="admin@chip-fault.local",
                full_name="系统管理员",
                password_hash=AuthService.hash_password("admin123"),
                is_active=True,
                is_verified=True,
                department="IT",
                position="系统管理员",
                created_by="system"
            )

            session.add(admin_user)
            await session.flush()

            # 分配超级管理员角色
            super_admin_role = all_roles.get(SystemRoles.SUPER_ADMIN)
            if super_admin_role:
                admin_user.roles.append(super_admin_role)

            await session.commit()
            logger.info("超级管理员创建成功 - username: admin, password: admin123")
        else:
            # 确保超级管理员拥有超级管理员角色
            super_admin_role = all_roles.get(SystemRoles.SUPER_ADMIN)
            if super_admin_role and super_admin_role not in admin_user.roles:
                admin_user.roles.append(super_admin_role)
                await session.commit()
            logger.info("超级管理员已存在")

    logger.info("RBAC系统初始化完成!")


async def create_test_users():
    """创建测试用户"""
    logger.info("创建测试用户...")

    from src.auth.service import AuthService

    test_users = [
        {
            "username": "expert1",
            "password": "expert123",
            "email": "expert1@chip-fault.local",
            "full_name": "测试专家",
            "department": "研发部",
            "position": "高级工程师",
            "role": SystemRoles.EXPERT
        },
        {
            "username": "analyst1",
            "password": "analyst123",
            "email": "analyst1@chip-fault.local",
            "full_name": "测试分析师",
            "department": "测试部",
            "position": "测试工程师",
            "role": SystemRoles.ANALYST
        },
        {
            "username": "viewer1",
            "password": "viewer123",
            "email": "viewer1@chip-fault.local",
            "full_name": "测试查看者",
            "department": "质量部",
            "position": "质量工程师",
            "role": SystemRoles.VIEWER
        }
    ]

    for user_config in test_users:
        role = user_config.pop("role")
        user = await auth_service.create_user(
            role_names=[role],
            created_by="system",
            **user_config
        )

        if user:
            logger.info(f"测试用户创建成功: {user.username}")
        else:
            logger.warning(f"测试用户创建失败: {user_config['username']}")


async def main():
    """主函数"""
    try:
        # 初始化RBAC
        await init_rbac()

        # 创建测试用户
        await create_test_users()

        logger.info("========================================")
        logger.info("RBAC初始化完成!")
        logger.info("========================================")
        logger.info("默认账户信息:")
        logger.info("  超级管理员: admin / admin123")
        logger.info("  测试专家:   expert1 / expert123")
        logger.info("  测试分析师: analyst1 / analyst123")
        logger.info("  测试查看者: viewer1 / viewer123")
        logger.info("========================================")

    except Exception as e:
        logger.error(f"初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库连接
        db_manager = get_db_manager()
        await db_manager.close()


if __name__ == "__main__":
    auth_service = None
    from src.auth.service import auth_service as service
    auth_service = service

    asyncio.run(main())
