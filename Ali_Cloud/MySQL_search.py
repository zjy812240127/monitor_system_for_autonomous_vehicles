# -*-coding:utf-8-*-

import pymysql

# 打开数据库连接
conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'test')

# 使用cursor()方法获取操作游标
cursor = conn.cursor()

# SQL语句：查询
sql = "SELECT * FROM employee WHERE income > 100 "

# 异常处理
try:
    # 执行SQL语句
    cursor.execute(sql)
    # 获取所有的记录列表
    results = cursor.fetchall()
    # 遍历列表
    for row in results:
        # 打印列表元素
        print(row)
        # 姓
        first_name = row[0]
        # 名
        last_name = row[1]
        # 年龄
        age = row[2]
        # 性别
        sex = row[3]
        # 收入
        income = row[4]
        # 打印列表元素
        print(first_name, last_name, age, sex, income)
except:
    print('Uable to fetch data!')

# 关闭数据库连接
conn.close()
