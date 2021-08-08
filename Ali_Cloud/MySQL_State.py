# -*-coding:utf-8-*-

import pymysql

# 打开数据库连接（此处修改用户名和密码）
conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload')

# 使用cursor()方法创建一个游标对象cursor
cursor = conn.cursor()  # 游标对象用于执行查询和获取结果

# 使用execute()方法执行SQL，如果表存在则将其删除
cursor.execute('DROP TABLE IF EXISTS EMPLOYEE')

# 使用预处理语句创建表
sql = """CREATE TABLE `State` (
  `Number_M` INT DEFAULT NULL COMMENT '上传次数',
  `ID_M` INT DEFAULT NULL COMMENT '车辆编号',
  `State_M` INT DEFAULT NULL COMMENT '运行状态',
  `UPWM_M` FLOAT DEFAULT NULL COMMENT '电池电压',
  `L2V_M` FLOAT DEFAULT NULL COMMENT '左轮电机转速',
  `R2V_M` FLOAT DEFAULT NULL COMMENT '右轮电机转速',
  `Angle_M` FLOAT DEFAULT NULL COMMENT '车轮转角',
  `Ay_M` FLOAT DEFAULT NULL COMMENT '横向加速度',
  `Yaw_M` FLOAT DEFAULT NULL COMMENT '横摆角速度',
  `Tn_M` FLOAT DEFAULT NULL COMMENT '转矩',
  `Vy_M` FLOAT DEFAULT NULL COMMENT '横向速度'
   )"""

# 执行SQL语句
cursor.execute(sql)

# 关闭数据库连接
conn.close()