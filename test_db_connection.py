#!/usr/bin/env python3
"""
数据库连接测试脚本
用于测试PostgreSQL数据库连接和pgvector扩展
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_database_connection():
    """
    测试数据库连接功能
    检查PostgreSQL连接、pgvector扩展和表结构
    """
    try:
        import psycopg
        print("✅ psycopg 导入成功")
    except ImportError as e:
        print(f"❌ psycopg 导入失败: {e}")
        print("请运行: poetry add psycopg-binary")
        return False
    
    # 获取数据库连接字符串
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ 未找到 DATABASE_URL 环境变量")
        print("请在 .env 文件中设置 DATABASE_URL")
        print("示例: DATABASE_URL=postgresql://username:password@host:port/database")
        return False
    
    print(f"🔗 尝试连接数据库: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    try:
        # 建立数据库连接
        with psycopg.connect(database_url) as conn:
            print("✅ 数据库连接成功")
            
            with conn.cursor() as cur:
                # 检查PostgreSQL版本
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"📊 PostgreSQL版本: {version.split(',')[0]}")
                
                # 检查pgvector扩展
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'vector'
                    );
                """)
                has_vector = cur.fetchone()[0]
                if has_vector:
                    print("✅ pgvector 扩展已安装")
                else:
                    print("❌ pgvector 扩展未安装")
                    print("请运行: CREATE EXTENSION vector;")
                    return False
                
                # 检查items表是否存在
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = 'items'
                    );
                """)
                has_items_table = cur.fetchone()[0]
                if has_items_table:
                    print("✅ items 表存在")
                    
                    # 检查表结构
                    cur.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'items'
                        ORDER BY ordinal_position;
                    """)
                    columns = cur.fetchall()
                    print("📋 表结构:")
                    for col_name, col_type in columns:
                        print(f"   - {col_name}: {col_type}")
                    
                    # 检查表中数据数量
                    cur.execute("SELECT COUNT(*) FROM items;")
                    count = cur.fetchone()[0]
                    print(f"📊 items 表中有 {count} 条记录")
                    
                else:
                    print("❌ items 表不存在")
                    print("请运行 schema.sql 创建表结构")
                    return False
                
        print("\n🎉 数据库连接测试完成！所有检查都通过了。")
        return True
        
    except psycopg.OperationalError as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n🔧 故障排除建议:")
        print("1. 检查数据库服务器是否运行")
        print("2. 验证连接字符串中的主机名、端口、用户名和密码")
        print("3. 确认网络连接正常")
        print("4. 检查防火墙设置")
        return False
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
        return False

def main():
    """
    主函数：执行数据库连接测试
    """
    print("🚀 开始数据库连接测试...\n")
    
    # 检查OpenAI API密钥（RAG应用需要）
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        print("✅ OPENAI_API_KEY 已设置")
    else:
        print("⚠️  OPENAI_API_KEY 未设置（RAG功能需要）")
    
    print()
    
    # 执行数据库连接测试
    success = test_database_connection()
    
    if success:
        print("\n✨ 准备就绪！可以运行 RAG 应用了:")
        print("   poetry run python -m rag_demo")
        sys.exit(0)
    else:
        print("\n❌ 测试失败，请解决上述问题后重试")
        sys.exit(1)

if __name__ == "__main__":
    main()