# -*-coding:utf-8-*-

import pymysql

# 打开数据库连接
conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'test')

# 使用cursor()方法获取操作游标
cursor = conn.cursor()

# SQL语句：向数据表中插入数据
sql = """INSERT INTO employee(first_name,
         last_name, age, sex, income)
         VALUES ('Mac', 'Mohan', 20, 'M', 2000)""" #修改这一行数据，可多次插入

# 异常处理
try:
    # 执行SQL语句
    cursor.execute(sql)
    # 提交事务到数据库执行
    conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
except:
    # 如果发生错误则执行回滚操作
    conn.rollback()

# 关闭数据库连接
conn.close()
