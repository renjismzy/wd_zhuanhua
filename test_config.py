#!/usr/bin/env python3
"""
测试服务配置
"""

import sys
import os
from config import config
from document_converter import DocumentConverter

def test_config():
    """测试配置"""
    print("🔧 测试服务配置...")
    
    # 验证配置
    errors = config.validate()
    if errors:
        print("❌ 配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ 配置验证通过")
    
    # 显示当前配置
    print("\n📋 当前配置:")
    config_dict = config.to_dict()
    for section, values in config_dict.items():
        print(f"  {section}:")
        for key, value in values.items():
            print(f"    {key}: {value}")
    
    # 测试文档转换器
    print("\n🔄 测试文档转换器...")
    try:
        converter = DocumentConverter()
        formats = converter.get_supported_formats()
        print(f"✅ 支持的格式: {formats}")
        
        # 测试格式支持
        supported_formats = converter.supported_formats
        print("\n📝 格式支持详情:")
        for fmt, capabilities in supported_formats.items():
            read_status = "✅" if capabilities['read'] else "❌"
            write_status = "✅" if capabilities['write'] else "❌"
            print(f"  {fmt}: 读取{read_status} 写入{write_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文档转换器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_temp_directory():
    """测试临时目录"""
    print("\n📁 测试临时目录...")
    
    temp_dir = config.temp_dir
    print(f"临时目录: {temp_dir}")
    
    # 检查目录是否存在
    if os.path.exists(temp_dir):
        print("✅ 临时目录存在")
        
        # 测试写入权限
        try:
            test_file = os.path.join(temp_dir, "test_write.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print("✅ 临时目录可写")
            return True
        except Exception as e:
            print(f"❌ 临时目录不可写: {e}")
            return False
    else:
        print("❌ 临时目录不存在")
        try:
            os.makedirs(temp_dir, exist_ok=True)
            print("✅ 已创建临时目录")
            return True
        except Exception as e:
            print(f"❌ 无法创建临时目录: {e}")
            return False

def main():
    """主函数"""
    print("🚀 开始服务配置测试\n")
    
    success = True
    
    # 测试配置
    if not test_config():
        success = False
    
    # 测试临时目录
    if not test_temp_directory():
        success = False
    
    print("\n" + "="*50)
    if success:
        print("✅ 所有配置测试通过！服务配置可以正常使用。")
        return 0
    else:
        print("❌ 配置测试失败！请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())