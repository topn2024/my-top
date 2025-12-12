"""
重构后应用测试脚本
验证新架构的功能
"""
import sys
import os

# 添加backend目录到路径
backend_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_dir)

import unittest
from config import TestConfig


class TestFileService(unittest.TestCase):
    """文件服务测试"""

    def setUp(self):
        from services.file_service import FileService
        self.config = TestConfig()
        self.service = FileService(self.config)

    def test_allowed_file(self):
        """测试文件类型验证"""
        # 允许的类型
        self.assertTrue(self.service.allowed_file('test.txt'))
        self.assertTrue(self.service.allowed_file('test.pdf'))
        self.assertTrue(self.service.allowed_file('test.docx'))
        self.assertTrue(self.service.allowed_file('test.md'))

        # 不允许的类型
        self.assertFalse(self.service.allowed_file('test.exe'))
        self.assertFalse(self.service.allowed_file('test.zip'))
        self.assertFalse(self.service.allowed_file('test'))

    def test_validate_file(self):
        """测试文件验证"""
        # 创建模拟文件对象
        class MockFile:
            def __init__(self, filename):
                self.filename = filename

        # 有效文件
        valid_file = MockFile('test.txt')
        is_valid, error = self.service.validate_file(valid_file)
        self.assertTrue(is_valid)
        self.assertEqual(error, '')

        # 无效文件类型
        invalid_file = MockFile('test.exe')
        is_valid, error = self.service.validate_file(invalid_file)
        self.assertFalse(is_valid)
        self.assertIn('不支持的文件类型', error)

        # 空文件名
        empty_file = MockFile('')
        is_valid, error = self.service.validate_file(empty_file)
        self.assertFalse(is_valid)
        self.assertIn('文件名为空', error)


class TestConfig(unittest.TestCase):
    """配置模块测试"""

    def test_config_init(self):
        """测试配置初始化"""
        from config import Config

        self.assertIsNotNone(Config.SECRET_KEY)
        self.assertIsNotNone(Config.UPLOAD_FOLDER)
        self.assertIsNotNone(Config.QIANWEN_API_KEY)

    def test_config_environments(self):
        """测试不同环境配置"""
        from config import DevelopmentConfig, ProductionConfig, TestConfig

        # 开发环境
        dev_config = DevelopmentConfig()
        self.assertTrue(dev_config.DEBUG)

        # 生产环境
        prod_config = ProductionConfig()
        self.assertFalse(prod_config.DEBUG)

        # 测试环境
        test_config = TestConfig()
        self.assertTrue(test_config.TESTING)


class TestAppFactory(unittest.TestCase):
    """应用工厂测试"""

    def test_create_app(self):
        """测试应用创建"""
        from app_factory import create_app

        app = create_app('testing')
        self.assertIsNotNone(app)
        self.assertTrue(app.config['TESTING'])

    def test_blueprints_registered(self):
        """测试蓝图注册"""
        from app_factory import create_app

        app = create_app('testing')

        # 检查蓝图是否注册
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        self.assertIn('pages', blueprint_names)
        self.assertIn('auth', blueprint_names)
        self.assertIn('api', blueprint_names)


def run_tests():
    """运行测试"""
    print("="*70)
    print("  重构代码测试")
    print("="*70)
    print()

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestFileService))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestAppFactory))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("="*70)
    if result.wasSuccessful():
        print("  ✅ 所有测试通过")
    else:
        print("  ❌ 部分测试失败")
    print("="*70)
    print(f"  运行: {result.testsRun}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print("="*70)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
