#!/usr/bin/env python3
"""
测试MCP服务器API功能的脚本
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any


def test_formats_api():
    """测试格式列表API"""
    print("\n=== 测试支持的格式列表 ===")
    try:
        response = requests.get('http://localhost:8000/formats')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 支持的格式: {data['formats']}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        return False


def test_conversion_api():
    """测试文档转换API"""
    print("\n=== 测试文档转换功能 ===")
    
    # 测试用例
    test_cases = [
        {
            'name': 'Markdown转HTML',
            'source_format': 'md',
            'target_format': 'html',
            'content': '# Hello World\n\nThis is **markdown** text with *emphasis*.'
        },
        {
            'name': 'HTML转文本',
            'source_format': 'html',
            'target_format': 'txt',
            'content': '<h1>Hello World</h1><p>This is <strong>HTML</strong> content.</p>'
        },
        {
            'name': '文本转Markdown',
            'source_format': 'txt',
            'target_format': 'md',
            'content': 'Hello World\n\nThis is plain text content.'
        }
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        try:
            data = {
                'source_format': test_case['source_format'],
                'target_format': test_case['target_format'],
                'content': test_case['content']
            }
            
            response = requests.post('http://localhost:8000/convert', data=data)
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"✅ 转换成功")
                    print(f"输入: {test_case['content'][:50]}...")
                    print(f"输出: {result['content'][:100]}...")
                    success_count += 1
                else:
                    print(f"❌ 转换失败: {result.get('error', '未知错误')}")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"响应: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求错误: {e}")
    
    print(f"\n转换测试结果: {success_count}/{len(test_cases)} 成功")
    return success_count == len(test_cases)


def test_server_health():
    """测试服务器健康状态"""
    print("\n=== 测试服务器健康状态 ===")
    try:
        response = requests.get('http://localhost:8000/formats', timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
        return False
    except requests.exceptions.Timeout:
        print("❌ 服务器响应超时")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试MCP文档转换服务器")
    print("服务器地址: http://localhost:8000")
    
    # 测试服务器健康状态
    if not test_server_health():
        print("\n❌ 服务器未运行，请先启动服务器: python main.py --api")
        return
    
    # 测试各个功能
    results = []
    results.append(test_formats_api())
    results.append(test_conversion_api())
    
    # 总结测试结果
    print("\n" + "="*50)
    print("📊 测试总结")
    print("="*50)
    
    if all(results):
        print("🎉 所有测试通过！MCP服务器功能正常")
        print("\n✨ 功能特性:")
        print("  • 支持多种文档格式转换 (md, html, txt, pdf, docx)")
        print("  • REST API接口")
        print("  • Server-Sent Events (SSE) 支持")
        print("  • MCP协议兼容")
        print("\n🔗 API端点:")
        print("  • GET  /formats     - 获取支持的格式列表")
        print("  • POST /convert     - 文档转换")
        print("  • GET  /events      - SSE事件流")
        print("  • GET  /status/{id} - 获取转换状态")
    else:
        failed_tests = sum(1 for r in results if not r)
        print(f"⚠️  {failed_tests} 个测试失败，请检查服务器配置")


if __name__ == "__main__":
    main()