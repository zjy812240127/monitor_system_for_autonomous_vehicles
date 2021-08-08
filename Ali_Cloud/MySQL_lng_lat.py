# -*-coding:utf-8-*-

import pymysql

# 打开数据库连接（此处修改用户名和密码）
conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload')

# 使用cursor()方法创建一个游标对象cursor
cursor = conn.cursor()  # 游标对象用于执行查询和获取结果

# 使用execute()方法执行SQL，如果表存在则将其删除
cursor.execute('DROP TABLE IF EXISTS EMPLOYEE')

# 使用预处理语句创建表
sql = """CREATE TABLE `lng_lat` (
  `ID_M` INT DEFAULT NULL COMMENT '上传次数',
  `Lng_M` DOUBLE DEFAULT NULL COMMENT '经度',
  `Lat_M` DOUBLE DEFAULT NULL COMMENT '纬度'
   )"""

# 执行SQL语句
cursor.execute(sql)

# 关闭数据库连接
conn.close()