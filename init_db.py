"""
数据库初始化脚本
运行方式：
python init_db.py # 初始化数据库
python init_db.py --reset # 清除所有数据并重新初始化
确保 MySQL 已启动并创建了数据库:
    docker run -d --name mini_kb_mysql \\
      -p 3307:3306 \\
      -e MYSQL_ROOT_PASSWORD=password \\
      -e MYSQL_DATABASE=mini_kb \\
      mysql:8.4
      mysql:
"""
import pymysql

from config import settings


def create_database():
    """创建数据库"""
    print(f"数据库{settings.DB_NAME}")

    # 连接MySQL服务（此时不指定具体业务数据库，仅连接mysql服务层）
    connection = pymysql.connect(
        # 数据库主机地址
        host=settings.DB_HOST,
        # 数据库端口号
        port=settings.DB_PORT,
        # 用户名
        user=settings.DB_USER,
        # 密码
        password=settings.DB_PASSWORD,
    )

    try:
        # 创建游标对象，用于执行sql语句
        with connection.cursor() as cursor:
            # 执行建库SQL：不存在则创建，字符集utf8mb4支持完整emoji，排序规则通用unicode
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            # 打印提示：目标数据库已存在或刚新建完成
            print(f"数据库 '{settings.DB_NAME}' 已创建或已存在")
    finally:
        # 无论是否报错，最终关闭数据库连接，释放资源
        connection.close()

def reset_database():
    """清除所有数据并重新建表"""
    # 打印日志，提示开始清空库内数据
    print("清除所有数据...")

    # 连接指定业务数据库mini_kb
    connection = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        # 指定要操作的业务数据库名
        database=settings.DB_NAME,
    )

    try:
        with connection.cursor() as cursor:
            # 关闭MySQL外键约束检查，否则删表会因为关联关系报错
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        # 查询当前库中所有数据表
        cursor.execute("SHOW TABLES")
        # 取出所有表名列表
        tables = cursor.fetchall()

        # 循环每张表执行删除
        for (table_name,) in tables:
            # 打印当前正在删除的表名
            print(f"  删除表: {table_name}")
            # 删除数据表，不存在也不会报错
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        # 重新开启外键约束
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        # 提交数据库事务，使删表操作永久生效
        connection.commit()
        # 日志提示全部表删除完成
        print("所有数据已清除!")
    finally:
        connection.close()

def create_tables():
    """创建所有表"""
    """创建所有表"""
    print("创建数据表...")

    # 延迟导入：引入全局ORM基类、数据库引擎实例
    from app import Base, engine

    # 一次性导入全部业务模型，把表结构注册到Base.metadata元数据中
    from app.models import (
        Tenant, User, Department,
        KnowledgeBase, Document, Paragraph,
        ChatSession, ChatMessage, TokenUsage
    )

    # 根据元数据中注册的模型，自动生成不存在的数据表，不会覆盖已有表
    Base.metadata.create_all(bind=engine)
    print("数据表创建完成!")

def main():
    # 导入系统模块，用于读取命令行启动参数
    import sys

    # 打印初始化开始日志
    print(f"数据库操作开始...")
    # 打印数据库连接地址
    print(f"数据库地址: {settings.DB_HOST}:{settings.DB_PORT}")
    # 打印目标业务库名称
    print(f"数据库名称: {settings.DB_NAME}")

    try:
        # 第一步：校验并创建业务数据库
        create_database()
        # 判断命令行参数是否携带 --reset 重置标识
        if len(sys.argv) > 1 and sys.argv[1] == "--reset":
            reset_database()

        create_tables()
        print("数据库初始化完成!")
    except Exception as e:
        # 捕获所有异常，打印错误信息
        print(f"数据库操作失败: {e}")
        # 抛出异常，终止程序运行
        raise

if __name__ == '__main__':
    main()