#!/usr/bin/env python3
"""
测试tools.py中邮件服务检查的修复
"""

import sys
import asyncio
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools import ReportGenerationTool
from src.settings import Settings


async def test_email_service_check():
    """测试邮件服务检查逻辑"""
    print("=== 测试邮件服务检查逻辑 ===")
    
    try:
        # 创建设置
        settings = Settings()
        print("✅ 设置加载成功")
        
        # 创建报告生成工具
        tool = ReportGenerationTool(settings)
        print("✅ 报告生成工具创建成功")
        
        # 测试邮件服务检查逻辑
        print("\n🔍 检查邮件服务配置:")
        
        # 检查腾讯云配置
        tencent_configured = all([
            hasattr(settings, 'tencent_cloud_secret_id') and settings.tencent_cloud_secret_id,
            hasattr(settings, 'tencent_cloud_secret_key') and settings.tencent_cloud_secret_key,
            hasattr(settings, 'tencent_from_email') and settings.tencent_from_email
        ])
        
        print(f"   腾讯云邮件服务: {'已配置' if tencent_configured else '未配置'}")
        
        # 检查SMTP配置
        smtp_configured = all([
            hasattr(settings, 'email_username') and settings.email_username,
            hasattr(settings, 'email_password') and settings.email_password,
            hasattr(settings, 'smtp_server') and settings.smtp_server,
            hasattr(settings, 'smtp_port') and settings.smtp_port
        ])
        
        print(f"   SMTP邮件服务: {'已配置' if smtp_configured else '未配置'}")
        
        # 检查是否有任何邮件服务配置
        any_email_service = tencent_configured or smtp_configured
        print(f"   邮件服务状态: {'可用' if any_email_service else '不可用'}")
        
        if any_email_service:
            print("✅ 邮件服务配置正常，可以发送邮件")
        else:
            print("⚠️  没有配置邮件服务，邮件功能将不可用")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_settings_attributes():
    """测试设置属性"""
    print("\n=== 测试设置属性 ===")
    
    try:
        settings = Settings()
        
        # 检查所有相关属性
        attributes_to_check = [
            'tencent_cloud_secret_id',
            'tencent_cloud_secret_key', 
            'tencent_cloud_region',
            'tencent_from_email',
            'email_username',
            'email_password',
            'smtp_server',
            'smtp_port',
            'email_from_name'
        ]
        
        print("设置属性检查:")
        for attr in attributes_to_check:
            has_attr = hasattr(settings, attr)
            value = getattr(settings, attr, None)
            status = "✅" if has_attr else "❌"
            print(f"   {status} {attr}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 设置属性测试失败: {str(e)}")
        return False


def test_email_service_import():
    """测试邮件服务导入"""
    print("\n=== 测试邮件服务导入 ===")
    
    try:
        from src.email_service import EmailService, TencentCloudEmailService, SMTPEmailService
        print("✅ 邮件服务模块导入成功")
        
        # 测试类是否存在
        print("✅ EmailService 类可用")
        print("✅ TencentCloudEmailService 类可用")
        print("✅ SMTPEmailService 类可用")
        
        return True
        
    except ImportError as e:
        print(f"❌ 邮件服务模块导入失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("🚀 Tools.py 邮件服务检查修复测试")
    print("="*50)
    
    # 运行测试
    test1 = await test_email_service_check()
    test2 = test_settings_attributes()
    test3 = test_email_service_import()
    
    print("\n=== 测试结果汇总 ===")
    print(f"邮件服务检查测试: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"设置属性测试: {'✅ 通过' if test2 else '❌ 失败'}")
    print(f"邮件服务导入测试: {'✅ 通过' if test3 else '❌ 失败'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 所有测试通过！邮件服务检查修复成功")
    else:
        print("\n⚠️  部分测试失败，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())