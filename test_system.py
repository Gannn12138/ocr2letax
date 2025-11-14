#!/usr/bin/env python3
"""
系统测试脚本
用于验证OCR2LATEX系统的基本功能
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from src.config import MATHPIX_APP_ID, MATHPIX_APP_KEY
        print("   ✅ config模块导入成功")
        
        from src.image_processor import image_processor
        print("   ✅ image_processor模块导入成功")
        
        from src.mathpix_client import mathpix_client
        print("   ✅ mathpix_client模块导入成功")
        
        from src.result_processor import result_processor
        print("   ✅ result_processor模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False

def test_dependencies():
    """测试依赖库"""
    print("\n📦 测试依赖库...")
    
    dependencies = [
        ('cv2', 'opencv-python'),
        ('PIL', 'Pillow'),
        ('numpy', 'numpy'),
        ('requests', 'requests')
    ]
    
    missing_deps = []
    
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"   ✅ {package_name} 已安装")
        except ImportError:
            print(f"   ❌ {package_name} 未安装")
            missing_deps.append(package_name)
    
    if missing_deps:
        print(f"\n⚠️  缺少依赖: {', '.join(missing_deps)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def test_api_config():
    """测试API配置"""
    print("\n🔑 测试API配置...")
    
    try:
        from src.mathpix_client import mathpix_client
        
        if mathpix_client.check_credentials():
            print("   ✅ API密钥配置正确")
            return True
        else:
            print("   ⚠️  API密钥未配置或无效")
            print("   请在 src/config.py 中设置您的Mathpix API密钥")
            return False
            
    except Exception as e:
        print(f"   ❌ API配置检查失败: {e}")
        return False

def test_directories():
    """测试目录结构"""
    print("\n📁 测试目录结构...")
    
    required_dirs = ['src', 'templates', 'uploads', 'results']
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"   ✅ {dir_name}/ 目录存在")
        else:
            print(f"   ❌ {dir_name}/ 目录不存在")
            return False
    
    return True

def test_image_processor():
    """测试图像处理器"""
    print("\n🖼️  测试图像处理器...")
    
    try:
        from src.image_processor import image_processor
        import numpy as np
        
        # 创建测试图像
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image.fill(255)  # 白色背景
        
        # 测试base64编码
        base64_str = image_processor.image_to_base64(test_image)
        
        if base64_str:
            print("   ✅ 图像处理器工作正常")
            return True
        else:
            print("   ❌ 图像处理器测试失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 图像处理器测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 OCR2LATEX 系统测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_dependencies,
        test_directories,
        test_image_processor,
        test_api_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统准备就绪。")
        print("\n💡 下一步:")
        print("   1. 配置Mathpix API密钥（如果还未配置）")
        print("   2. 运行: python main.py your_image.jpg")
    else:
        print("⚠️  部分测试失败，请检查上述问题。")
        
        if passed >= 3:  # 基本功能可用
            print("\n💡 基本功能可用，可以尝试运行主程序。")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

