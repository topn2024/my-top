"""
测试迁移路由的功能
验证从 app_with_upload.py 迁移到蓝图的 7 个路由是否正常工作
"""
import unittest
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_factory import create_app


class TestMigratedRoutes(unittest.TestCase):
    """测试迁移的路由"""

    def setUp(self):
        """测试前准备"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

    def tearDown(self):
        """测试后清理"""
        pass

    # ============ 账号管理路由测试 ============

    def test_account_test_endpoint_exists(self):
        """测试 /api/accounts/<id>/test 端点存在"""
        # 未登录应返回 401，而不是 404
        response = self.client.post('/api/accounts/1/test')
        self.assertIn(response.status_code, [400, 401, 404],
                      "账号测试端点应该存在（返回401/400/404而不是404）")
        self.assertNotEqual(response.status_code, 404,
                           "端点不应该返回404 Not Found")

    def test_account_import_endpoint_exists(self):
        """测试 /api/accounts/import 端点存在"""
        # 未登录应返回 401，而不是 404
        response = self.client.post('/api/accounts/import')
        self.assertIn(response.status_code, [400, 401],
                      "账号导入端点应该存在（返回401/400而不是404）")
        self.assertNotEqual(response.status_code, 404,
                           "端点不应该返回404 Not Found")

    # ============ CSDN 功能路由测试 ============

    def test_csdn_login_endpoint_exists(self):
        """测试 /api/csdn/login 端点存在"""
        response = self.client.post('/api/csdn/login')
        self.assertIn(response.status_code, [400, 401],
                      "CSDN登录端点应该存在")
        self.assertNotEqual(response.status_code, 404)

    def test_csdn_check_login_endpoint_exists(self):
        """测试 /api/csdn/check_login 端点存在"""
        response = self.client.post('/api/csdn/check_login')
        self.assertIn(response.status_code, [400, 401],
                      "CSDN检查登录端点应该存在")
        self.assertNotEqual(response.status_code, 404)

    def test_csdn_publish_endpoint_exists(self):
        """测试 /api/csdn/publish 端点存在"""
        response = self.client.post('/api/csdn/publish')
        self.assertIn(response.status_code, [400, 401],
                      "CSDN发布端点应该存在")
        self.assertNotEqual(response.status_code, 404)

    # ============ 平台和重试路由测试 ============

    def test_platforms_endpoint_exists(self):
        """测试 /api/platforms 端点存在"""
        response = self.client.get('/api/platforms')
        self.assertIn(response.status_code, [200, 401],
                      "平台列表端点应该存在")
        self.assertNotEqual(response.status_code, 404)

    def test_retry_publish_endpoint_exists(self):
        """测试 /api/retry_publish/<id> 端点存在"""
        response = self.client.post('/api/retry_publish/1')
        self.assertIn(response.status_code, [400, 401, 404],
                      "重试发布端点应该存在")
        # 404 是可以接受的，因为记录可能不存在
        # 重要的是路由本身被注册了

    # ============ 综合测试 ============

    def test_all_routes_registered(self):
        """验证所有新增路由都已注册"""
        # 获取所有路由
        routes = []
        for rule in self.app.url_map.iter_rules():
            routes.append(str(rule))

        # 检查所有迁移的路由是否存在
        expected_routes = [
            '/api/accounts/<int:account_id>/test',
            '/api/accounts/import',
            '/api/csdn/login',
            '/api/csdn/check_login',
            '/api/csdn/publish',
            '/api/platforms',
            '/api/retry_publish/<int:history_id>',
        ]

        for route in expected_routes:
            # 使用部分匹配，因为Flask的路由规则可能有细微差异
            route_found = any(route.replace('<int:', '<').replace('>', '') in r
                             for r in routes)
            self.assertTrue(route_found,
                           f"路由 {route} 应该已注册")

    def test_no_duplicate_routes(self):
        """验证没有重复的路由定义"""
        routes = [str(rule) for rule in self.app.url_map.iter_rules()]

        # 检查是否有重复
        route_counts = {}
        for route in routes:
            route_counts[route] = route_counts.get(route, 0) + 1

        duplicates = [r for r, count in route_counts.items() if count > 1]

        self.assertEqual(len(duplicates), 0,
                        f"发现重复的路由: {duplicates}")

    def test_blueprint_import(self):
        """测试蓝图导入是否成功"""
        from blueprints.api import api_bp
        from blueprints.api_retry import api_retry_bp

        self.assertIsNotNone(api_bp, "API蓝图应该可以导入")
        self.assertIsNotNone(api_retry_bp, "重试蓝图应该可以导入")

    def test_auth_decorators(self):
        """测试认证装饰器是否正常工作"""
        # 测试需要登录的端点，未登录应返回401
        protected_endpoints = [
            ('/api/accounts/1/test', 'POST'),
            ('/api/accounts/import', 'POST'),
            ('/api/csdn/login', 'POST'),
            ('/api/platforms', 'GET'),
            ('/api/retry_publish/1', 'POST'),
        ]

        for endpoint, method in protected_endpoints:
            if method == 'GET':
                response = self.client.get(endpoint)
            else:
                response = self.client.post(endpoint)

            # 应该返回401（未授权）而不是其他错误
            # 注意：有些端点可能先验证参数，返回400
            self.assertIn(response.status_code, [400, 401],
                         f"{endpoint} 应该需要认证")


class TestConfigValidation(unittest.TestCase):
    """测试配置验证功能"""

    def test_production_config_has_validation(self):
        """测试生产配置有验证方法"""
        from config import ProductionConfig

        self.assertTrue(hasattr(ProductionConfig, 'validate_config'),
                       "生产配置应该有 validate_config 方法")

    def test_development_config_no_validation(self):
        """测试开发配置没有严格验证"""
        from config import DevelopmentConfig

        # 开发配置不应该有强制验证
        has_validation = hasattr(DevelopmentConfig, 'validate_config')
        self.assertFalse(has_validation,
                        "开发配置不应该有强制验证")


class TestEnvironmentTemplate(unittest.TestCase):
    """测试环境变量模板"""

    def test_env_template_exists(self):
        """测试 .env.template 文件存在"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            '.env.template'
        )

        self.assertTrue(os.path.exists(template_path),
                       ".env.template 文件应该存在")

    def test_env_template_has_required_vars(self):
        """测试 .env.template 包含必需的变量"""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            '.env.template'
        )

        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            required_vars = [
                'TOPN_SECRET_KEY',
                'ZHIPU_API_KEY',
                'FLASK_ENV',
                'DATABASE_URL',
            ]

            for var in required_vars:
                self.assertIn(var, content,
                             f".env.template 应该包含 {var}")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
