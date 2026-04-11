import unittest
from app.models.user import User
from app.rbac import role_has_permission

class RBACBasicTest(unittest.TestCase):
    def setUp(self):
        self.super_admin = User(username='super', email='super@x.de', role='super_admin', is_active=True)
        self.admin = User(username='admin', email='admin@x.de', role='admin', is_active=True)
        self.user = User(username='user', email='user@x.de', role='user', is_active=True)

    def test_super_admin_permissions(self):
        self.assertTrue(self.super_admin.has_permission('manage_users'))
        self.assertTrue(self.super_admin.has_permission('manage_roles'))
        self.assertTrue(self.super_admin.has_permission('view_system_logs'))
        self.assertTrue(self.super_admin.is_super_admin())

    def test_admin_permissions(self):
        self.assertTrue(self.admin.has_permission('manage_users'))
        self.assertFalse(self.admin.has_permission('manage_feature_flags'))
        self.assertTrue(self.admin.is_admin())
        self.assertFalse(self.admin.is_super_admin())

    def test_user_permissions(self):
        self.assertTrue(self.user.has_permission('use_search'))
        self.assertFalse(self.user.has_permission('manage_users'))
        self.assertFalse(self.user.is_admin())

    def test_role_has_permission(self):
        self.assertTrue(role_has_permission('admin', 'manage_users'))
        self.assertFalse(role_has_permission('user', 'manage_users'))

if __name__ == '__main__':
    unittest.main()
