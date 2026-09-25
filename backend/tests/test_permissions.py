from app.models.user import User
from app.services.permission_service import PermissionService

def test_permission_checks():
    admin = User(id="1", role="ADMIN")
    manager = User(id="2", role="MANAGER")
    member = User(id="3", role="MEMBER")

    assert PermissionService.can_create_project(admin) is True
    assert PermissionService.can_create_project(manager) is True
    assert PermissionService.can_create_project(member) is False

    assert PermissionService.can_create_task(member) is True
    assert PermissionService.can_assign_task(member) is True
