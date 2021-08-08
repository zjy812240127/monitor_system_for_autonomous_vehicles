import sys
import json
import socket
import cv2 as cv      #导入opencv
import cv2
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import linecache
from PyQt5.Qt import QThread,pyqtSignal
import struct
from map_load2 import Map_load2
import threading
from pyecharts import options as opts
from pyecharts.charts import Map
from pyecharts.faker import Faker
import wgs84_to_bd09_change
import os
import pymysql

# =================================创建电脑、手机摄像头图像获取子线程
# setDaemon 设置为守护线程，主线程结束该子线程立马随之结束
# join 主线程需要等待子线程结束后才能继续执行
# 通常情况，子线程与主线程的生命周期互不影响

#==========================================监听程序块
# 第一辆车的监听线程
class Listener_ID1(QThread):  # 创建子线程类
    listenFlag = 1
    connectFlag = 1
    sigID = pyqtSignal(str)  # run方法中用来将上位机的数据传送到GUI界面上
    sigState = pyqtSignal(str)
    sigL2v = pyqtSignal(float)
    sigR2v = pyqtSignal(float)
    sigU = pyqtSignal(float)
    sigangle = pyqtSignal(float)
    sigImage = pyqtSignal(str)

    sigAy = pyqtSignal(float)
    sigYaw = pyqtSignal(float)
    sigTn = pyqtSignal(float)
    sigVy = pyqtSignal(float)


    sigLPWM = pyqtSignal(float)
    sigRPWM = pyqtSignal(float)

    siglat = pyqtSignal(float)
    siglng = pyqtSignal(float)



    def __init__(self, ip, port, serverIP, serverPort, length, weight, maxV,
                 minV, maxA, maxD):
        super(Listener_ID1, self).__init__()  # 继承父类的属性和方法

        self.L2vArr = []
        self.R2vArr = []
        self.dataFromCarDecode = ''
        self.serverFlag = 0
        self.flag = 1




    def run(self):
        global sendFlag_ID1  # 因为sendFlag是在方法外定义的变量，所以要在方法内使用的话加上global成为全局变量
        global startFlag
        global askstateFlag_ID1
        global askimageFlag_ID1
        global frame
        global askstate_imageFlag_ID1



        sendFlag_ID1 = 0
        startFlag = 0
        askstateFlag_ID1 = 0
        askimageFlag_ID1 = 0
        askstate_imageFlag_ID1 = 0

        def askimage_method():
            global askimageFlag_ID1
            while True:
                askimageFlag_ID1 = 2
                time.sleep(20)  # 每隔10秒主动请求一次图像数据

        def askstate_method():
            global askstateFlag_ID1
            while True:
                askstateFlag_ID1 = 2
                time.sleep(5)  # 每隔5秒主动请求一次状态数据

            # ===================================接收上传经纬度数据并写入json文件
            # i=0

        def fun_time(lng_ID1, lat_ID1):  # 将上传的经纬度数据写入json文件中供BD_map.html文件读取
            # global i
            with open("weather.json", "w", encoding='utf-8') as f:  # 打开对应车辆的json文件写入数据

                dicts = {"lng": lng_ID1, "lat": lat_ID1}
                f.write(json.dumps(dicts, indent=4))  # Indent表示隔开四个单位
                # i = i + 2
                # if i > 2000:
                #     i = 0

        # ===================================接收上传经纬度数据并写入json文件



        while True:

            while (self.listenFlag):
                print("连接云端服务器")

                tcp_socket_ID1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # STREAM表示TCP传输
                tcp_socket_ID1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用


                # 2.链接服务器
                # server_ip = input("请输入服务器ip地址：")
                # server_port = input("请输入服务器端口:")
                # tcp_socket.connect((str(server_ip), server_port))
                # tcp_socket.connect(("10.80.7.157", 8080))
                tcp_socket_ID1.connect(("47.102.36.187", 8082))   # 链接云端服务器

                # 创建线程锁，防止主线程socket被close了，子线程还在recv而引发的异常
                # socket_lock = threading.Lock()
                def read_thread_method():  # 读取数据的方法
                    print("接收线程开启")

                    while True:
                        if not tcp_socket_ID1:  # 如果socket关闭，退出
                            break
                        dataFromCar = tcp_socket_ID1.recv(1)  # 缓冲区大小，接收文件的个数

                        i = 1  # 下发经纬度数据时的计数,前五个数已经主动下发

                        if not dataFromCar:
                            print("小车停止上传数据")
                        else:
                            while True:
                                print("逐个读取字节",dataFromCar)

                                try:
                                    z1 = struct.unpack('B', dataFromCar)
                                except:
                                    print("第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包头
                                if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                                    dataFromCar = tcp_socket_ID1.recv(3)
                                    break
                                else:
                                    dataFromCar = tcp_socket_ID1.recv(1)
                            # print("dataFromCar的长度", len(dataFromCar))
                            try:
                                x2, x3, x4 = struct.unpack('3B', dataFromCar)  # 包头
                            except:
                                print("包头解析错误")

                            dataFromCar = tcp_socket_ID1.recv(24)
                            try:
                                x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar)
                            except:
                                print("前24个字节解析错误")
                            ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2
                            # print("该段字节流包长", x5)  # 查看包长是否正确

                            # 如果是ID为1的车发送的数据则进行接收
                            # if (x8 == 1):
                            if (x5 == 44):  # 如果上发的是44字节的数据（请求下发经纬度时设下位机发送数据块为空）
                                # 发送数据示例 dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18  00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                print(" 请求下发经纬度数据")
                                dataFromCar_jingwei_to_car = tcp_socket_ID1.recv(16)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                # print("读取余下的字节为：", dataFromCar_jingwei_to_car)
                                baotou1 = 0xff  # char
                                baotou2 = 0xff  # char
                                baotou3 = 0xff  # char
                                baotou4 = 0xff  # char
                                baochang = 128  # int  i包长 字节对齐会在double前面加上四个字节00000000
                                baoxuhao = i  # int  i发送次数
                                shijianchuo = 0  # int  i上位机下发设为0
                                # zhongduanID = 1  # int  i终端ID
                                shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
                                shujuyu_2 = 84  # int  I 5个经纬度数组，一共80字节
                                dianshu = 5  # Uint32 I 下发5个点

                                ## 数据块之前的内容
                                data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,

                                          shujuyu_1, shujuyu_2, dianshu]

                                #####################################--------------------------------------------数据域
                                file_path = "jingweidu.txt"  # 经纬度存储文件名

                                with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                    t_sum = len(f.readlines())  # 总共有的经纬度组数

                                    # print("ccccccc文档的总行数为：", t_sum)
                                    if 5 * i + 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
                                        for j in range(5 * i + 1, 5 * i + 6):
                                            line_number = j  # 文件行数从1开始，而i初始值为0
                                            fread_j = linecache.getline(file_path,
                                                                        line_number).strip()  # 读取对应行数的经纬度
                                            fread_j_num = fread_j.strip("()")  # 删去字符串中左右两边的括号
                                            fread_split = fread_j_num.split(",")
                                            fread_j_jingdu = fread_split[0]  # 每行的经度str
                                            fread_j_weidu = fread_split[1]  # 每行的纬度str
                                            print(type(fread_j_jingdu))
                                            print(fread_j_jingdu)

                                            jingdu = float(fread_j_jingdu)
                                            weidu = float(fread_j_weidu)
                                            data_1.append(jingdu)
                                            data_1.append(weidu)
                                    else:
                                        print("已经发送完毕所有数据")
                                f.close()
                                # 加入数据块后的数据包
                                # print("data_1", data_1)

                                yuliu = 0x00
                                # 循环加入12个0x00表示预留位和CRC32位
                                for n in range(0, 12):
                                    data_1.append(yuliu)

                                baowei = 0xee
                                # 循环加入四个0xee表示包尾
                                for m in range(0, 4):
                                    data_1.append(baowei)
                                    # print(data_1)

                                # 显示完整数据包
                                # print(data_1)

                                ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                                # 为大端接收模式
                                dataTobytes = struct.pack('4B3i3I10d16B', data_1[0], data_1[1], data_1[2], data_1[3],
                                                          data_1[4],
                                                          data_1[5]
                                                          , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10],
                                                          data_1[11]
                                                          , data_1[12], data_1[13], data_1[14], data_1[15],
                                                          data_1[16],
                                                          data_1[17], data_1[18], data_1[19]
                                                          , data_1[20], data_1[21], data_1[22], data_1[23],
                                                          data_1[24],
                                                          data_1[25], data_1[26], data_1[27]
                                                          , data_1[28], data_1[29], data_1[30], data_1[31],
                                                          data_1[32],
                                                          data_1[33], data_1[34], data_1[35]

                                                          )
                                # print(type(dataTobytes), len(dataTobytes))

                                tcp_socket_ID1.send(dataTobytes)
                                # print(i)
                                i += 1

                                # 0xff, 0xff, 0xff, 0xff, 128, 0, 0, 1, 1, 80, 5, 120.04208246406465, 30.231343807768763, \
                                # 120.04207836129298, 30.23134029404531, 120.04207425852078, 30.231336780321374, \
                                # 120.04207015574802, 30.231333266596973, 120.0420660529747, 30.231329752872096, \
                                # 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xee, 0xee, 0xee
                            # ==========================================下传经纬度数据

                            ####-------------------  接收下位机上传数据
                            ##================================更新车辆状态数据以及检测废数据
                            elif (x5 == 68):  # 小车上发车辆状态数据
                                # print("该段字节流包长：", x5)
                                print("这是上发的车辆的状态信息")
                                # 1. 如果数据域前四个字节为0，则上传的为无效的废数据
                                # 2. 如果数据域前四个字节为1，则上传的是车辆的状态信息，分别更新GUI界面上的数据
                                # 3. 如果数据域前四个字节为2，则上传的是GPS的定位信息，提取经纬度数据用于控制算法
                                # 4. 如果数据区前四个字节为3，则上传的是图像信息，更新GUI界面上的图像数据
                                # 上传结构体数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                dataFromCar_state_from_car = tcp_socket_ID1.recv(40)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                if (x9 == 0):  # 数据域前四个字节为0x000x000x000x00,对应情况1
                                    print("这是无效的废数据")
                                else:
                                    try:
                                        x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32 \
                                            = struct.unpack(
                                            'I2fIfI16B',
                                            dataFromCar_state_from_car)  # 4B4i3I2fIfI16B  解包C的结构体数据，大端格式加！（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                    except:
                                        print("解析状态数据出错")

                                    ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                    # print("接收数据转换成字符串为：", x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14,
                                    #       x15, x16,
                                    #       x17,
                                    #       x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32)

                                    ##==============================更新车辆状态数据
                                    # elif (len(dataFromCar) == 68):  # 数据域前四个字节为0x000x000x000x01,对应情况2
                                    self.serverFlag = 1  # 启动多线程服务器？

                                    ID = x8
                                    LPWM = x11  # 车辆状态
                                    RPWM = x15  # 电池电压
                                    L2v = x12  # 左轮电机转速
                                    R2V = x13  # 右轮电机转速
                                    angle = x14

                                    self.sigID.emit(str(ID))  # 往GUI界面中传入数据,注意ID传入的参数为int型要与Listener属性定义处的sigID类型一致

                                    self.sigL2v.emit(float(L2v))

                                    self.sigR2v.emit(float(R2V))

                                    self.sigangle.emit(float(angle))

                                    self.sigLPWM.emit(LPWM)

                                    self.sigRPWM.emit(RPWM)

                                    Ay = 111
                                    Yaw = 111
                                    Tn = 111
                                    Vy = 111

                                    self.sigAy.emit(Ay)
                                    self.sigYaw.emit(Yaw)
                                    self.sigTn.emit(Tn)
                                    self.sigVy.emit(Vy)



                                    # ================写入数据库
                                    conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                           autocommit=True)

                                    # 使用cursor()方法获取操作游标
                                    cursor1 = conn.cursor()

                                    # SQL语句：向数据表中插入数据
                                    # sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                    #                                              VALUES (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)"""  # 修改这一行数据，可多次插入
                                    sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                                                                values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""  # 修改这一行数据，可多次插入,名字要与数据库创立时的一致
                                    data_state = (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)
                                    # 异常处理
                                    try:
                                        # 执行SQL语句
                                        cursor1.execute(sql1, data_state)
                                        # 提交事务到数据库执行
                                        conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                        print("状态数据写入数据库")
                                    except:
                                        # 如果发生错误则执行回滚操作
                                        conn.rollback()

                                    # 关闭数据库连接
                                    conn.close()
                                    ##############写入数据库

                                    # self.stateButton.setCheckable(False)
                                ##==============================更新车辆状态数据
                            ##================================更新车辆状态数据以及检测废数据

                            ##================================获取车辆上传的GPS定位数据
                            elif (x5 == 64):  # 如果上传的数据为64字节，则对应车辆目前GPS获取的经纬度数据
                                Start_LngLat = time.time()  # 开始读取经纬度的时间点

                                print("这是车辆所处的经纬度")
                                # 上传数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                # 数据块：N 的十六进制为4E; P的十六进制为50；L为4C；B为42；卫星个数：01；填充数据： 00 00
                                # 经度：（120.04208246406465）40 5E 02 B1 7A A5 B9 23  纬度：（30.231343807768763）40 3E 3B 39 59 08 7F BB
                                # 120.04862759640338  \x40\x5e\x03\x1c\xb6\xec\x0f\x14  30.237128736109234  \x40\x3e\x3c\xb4\x78\x06\x87\xee
                                # 120.0457642526888  \x40\x5e\x02\xed\xcd\x30\x27\xf4  30.23500645123769  \x40\x3e\x3c\x29\x61\xfe\x6a\x37
                                dataFromCar_jingwei_from_car = tcp_socket_ID1.recv(4)  # 接收GPS等
                                try:
                                    y11, y12, y13, y14 = struct.unpack('4B', dataFromCar_jingwei_from_car)
                                except:
                                    print("解析GPS/卫星数据出错")
                                GPS = y11  # GPS协议类型
                                Star = y12  # 卫星个数
                                print("GPS:", str(GPS))
                                print("卫星个数：", int(Star))

                                dataFromCar_jingwei_from_car = tcp_socket_ID1.recv(32)
                                try:
                                    y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31, y32\
                                        = struct.unpack(
                                        '2d16B',
                                        dataFromCar_jingwei_from_car)  # 4B4i2I4B2d16B 解包C的结构体数据,大端格式加！,h表示两个字节的short型数据（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                except:
                                    print("解析经纬度数据出错")

                                ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                # print("接收数据转换成字符串为：", y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14,
                                #       y15, y16,
                                #       y17,
                                #       y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31,y32)

                                jingdu_Car = y15  # 小车所处经度
                                weidu_Car = y16  # 小车所处纬度
                                lng = y15
                                lat = y16
                                converted = []
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))
                                # print("+++++++++++++++++")


                                #================写入数据库
                                conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                       autocommit=True)

                                # 使用cursor()方法获取操作游标
                                cursor2 = conn.cursor()

                                # SQL语句：向数据表中插入数据
                                # sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)VALUES (x6, y11,y15,y16)"""  # 修改这一行数据，可多次插入
                                # VALUES 里的数据的类型一定要与定义表时的类型一致,该方法适合传入给定数据，如果是变量则要用（"%s",%d）等格式字符
                                sql2 = """INSERT INTO lng_lat(ID_M,Lng_M, Lat_M)values("%s","%s","%s")"""  # 修改这一行数据，可多次插入,名字要与数据库创立时的一致
                                data_lnglat = (x8, y15, y16)

                                # 异常处理
                                try:
                                    # 执行SQL语句
                                    cursor2.execute(sql2, data_lnglat)
                                    # 提交事务到数据库执行
                                    conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                    print("经纬度数据写入数据库")
                                except:
                                    # 如果发生错误则执行回滚操作
                                    conn.rollback()

                                # 关闭数据库连接
                                conn.close()
                                ##############写入数据库


                                converted = wgs84_to_bd09_change.gcj02_to_bd09(y15,
                                                                               y16)  # 调用外部函数将谷歌地图GPS经纬度数据转换成百度地图格式

                                fun_time(converted[0], converted[1])

                                # ti = threading.Thread(target=fun_time, args=(converted[0], converted[1])) ##传入经纬度和车辆ID，将其写入对应的json文件
                                # ti.start()

                                self.siglng.emit(float(converted[0]))
                                self.siglat.emit(float(converted[1]))
                                # time.sleep(1)

                                End_Lnglat = time.time()
                                print("执行一次经纬度数据读取用时",End_Lnglat-Start_LngLat)






                                # def send_jingweidu(jingdu, weidu):
                                #     self.siglng.emit(float(jingdu))
                                #     self.siglat.emit(float(weidu))
                                #     time.sleep(1)
                                #
                                # t_send = threading.Thread(target=send_jingweidu, args=(converted[0], converted[1],))
                                # t_send.start()


                            ##================================获取车辆上传的GPS定位数据

                            elif (x9 == 3 ):  # 如果上传数据字节数过多，则为图像信息

                                print("上传的是图像数据")
                                # def ImageRead():
                                StartImage = time.time()  # 开始读取图片数据

                                data_image = tcp_socket_ID1.recv(1)
                                try:
                                    image_geshi = struct.unpack('B', data_image)
                                except:
                                    print("解析图像格式出错")
                                # print("图像格式为：", image_geshi)
                                data_image = tcp_socket_ID1.recv(4)
                                try:
                                    image_len = struct.unpack('1I', data_image)
                                except:
                                    print("解析图像字节数出错")
                                print("图像字节数：", image_len)

                                image_msg = b''
                                # print("帧中读取的图像数据块字节数，未转化成int型前：",image_len )
                                len1 = int(image_len[0])  # 图像数据的字节长度
                                # print("转化成int型后：", len1)
                                image_length = len1
                                readlength = 0  # 从缓冲区读取的字节数
                                while (len1 > 0):
                                    if len1 > 20000:  # 如果剩余图像字节数大于20000
                                        buffer = tcp_socket_ID1.recv(20000, socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                        # print("本次recv收到的字节是否为20000，", len(buffer))  # 检查每次recv是否收到完整的1024个字节
                                        image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                        len1 = len1 - 20000
                                        readlength += 20000
                                    else:
                                        buffer = tcp_socket_ID1.recv(len1, socket.MSG_WAITALL)
                                        # print("剩余不满20000的字节数为", len1,"读取的字节数为",len(buffer))  # 检查最后一次读取的字节数
                                        image_msg += buffer
                                        readlength += len1
                                        break

                                try:
                                    # 将读取到的字节流存储到图像文件中
                                    start = time.time()
                                    with open("image_file_ID1.jpg", "wb+") as img_file:
                                        img_file.write(image_msg)
                                    end = time.time()
                                    print("写入图片用时", end-start)
                                    imge = "image_file_ID1.jpg"
                                    self.sigImage.emit(imge)


                                except:
                                    print("图像数据出错")


                                # 继续检测包尾
                                left = tcp_socket_ID1.recv(1)
                                while 1:
                                    try:
                                        left_baowei = struct.unpack('B', left)
                                        # print("检测包尾读到的数据为", left_baowei)
                                    except:
                                        print("检测包尾第一个字节解析错误")

                                    # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                                    if (left_baowei == (204,)):  # 如果读到包尾则一次性读完包尾
                                        left = tcp_socket_ID1.recv(3)
                                        print("读完四个包尾")
                                        break
                                    else:
                                        left = tcp_socket_ID1.recv(1)

                                EndImage = time.time()  # 发送完图片时间
                                print("一次图片操作用时", EndImage - StartImage)


                            else:
                                print("上传数据出错")
                        # 如果是ID为1的车发送的数据则进行接收

                while True:
                    # 创建一个线程去读取数据
                    read_thread = threading.Thread(target=read_thread_method)
                    # read_thread.setDaemon(True)  # 守护线程，read_thread作为一个守护线程，主线程结束，其立马也随之结束
                    read_thread.start()
                    # 要在线程执行完毕后在关闭套接字，不然会报错：在一个非套接字上尝试了一个操作
                    # read_thread.join()  # join 设置为主线程等待子线程结束后再继续执行主线程


                    #
                    #     askimage_thread = threading.Thread(target=askimage_method)
                    #     askimage_thread.start()
                    #     print("开启主动请求图像线程")

                    while True:

                        j = 0  # 请求状态数据时的计数
                        h = 0  # 请求图像数据时的计数

                        ###=======================上位机主动下发第一组经纬度数据
                        if (sendFlag_ID1 == 1):
                            print("下发第一组数据")
                            baotou_1 = 0xff  # char
                            baotou_2 = 0xff  # char
                            baotou_3 = 0xff  # char
                            baotou_4 = 0xff  # char
                            baochang_1 = 128  # int  包长  字节对齐会在double前面加上四个字节00000000
                            baoxuhao_1 = 1  # int  发送次数
                            shijianchuo_1 = 0  # int  上位机下发设为0
                            # zhongduanID_1 = 1  # int  终端ID
                            shujuyu_11 = 1  # int  类型1表示下发经纬度
                            shujuyu_21 = 84  # int  5个经纬度数组，一共80字节
                            dianshu_11 = 5  # I 下发5个点

                            ## 数据块之前的内容
                            data_11 = [baotou_1, baotou_2, baotou_3, baotou_4, baochang_1, baoxuhao_1, shijianchuo_1,

                                       shujuyu_11, shujuyu_21, dianshu_11]

                            #####################################--------------------------------------------数据域
                            file_path = "jingweidu.txt"  # 经纬度存储文件名

                            with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                t_sum1 = len(f.readlines())  # 总共有的经纬度组数

                                if 6 < t_sum1:  # 保证文档里经纬度数据大于五个

                                    for n in range(1, 6):
                                        line_number_1 = n  # 文件行数从1开始
                                        fread_n = linecache.getline(file_path, line_number_1).strip()  # 读取对应行数的经纬度
                                        fread_n_num = fread_n.strip("()")  # 删去字符串中左右两边的括号
                                        fread_split = fread_n_num.split(",")
                                        fread_n_jingdu = fread_split[0]  # 每行的经度str
                                        fread_n_weidu = fread_split[1]  # 每行的纬度str

                                        jingdu_1 = float(fread_n_jingdu)
                                        weidu_1 = float(fread_n_weidu)
                                        data_11.append(jingdu_1)
                                        data_11.append(weidu_1)
                                else:
                                    print("已经发送完毕所有数据")
                            f.close()

                            yuliu_1 = 0x00
                            # 循环加入12个0x00表示预留位和CRC32位
                            for s in range(0, 12):
                                data_11.append(yuliu_1)

                            baowei_1 = 0xee
                            # 循环加入四个0xee表示包尾
                            for t in range(0, 4):
                                data_11.append(baowei_1)

                            ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                            # 为小端接收模式
                            dataTobytes_1 = struct.pack('4B6i10d16B', data_11[0], data_11[1], data_11[2], data_11[3],
                                                        data_11[4], data_11[5]
                                                        , data_11[6], data_11[7], data_11[8], data_11[9], data_11[10],
                                                        data_11[11]
                                                        , data_11[12], data_11[13], data_11[14], data_11[15],
                                                        data_11[16],
                                                        data_11[17], data_11[18], data_11[19]
                                                        , data_11[20], data_11[21], data_11[22], data_11[23],
                                                        data_11[24],
                                                        data_11[25], data_11[26], data_11[27]
                                                        , data_11[28], data_11[29], data_11[30], data_11[31],
                                                        data_11[32],
                                                        data_11[33], data_11[34], data_11[35]

                                                        )
                            # print(type(dataTobytes_1), len(dataTobytes_1))

                            tcp_socket_ID1.send(dataTobytes_1)
                            print("发送的经纬度数据为：",dataTobytes_1)
                            sendFlag_ID1 = 0
                            ###=======================上位机主动下发第一组经纬度数据


                        if (askstateFlag_ID1 == 1):  # 如果请求状态按钮被激活则 下发请求状态指令，小车发送任意指令上位机均可以下发请求指令
                            askstate_thread = threading.Thread(target=askstate_method)
                            askstate_thread.start()
                            print("开启主动请求状态线程")
                            print("askstateFlag_ID1:", askstateFlag_ID1)

                        if (askstateFlag_ID1 == 2):
                            print("开始请求车辆状态的数据")

                            send_state_baotou = 0xff  # 包头
                            send_state_baochang = 44  # 包长度，请求时数据域为0字节
                            send_state_xuhao = j  # 包序号
                            send_state_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_state_ID = 1  # int 固定车辆ID号
                            send_state_shujuyu_1 = 2  # int 第二类终端状态请求
                            send_state_shujuyu_2 = 0  # int 请求状态时L为0
                            send_state_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_state_yuliu = 0x00  # 保留帧暂时填充
                            send_state_baowei = 0xee  # 结束帧暂时填充

                            send_state_dataTobytes = []
                            for state_i in range(0, 4):
                                send_state_dataTobytes.append(send_state_baotou)
                            send_state_dataTobytes.append(send_state_baochang)
                            send_state_dataTobytes.append(send_state_xuhao)
                            send_state_dataTobytes.append(send_state_timechuo)
                            # send_state_dataTobytes.append(send_state_ID)
                            send_state_dataTobytes.append(send_state_shujuyu_1)
                            send_state_dataTobytes.append(send_state_shujuyu_2)
                            for state_j in range(0, 8):
                                send_state_dataTobytes.append(send_state_yuliu)

                            for state_k in range(0, 4):
                                send_state_dataTobytes.append(send_state_CRC32)

                            for state_l in range(0, 4):
                                send_state_dataTobytes.append(send_state_baowei)

                            dataTobytes_state = struct.pack('4B3i2I16B', send_state_dataTobytes[0],
                                                            send_state_dataTobytes[1], send_state_dataTobytes[2],
                                                            send_state_dataTobytes[3]
                                                            , send_state_dataTobytes[4], send_state_dataTobytes[5],
                                                            send_state_dataTobytes[6], send_state_dataTobytes[7]
                                                            , send_state_dataTobytes[8], send_state_dataTobytes[9],
                                                            send_state_dataTobytes[10], send_state_dataTobytes[11]
                                                            , send_state_dataTobytes[12], send_state_dataTobytes[13],
                                                            send_state_dataTobytes[14], send_state_dataTobytes[15]
                                                            , send_state_dataTobytes[16], send_state_dataTobytes[17],
                                                            send_state_dataTobytes[18], send_state_dataTobytes[19]
                                                            , send_state_dataTobytes[20], send_state_dataTobytes[21],
                                                            send_state_dataTobytes[22], send_state_dataTobytes[23]
                                                            , send_state_dataTobytes[24])

                            tcp_socket_ID1.send(dataTobytes_state)
                            askstateFlag_ID1 = 0  # 发送完后重新把标志位置零
                            j += 1
                        ####======================上位机向下位机发送请求状态数据的请求

                        ##==========================上位机向下位机请求图像数据
                        if (askimageFlag_ID1 == 1):  # 请求图像按钮被按下时激活，向下发送请求图像指令，小车发送任意数据上位机均可以下发请求指令
                            askimage_thread = threading.Thread(target=askimage_method)
                            askimage_thread.start()
                            print("开启主动请求图像线程")
                            print("askimageFlag_ID1:", askimageFlag_ID1)

                        if (askimageFlag_ID1 == 2):
                            print("开始请求图像的数据")
                            send_image_baotou = 0xff  # 包头
                            send_image_baochang = 44  # 包长度，请求时数据域为0字节
                            send_image_xuhao = h  # 包序号
                            send_image_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_image_ID = 1  # int 固定车辆ID号
                            send_image_shujuyu_1 = 3  # int 第三类终端状态请求
                            send_image_shujuyu_2 = 0  # int 请求图像时L为0
                            send_image_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_image_yuliu = 0x00  # 保留帧暂时填充
                            send_image_baowei = 0xee  # 结束帧暂时填充

                            send_image_dataTobytes = []
                            for image_i in range(0, 4):
                                send_image_dataTobytes.append(send_image_baotou)
                            send_image_dataTobytes.append(send_image_baochang)
                            send_image_dataTobytes.append(send_image_xuhao)
                            send_image_dataTobytes.append(send_image_timechuo)
                            # send_image_dataTobytes.append(send_image_ID)
                            send_image_dataTobytes.append(send_image_shujuyu_1)
                            send_image_dataTobytes.append(send_image_shujuyu_2)
                            for image_j in range(0, 8):
                                send_image_dataTobytes.append(send_image_yuliu)

                            for state_k in range(0, 4):
                                send_image_dataTobytes.append(send_image_CRC32)

                            for state_l in range(0, 4):
                                send_image_dataTobytes.append(send_image_baowei)

                            dataTobytes_image = struct.pack('4B3i2I16B', send_image_dataTobytes[0],
                                                            send_image_dataTobytes[1], send_image_dataTobytes[2],
                                                            send_image_dataTobytes[3]
                                                            , send_image_dataTobytes[4], send_image_dataTobytes[5],
                                                            send_image_dataTobytes[6], send_image_dataTobytes[7]
                                                            , send_image_dataTobytes[8], send_image_dataTobytes[9],
                                                            send_image_dataTobytes[10], send_image_dataTobytes[11]
                                                            , send_image_dataTobytes[12], send_image_dataTobytes[13],
                                                            send_image_dataTobytes[14], send_image_dataTobytes[15]
                                                            , send_image_dataTobytes[16], send_image_dataTobytes[17],
                                                            send_image_dataTobytes[18], send_image_dataTobytes[19]
                                                            , send_image_dataTobytes[20], send_image_dataTobytes[21],
                                                            send_image_dataTobytes[22], send_image_dataTobytes[23]
                                                            , send_image_dataTobytes[24])

                            # client.send(dataTobytes_image)  # 发送请求的信号的数据格式
                            tcp_socket_ID1.send(dataTobytes_image)
                            askimageFlag_ID1 = 0  # 发送后标志位重新置零
                            h += 1
                        ##==========================上位机向下位机请求图像数据

                    # 清理socket，同样道理，这里需要锁定和解锁
                    # socket_lock.acquire()
                    # read_thread.join()
                    tcp_socket_ID1.close()
                    tcp_socket_ID1 = None
                    # socket_lock.release()
                    # break

    def upSend(self, flag):
        pass

# 第二辆车的监听线程
class Listener_ID2(QThread):  # 创建子线程类
    listenFlag = 1
    connectFlag = 1
    sigID_ID2 = pyqtSignal(str)  # run方法中用来将上位机的数据传送到GUI界面上
    sigState_ID2 = pyqtSignal(str)
    sigL2v_ID2 = pyqtSignal(float)
    sigR2v_ID2 = pyqtSignal(float)
    # sigU_ID2 = pyqtSignal(float)
    sigangle_ID2 = pyqtSignal(float)
    sigImage_ID2 = pyqtSignal(str)

    sigAy_ID2 = pyqtSignal(float)
    sigYaw_ID2 = pyqtSignal(float)
    sigTn_ID2 = pyqtSignal(float)
    sigVy_ID2 = pyqtSignal(float)


    sigLPWM_ID2 = pyqtSignal(float)  #车辆状态
    sigRPWM_ID2 = pyqtSignal(float)  #电压

    siglat_ID2 = pyqtSignal(float)
    siglng_ID2 = pyqtSignal(float)



    def __init__(self, ip, port, serverIP, serverPort, length, weight, maxV,
                 minV, maxA, maxD):
        super(Listener_ID2, self).__init__()  # 继承父类的属性和方法

        self.L2vArr = []
        self.R2vArr = []
        self.dataFromCarDecode = ''
        self.serverFlag = 0
        self.flag = 1



    def run(self):
        global sendFlag_ID2  # 因为sendFlag是在方法外定义的变量，所以要在方法内使用的话加上global成为全局变量
        global startFlag
        global askstateFlag_ID2
        global askimageFlag_ID2
        global frame
        global askstate_imageFlag_ID2



        sendFlag_ID2 = 0
        startFlag = 0
        askstateFlag_ID2 = 0
        askimageFlag_ID2 = 0
        askstate_imageFlag_ID2 = 0

        def askimage_method():
            global askimageFlag_ID2
            while True:
                askimageFlag_ID2 = 2
                time.sleep(10)  # 每隔10秒主动请求一次图像数据

        def askstate_method_ID2():
            global askstateFlag_ID2
            while True:
                askstateFlag_ID2 = 2
                time.sleep(5)  # 每隔5秒主动请求一次状态数据

        # ===================================接收上传经纬度数据并写入json文件
        # i=0
        def fun_time_ID2(lng_ID2, lat_ID2):  # 将上传的经纬度数据写入json文件中供BD_map.html文件读取
            # global i
            with open("weather2.json", "w", encoding='utf-8') as f:  # 打开对应车辆的json文件写入数据

                dicts = {"lng": lng_ID2, "lat": lat_ID2}
                f.write(json.dumps(dicts, indent=4))  # Indent表示隔开四个单位
                # i = i + 2
                # if i > 2000:
                #     i = 0

        # ===================================接收上传经纬度数据并写入json文件

        while True:

            while (self.listenFlag):
                print("连接云端服务器")

                tcp_socket_ID2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # STREAM表示TCP传输
                tcp_socket_ID2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

                # 2.链接服务器
                # server_ip = input("请输入服务器ip地址：")
                # server_port = input("请输入服务器端口:")
                # tcp_socket.connect((str(server_ip), server_port))
                # tcp_socket.connect(("10.80.7.157", 8080))
                tcp_socket_ID2.connect(("47.102.36.187", 8084))   # 链接云端服务器

                # 创建线程锁，防止主线程socket被close了，子线程还在recv而引发的异常
                # socket_lock = threading.Lock()
                def read_thread_method():  # 读取数据的方法
                    print("接收线程开启")

                    while True:
                        if not tcp_socket_ID2:  # 如果socket关闭，退出
                            break
                        # Car_ID1 = tcp_socket_ID2.recv(64)
                        # print(test)
                        # return


                        FromCar_ID2 = tcp_socket_ID2.recv(1)  # 缓冲区大小，接收文件的个数
                        print("第一个字节",FromCar_ID2)


                        i = 1  # 下发经纬度数据时的计数,前五个数已经主动下发

                        if not FromCar_ID2:
                            print("小车停止上传数据")
                        else:
                            while 1:
                                print("逐个读取字节")
                                try:
                                    m1_ID2 = struct.unpack('B',FromCar_ID2)
                                except:
                                    print("第一个字节解析错误")
                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包头
                                # if (z1_ID2 == (221,)):  # 如果读到包头则一次性读完包头
                                #     FromCar_ID2 = tcp_socket_ID2.recv(3)
                                #     print("读取后面三个字节")
                                #     break
                                #
                                # else:
                                #     FromCar_ID2 = tcp_socket_ID2.recv(1)
                                #     print("第一个字节是",FromCar_ID2)
                                if (m1_ID2 != (221,)):  # 如果读到包头则一次性读完包头
                                    FromCar_ID2 = tcp_socket_ID2.recv(1)
                                    print("第一个字节是", FromCar_ID2)

                                else:
                                    three = tcp_socket_ID2.recv(3)
                                    print("读取后面三个字节")
                                    break
                            print("dataFromCar的长度++++++++++++++++++")
                            try:
                                s2, s3, s4 = struct.unpack('3B', three)  # 包头
                            except:
                                print("包头解析错误")

                            dataFromCar_ID2 = tcp_socket_ID2.recv(24)
                            try:
                                x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar_ID2)
                            except:
                                print("前24个字节解析错误")
                            ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2
                            # print("该段字节流包长", x5)  # 查看包长是否正确

                            # 如果是ID为1的车发送的数据则进行接收
                            print("判断是否是对应车辆上发的数据")
                            # if (x8 == 2):
                            if (x5 == 44):  # 如果上发的是44字节的数据（请求下发经纬度时设下位机发送数据块为空）
                                # 发送数据示例 dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18  00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                print(" 请求下发经纬度数据")
                                dataFromCar_jingwei_to_car = tcp_socket_ID2.recv(16)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                # print("读取余下的字节为：", dataFromCar_jingwei_to_car)
                                baotou1 = 0xff  # char
                                baotou2 = 0xff  # char
                                baotou3 = 0xff  # char
                                baotou4 = 0xff  # char
                                baochang = 128  # int  i包长 字节对齐会在double前面加上四个字节00000000
                                baoxuhao = i  # int  i发送次数
                                shijianchuo = 0  # int  i上位机下发设为0
                                # zhongduanID = 1  # int  i终端ID
                                shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
                                shujuyu_2 = 84  # int  I 5个经纬度数组，一共80字节
                                dianshu = 5  # Uint32 I 下发5个点

                                ## 数据块之前的内容
                                data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,

                                          shujuyu_1, shujuyu_2, dianshu]

                                #####################################--------------------------------------------数据域
                                file_path = "jingweidu.txt"  # 经纬度存储文件名

                                with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                    t_sum = len(f.readlines())  # 总共有的经纬度组数

                                    # print("ccccccc文档的总行数为：", t_sum)
                                    if 5 * i + 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
                                        for j in range(5 * i + 1, 5 * i + 6):
                                            line_number = j  # 文件行数从1开始，而i初始值为0
                                            fread_j = linecache.getline(file_path,
                                                                        line_number).strip()  # 读取对应行数的经纬度
                                            fread_j_num = fread_j.strip("()")  # 删去字符串中左右两边的括号
                                            fread_split = fread_j_num.split(",")
                                            fread_j_jingdu = fread_split[0]  # 每行的经度str
                                            fread_j_weidu = fread_split[1]  # 每行的纬度str
                                            print(type(fread_j_jingdu))
                                            print(fread_j_jingdu)

                                            jingdu = float(fread_j_jingdu)
                                            weidu = float(fread_j_weidu)
                                            data_1.append(jingdu)
                                            data_1.append(weidu)
                                    else:
                                        print("已经发送完毕所有数据")
                                f.close()
                                # 加入数据块后的数据包
                                # print("data_1", data_1)

                                yuliu = 0x00
                                # 循环加入12个0x00表示预留位和CRC32位
                                for n in range(0, 12):
                                    data_1.append(yuliu)

                                baowei = 0xee
                                # 循环加入四个0xee表示包尾
                                for m in range(0, 4):
                                    data_1.append(baowei)
                                    # print(data_1)

                                # 显示完整数据包
                                # print(data_1)

                                ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                                # 为大端接收模式
                                dataTobytes = struct.pack('4B3i3I10d16B', data_1[0], data_1[1], data_1[2], data_1[3],
                                                          data_1[4],
                                                          data_1[5]
                                                          , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10],
                                                          data_1[11]
                                                          , data_1[12], data_1[13], data_1[14], data_1[15],
                                                          data_1[16],
                                                          data_1[17], data_1[18], data_1[19]
                                                          , data_1[20], data_1[21], data_1[22], data_1[23],
                                                          data_1[24],
                                                          data_1[25], data_1[26], data_1[27]
                                                          , data_1[28], data_1[29], data_1[30], data_1[31],
                                                          data_1[32],
                                                          data_1[33], data_1[34], data_1[35]

                                                          )
                                # print(type(dataTobytes), len(dataTobytes))

                                tcp_socket_ID2.send(dataTobytes)
                                # print(i)
                                i += 1

                                # 0xff, 0xff, 0xff, 0xff, 128, 0, 0, 1, 1, 80, 5, 120.04208246406465, 30.231343807768763, \
                                # 120.04207836129298, 30.23134029404531, 120.04207425852078, 30.231336780321374, \
                                # 120.04207015574802, 30.231333266596973, 120.0420660529747, 30.231329752872096, \
                                # 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xee, 0xee, 0xee
                            # ==========================================下传经纬度数据

                            ####-------------------  接收下位机上传数据
                            ##================================更新车辆状态数据以及检测废数据
                            elif (x5 == 68):  # 小车上发车辆状态数据
                                # print("该段字节流包长：", x5)
                                print("这是上发的车辆的状态信息")
                                # 1. 如果数据域前四个字节为0，则上传的为无效的废数据
                                # 2. 如果数据域前四个字节为1，则上传的是车辆的状态信息，分别更新GUI界面上的数据
                                # 3. 如果数据域前四个字节为2，则上传的是GPS的定位信息，提取经纬度数据用于控制算法
                                # 4. 如果数据区前四个字节为3，则上传的是图像信息，更新GUI界面上的图像数据
                                # 上传结构体数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                dataFromCar_state_from_car_ID2 = tcp_socket_ID2.recv(40)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                print("++++++++++++++")


                                if (x9 == 0):  # 数据域前四个字节为0x000x000x000x00,对应情况1
                                    print("这是无效的废数据")
                                else:
                                    try:
                                        x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32 \
                                            = struct.unpack(
                                            'I2fIfI16B',
                                            dataFromCar_state_from_car_ID2)  # 4B4i3I2fIfI16B  解包C的结构体数据，大端格式加！（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                    except:
                                        print("解析状态数据出错")

                                    ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                    # print("接收数据转换成字符串为：", x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14,
                                    #       x15, x16,
                                    #       x17,
                                    #       x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32)

                                    ##==============================更新车辆状态数据
                                    # elif (len(dataFromCar) == 68):  # 数据域前四个字节为0x000x000x000x01,对应情况2
                                    self.serverFlag = 1  # 启动多线程服务器？

                                    ID = x8
                                    LPWM = x11  # 车辆状态
                                    RPWM = x15  # 电池电压
                                    L2v = x12  # 左轮电机转速
                                    R2V = x13  # 右轮电机转速
                                    angle = x14


                                    self.sigID_ID2.emit(str(ID))  # 往GUI界面中传入数据,注意ID传入的参数为int型要与Listener属性定义处的sigID类型一致
                                    print("向UI界面发送数据")
                                    self.sigL2v_ID2.emit(float(L2v))

                                    self.sigR2v_ID2.emit(float(R2V))

                                    self.sigangle_ID2.emit(float(angle))

                                    self.sigLPWM_ID2.emit(LPWM)

                                    self.sigRPWM_ID2.emit(RPWM)

                                    Ay = 111
                                    Yaw = 111
                                    Tn = 111
                                    Vy = 111

                                    self.sigAy_ID2.emit(Ay)
                                    self.sigYaw_ID2.emit(Yaw)
                                    self.sigTn_ID2.emit(Tn)
                                    self.sigVy_ID2.emit(Vy)



                                    # ================写入数据库
                                    conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                           autocommit=True)

                                    # 使用cursor()方法获取操作游标
                                    cursor1 = conn.cursor()

                                    # SQL语句：向数据表中插入数据
                                    # sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                    #                                              VALUES (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)"""  # 修改这一行数据，可多次插入
                                    sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                                                                values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""  # 修改这一行数据，可多次插入
                                    data_state = (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)
                                    # 异常处理
                                    try:
                                        # 执行SQL语句
                                        cursor1.execute(sql1, data_state)
                                        # 提交事务到数据库执行
                                        conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                        print("状态数据写入数据库")
                                    except:
                                        # 如果发生错误则执行回滚操作
                                        conn.rollback()

                                    # 关闭数据库连接
                                    conn.close()
                                    ##############写入数据库

                                    # self.stateButton.setCheckable(False)
                                ##==============================更新车辆状态数据
                            ##================================更新车辆状态数据以及检测废数据

                            ##================================获取车辆上传的GPS定位数据
                            elif (x5 == 64):  # 如果上传的数据为64字节，则对应车辆目前GPS获取的经纬度数据
                                Start_LngLat = time.time()  # 开始读取经纬度的时间点
                                print("这是车辆所处的经纬度")
                                # 上传数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                # 数据块：N 的十六进制为4E; P的十六进制为50；L为4C；B为42；卫星个数：01；填充数据： 00 00
                                # 经度：（120.04208246406465）40 5E 02 B1 7A A5 B9 23  纬度：（30.231343807768763）40 3E 3B 39 59 08 7F BB
                                # 120.04862759640338  \x40\x5e\x03\x1c\xb6\xec\x0f\x14  30.237128736109234  \x40\x3e\x3c\xb4\x78\x06\x87\xee
                                # 120.0457642526888  \x40\x5e\x02\xed\xcd\x30\x27\xf4  30.23500645123769  \x40\x3e\x3c\x29\x61\xfe\x6a\x37
                                dataFromCar_jingwei_from_car = tcp_socket_ID2.recv(4)  # 接收GPS等
                                try:
                                    y11, y12, y13, y14 = struct.unpack('4B', dataFromCar_jingwei_from_car)
                                except:
                                    print("解析GPS/卫星数据出错")
                                GPS = y11  # GPS协议类型
                                Star = y12  # 卫星个数
                                print("GPS:", str(GPS))
                                print("卫星个数：", int(Star))

                                dataFromCar_jingwei_from_car = tcp_socket_ID2.recv(32)
                                try:
                                    y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31, y32\
                                        = struct.unpack(
                                        '2d16B',
                                        dataFromCar_jingwei_from_car)  # 4B4i2I4B2d16B 解包C的结构体数据,大端格式加！,h表示两个字节的short型数据（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                except:
                                    print("解析经纬度数据出错")

                                ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                # print("接收数据转换成字符串为：", y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14,
                                #       y15, y16,
                                #       y17,
                                #       y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31,y32)

                                jingdu_Car = y15  # 小车所处经度
                                weidu_Car = y16  # 小车所处纬度
                                # lng = y15
                                # lat = y16
                                converted = []
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))
                                # print("+++++++++++++++++")

                                converted = wgs84_to_bd09_change.gcj02_to_bd09(y15,
                                                                               y16)  # 调用外部函数将谷歌地图GPS经纬度数据转换成百度地图格式

                                fun_time_ID2(converted[0], converted[1])

                                # ti = threading.Thread(target=fun_time, args=(converted[0], converted[1])) ##传入经纬度和车辆ID，将其写入对应的json文件
                                # ti.start()

                                self.siglng_ID2.emit(float(converted[0]))
                                self.siglat_ID2.emit(float(converted[1]))
                                # time.sleep(1)

                                End_Lnglat = time.time()
                                print("执行一次经纬度数据读取用时", End_Lnglat - Start_LngLat)



                            ##================================获取车辆上传的GPS定位数据

                            elif (x9 == 3 ):  # 如果上传数据字节数过多，则为图像信息

                                print("上传的是图像数据")
                                # def ImageRead():
                                StartImage = time.time()  # 开始读取图片数据

                                data_image = tcp_socket_ID2.recv(1)
                                try:
                                    image_geshi = struct.unpack('B', data_image)
                                except:
                                    print("解析图像格式出错")
                                # print("图像格式为：", image_geshi)
                                data_image = tcp_socket_ID2.recv(4)
                                try:
                                    image_len = struct.unpack('1I', data_image)
                                except:
                                    print("解析图像字节数出错")
                                print("图像字节数：", image_len)

                                image_msg = b''
                                # print("帧中读取的图像数据块字节数，未转化成int型前：", image_len)
                                len1 = int(image_len[0])  # 图像数据的字节长度
                                # print("转化成int型后：", len1)
                                image_length = len1
                                readlength = 0  # 从缓冲区读取的字节数
                                while (len1 > 0):
                                    if len1 > 20000:  # 如果剩余图像字节数大于20000
                                        buffer = tcp_socket_ID2.recv(20000,
                                                                     socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                        # print("本次recv收到的字节是否为20000，", len(buffer))  # 检查每次recv是否收到完整的1024个字节
                                        image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                        len1 = len1 - 20000
                                        readlength += 20000
                                    else:
                                        buffer = tcp_socket_ID2.recv(len1, socket.MSG_WAITALL)
                                        # print("剩余不满20000的字节数为", len1, "读取的字节数为", len(buffer))  # 检查最后一次读取的字节数
                                        image_msg += buffer
                                        readlength += len1
                                        break

                                try:
                                    # 将读取到的字节流存储到图像文件中
                                    start = time.time()
                                    with open("image_file_ID2.jpg", "wb+") as img_file:
                                        img_file.write(image_msg)
                                    end = time.time()
                                    print("写入图片用时", end - start)
                                    imge = "image_file_ID2.jpg"
                                    self.sigImage.emit(imge)


                                except:
                                    print("图像数据出错")

                                # 继续检测包尾
                                left = tcp_socket_ID2.recv(1)
                                while 1:
                                    try:
                                        left_baowei = struct.unpack('B', left)
                                        # print("检测包尾读到的数据为", left_baowei)
                                    except:
                                        print("检测包尾第一个字节解析错误")

                                    # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                                    if (left_baowei == (204,)):  # 如果读到包尾则一次性读完包尾
                                        left = tcp_socket_ID2.recv(3)
                                        print("读完四个包尾")
                                        break
                                    else:
                                        left = tcp_socket_ID2.recv(1)

                                EndImage = time.time()  # 发送完图片时间
                                print("一次图片操作用时", EndImage - StartImage)

                            else:
                                        print("上传数据出错")
                                # 如果是ID为1的车发送的数据则进行接收


                while True:
                    # 创建一个线程去读取数据
                    read_thread = threading.Thread(target=read_thread_method)
                    # read_thread.setDaemon(True)  # 守护线程，read_thread作为一个守护线程，主线程结束，其立马也随之结束
                    read_thread.start()
                    # 要在线程执行完毕后在关闭套接字，不然会报错：在一个非套接字上尝试了一个操作
                    # read_thread.join()  # join 设置为主线程等待子线程结束后再继续执行主线程


                    #
                    #     askimage_thread = threading.Thread(target=askimage_method)
                    #     askimage_thread.start()
                    #     print("开启主动请求图像线程")

                    while True:

                        j = 0  # 请求状态数据时的计数
                        h = 0  # 请求图像数据时的计数

                        ###=======================上位机主动下发第一组经纬度数据
                        if (sendFlag_ID2 == 1):
                            print("下发第一组数据")
                            baotou_1 = 0xff  # char
                            baotou_2 = 0xff  # char
                            baotou_3 = 0xff  # char
                            baotou_4 = 0xff  # char
                            baochang_1 = 128  # int  包长  字节对齐会在double前面加上四个字节00000000
                            baoxuhao_1 = 1  # int  发送次数
                            shijianchuo_1 = 0  # int  上位机下发设为0
                            # zhongduanID_1 = 1  # int  终端ID
                            shujuyu_11 = 1  # int  类型1表示下发经纬度
                            shujuyu_21 = 84  # int  5个经纬度数组，一共80字节
                            dianshu_11 = 5  # I 下发5个点

                            ## 数据块之前的内容
                            data_11 = [baotou_1, baotou_2, baotou_3, baotou_4, baochang_1, baoxuhao_1, shijianchuo_1,

                                       shujuyu_11, shujuyu_21, dianshu_11]

                            #####################################--------------------------------------------数据域
                            file_path = "jingweidu.txt"  # 经纬度存储文件名

                            with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                t_sum1 = len(f.readlines())  # 总共有的经纬度组数

                                if 6 < t_sum1:  # 保证文档里经纬度数据大于五个

                                    for n in range(1, 6):
                                        line_number_1 = n  # 文件行数从1开始
                                        fread_n = linecache.getline(file_path, line_number_1).strip()  # 读取对应行数的经纬度
                                        fread_n_num = fread_n.strip("()")  # 删去字符串中左右两边的括号
                                        fread_split = fread_n_num.split(",")
                                        fread_n_jingdu = fread_split[0]  # 每行的经度str
                                        fread_n_weidu = fread_split[1]  # 每行的纬度str

                                        jingdu_1 = float(fread_n_jingdu)
                                        weidu_1 = float(fread_n_weidu)
                                        data_11.append(jingdu_1)
                                        data_11.append(weidu_1)
                                else:
                                    print("已经发送完毕所有数据")
                            f.close()

                            yuliu_1 = 0x00
                            # 循环加入12个0x00表示预留位和CRC32位
                            for s in range(0, 12):
                                data_11.append(yuliu_1)

                            baowei_1 = 0xee
                            # 循环加入四个0xee表示包尾
                            for t in range(0, 4):
                                data_11.append(baowei_1)

                            ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                            # 为小端接收模式
                            dataTobytes_1 = struct.pack('4B6i10d16B', data_11[0], data_11[1], data_11[2], data_11[3],
                                                        data_11[4], data_11[5]
                                                        , data_11[6], data_11[7], data_11[8], data_11[9], data_11[10],
                                                        data_11[11]
                                                        , data_11[12], data_11[13], data_11[14], data_11[15],
                                                        data_11[16],
                                                        data_11[17], data_11[18], data_11[19]
                                                        , data_11[20], data_11[21], data_11[22], data_11[23],
                                                        data_11[24],
                                                        data_11[25], data_11[26], data_11[27]
                                                        , data_11[28], data_11[29], data_11[30], data_11[31],
                                                        data_11[32],
                                                        data_11[33], data_11[34], data_11[35]

                                                        )
                            # print(type(dataTobytes_1), len(dataTobytes_1))

                            tcp_socket_ID2.send(dataTobytes_1)
                            sendFlag_ID2 = 0
                            ###=======================上位机主动下发第一组经纬度数据


                        if (askstateFlag_ID2 == 1):  # 如果请求状态按钮被激活则 下发请求状态指令，小车发送任意指令上位机均可以下发请求指令
                            askstate_thread_ID2 = threading.Thread(target=askstate_method_ID2)
                            askstate_thread_ID2.start()
                            print("开启主动请求状态线程")
                            print("askstateFlag_ID2:", askstateFlag_ID2)

                        if (askstateFlag_ID2 == 2):
                            print("开始请求车辆状态的数据")

                            send_state_baotou = 0xff  # 包头
                            send_state_baochang = 44  # 包长度，请求时数据域为0字节
                            send_state_xuhao = j  # 包序号
                            send_state_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_state_ID = 1  # int 固定车辆ID号
                            send_state_shujuyu_1 = 2  # int 第二类终端状态请求
                            send_state_shujuyu_2 = 0  # int 请求状态时L为0
                            send_state_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_state_yuliu = 0x00  # 保留帧暂时填充
                            send_state_baowei = 0xee  # 结束帧暂时填充

                            send_state_dataTobytes = []
                            for state_i in range(0, 4):
                                send_state_dataTobytes.append(send_state_baotou)
                            send_state_dataTobytes.append(send_state_baochang)
                            send_state_dataTobytes.append(send_state_xuhao)
                            send_state_dataTobytes.append(send_state_timechuo)
                            # send_state_dataTobytes.append(send_state_ID)
                            send_state_dataTobytes.append(send_state_shujuyu_1)
                            send_state_dataTobytes.append(send_state_shujuyu_2)
                            for state_j in range(0, 8):
                                send_state_dataTobytes.append(send_state_yuliu)

                            for state_k in range(0, 4):
                                send_state_dataTobytes.append(send_state_CRC32)

                            for state_l in range(0, 4):
                                send_state_dataTobytes.append(send_state_baowei)

                            dataTobytes_state = struct.pack('4B3i2I16B', send_state_dataTobytes[0],
                                                            send_state_dataTobytes[1], send_state_dataTobytes[2],
                                                            send_state_dataTobytes[3]
                                                            , send_state_dataTobytes[4], send_state_dataTobytes[5],
                                                            send_state_dataTobytes[6], send_state_dataTobytes[7]
                                                            , send_state_dataTobytes[8], send_state_dataTobytes[9],
                                                            send_state_dataTobytes[10], send_state_dataTobytes[11]
                                                            , send_state_dataTobytes[12], send_state_dataTobytes[13],
                                                            send_state_dataTobytes[14], send_state_dataTobytes[15]
                                                            , send_state_dataTobytes[16], send_state_dataTobytes[17],
                                                            send_state_dataTobytes[18], send_state_dataTobytes[19]
                                                            , send_state_dataTobytes[20], send_state_dataTobytes[21],
                                                            send_state_dataTobytes[22], send_state_dataTobytes[23]
                                                            , send_state_dataTobytes[24])

                            tcp_socket_ID2.send(dataTobytes_state)
                            askstateFlag_ID2 = 0  # 发送完后重新把标志位置零
                            j += 1
                        ####======================上位机向下位机发送请求状态数据的请求

                        ##==========================上位机向下位机请求图像数据
                        if (askimageFlag_ID2 == 1):  # 请求图像按钮被按下时激活，向下发送请求图像指令，小车发送任意数据上位机均可以下发请求指令
                            askimage_thread = threading.Thread(target=askimage_method)
                            askimage_thread.start()
                            print("开启主动请求图像线程")
                            print("askimageFlag_ID2:", askimageFlag_ID2)

                        if (askimageFlag_ID2 == 2):
                            print("开始请求图像的数据")
                            send_image_baotou = 0xff  # 包头
                            send_image_baochang = 44  # 包长度，请求时数据域为0字节
                            send_image_xuhao = h  # 包序号
                            send_image_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_image_ID = 1  # int 固定车辆ID号
                            send_image_shujuyu_1 = 3  # int 第三类终端状态请求
                            send_image_shujuyu_2 = 0  # int 请求图像时L为0
                            send_image_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_image_yuliu = 0x00  # 保留帧暂时填充
                            send_image_baowei = 0xee  # 结束帧暂时填充

                            send_image_dataTobytes = []
                            for image_i in range(0, 4):
                                send_image_dataTobytes.append(send_image_baotou)
                            send_image_dataTobytes.append(send_image_baochang)
                            send_image_dataTobytes.append(send_image_xuhao)
                            send_image_dataTobytes.append(send_image_timechuo)
                            # send_image_dataTobytes.append(send_image_ID)
                            send_image_dataTobytes.append(send_image_shujuyu_1)
                            send_image_dataTobytes.append(send_image_shujuyu_2)
                            for image_j in range(0, 8):
                                send_image_dataTobytes.append(send_image_yuliu)

                            for state_k in range(0, 4):
                                send_image_dataTobytes.append(send_image_CRC32)

                            for state_l in range(0, 4):
                                send_image_dataTobytes.append(send_image_baowei)

                            dataTobytes_image = struct.pack('4B3i2I16B', send_image_dataTobytes[0],
                                                            send_image_dataTobytes[1], send_image_dataTobytes[2],
                                                            send_image_dataTobytes[3]
                                                            , send_image_dataTobytes[4], send_image_dataTobytes[5],
                                                            send_image_dataTobytes[6], send_image_dataTobytes[7]
                                                            , send_image_dataTobytes[8], send_image_dataTobytes[9],
                                                            send_image_dataTobytes[10], send_image_dataTobytes[11]
                                                            , send_image_dataTobytes[12], send_image_dataTobytes[13],
                                                            send_image_dataTobytes[14], send_image_dataTobytes[15]
                                                            , send_image_dataTobytes[16], send_image_dataTobytes[17],
                                                            send_image_dataTobytes[18], send_image_dataTobytes[19]
                                                            , send_image_dataTobytes[20], send_image_dataTobytes[21],
                                                            send_image_dataTobytes[22], send_image_dataTobytes[23]
                                                            , send_image_dataTobytes[24])

                            # client.send(dataTobytes_image)  # 发送请求的信号的数据格式
                            tcp_socket_ID2.send(dataTobytes_image)
                            askimageFlag_ID2 = 0  # 发送后标志位重新置零
                            h += 1
                        ##==========================上位机向下位机请求图像数据

                    # 清理socket，同样道理，这里需要锁定和解锁
                    # socket_lock.acquire()
                    # read_thread.join()
                    tcp_socket_ID2.close()
                    tcp_socket_ID2 = None
                    # socket_lock.release()
                    # break

    def upSend(self, flag):
        pass

# 第三辆车的监听线程
class Listener_ID3(QThread):  # 创建子线程类
    listenFlag = 1
    connectFlag = 1
    sigID_ID3 = pyqtSignal(str)  # run方法中用来将上位机的数据传送到GUI界面上
    sigState_ID3 = pyqtSignal(str)
    sigL2v_ID3 = pyqtSignal(float)
    sigR2v_ID3 = pyqtSignal(float)
    sigU_ID3 = pyqtSignal(float)
    sigangle_ID3 = pyqtSignal(float)
    sigImage_ID3 = pyqtSignal(str)

    sigAy_ID3 = pyqtSignal(float)
    sigYaw_ID3 = pyqtSignal(float)
    sigTn_ID3 = pyqtSignal(float)
    sigVy_ID3 = pyqtSignal(float)


    sigLPWM_ID3 = pyqtSignal(float)
    sigRPWM_ID3 = pyqtSignal(float)

    siglat_ID3 = pyqtSignal(float)
    siglng_ID3 = pyqtSignal(float)



    def __init__(self, ip, port, serverIP, serverPort, length, weight, maxV,
                 minV, maxA, maxD):
        super(Listener_ID3, self).__init__()  # 继承父类的属性和方法

        self.L2vArr = []
        self.R2vArr = []
        self.dataFromCarDecode = ''
        self.serverFlag = 0
        self.flag = 1



    def run(self):
        global sendFlag_ID3  # 因为sendFlag是在方法外定义的变量，所以要在方法内使用的话加上global成为全局变量
        global startFlag
        global askstateFlag_ID3
        global askimageFlag_ID3
        global frame
        global askstate_imageFlag_ID3



        sendFlag_ID3 = 0
        startFlag = 0
        askstateFlag_ID3 = 0
        askimageFlag_ID3 = 0
        askstate_imageFlag_ID3 = 0

        def askimage_method_ID3():
            global askimageFlag_ID3
            while True:
                askimageFlag_ID3 = 2
                time.sleep(10)  # 每隔10秒主动请求一次图像数据

        def askstate_method_ID3():
            global askstateFlag_ID3
            while True:
                askstateFlag_ID3 = 2
                time.sleep(5)  # 每隔5秒主动请求一次状态数据

        # ===================================接收上传经纬度数据并写入json文件
        # i=0
        def fun_time_ID3(lng_ID1, lat_ID2):  # 将上传的经纬度数据写入json文件中供BD_map.html文件读取
            # global i
            with open("weather3.json", "w", encoding='utf-8') as f:  # 打开对应车辆的json文件写入数据

                dicts = {"lng": lng_ID1, "lat": lat_ID2}
                f.write(json.dumps(dicts, indent=4))  # Indent表示隔开四个单位
                # i = i + 2
                # if i > 2000:
                #     i = 0

        # ===================================接收上传经纬度数据并写入json文件

        while True:

            while (self.listenFlag):
                print("连接云端服务器")

                tcp_socket_ID3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # STREAM表示TCP传输
                tcp_socket_ID3.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

                # 2.链接服务器
                # server_ip = input("请输入服务器ip地址：")
                # server_port = input("请输入服务器端口:")
                # tcp_socket.connect((str(server_ip), server_port))
                # tcp_socket.connect(("10.80.7.157", 8080))
                tcp_socket_ID3.connect(("47.102.36.187", 8086))   # 链接云端服务器

                # 创建线程锁，防止主线程socket被close了，子线程还在recv而引发的异常
                # socket_lock = threading.Lock()
                def read_thread_method():  # 读取数据的方法
                    print("接收线程开启")

                    while True:
                        if not tcp_socket_ID3:  # 如果socket关闭，退出
                            break
                        dataFromCar = tcp_socket_ID3.recv(1)  # 缓冲区大小，接收文件的个数

                        i = 1  # 下发经纬度数据时的计数,前五个数已经主动下发

                        if not dataFromCar:
                            print("小车停止上传数据")
                        else:
                            while True:
                                print("逐个读取字节")
                                try:
                                    z1 = struct.unpack('B', dataFromCar)
                                except:
                                    print("第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包头
                                if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                                    dataFromCar = tcp_socket_ID3.recv(3)
                                    break
                                else:
                                    dataFromCar = tcp_socket_ID3.recv(1)
                            # print("dataFromCar的长度", len(dataFromCar))
                            try:
                                x2, x3, x4 = struct.unpack('3B', dataFromCar)  # 包头
                            except:
                                print("包头解析错误")

                            dataFromCar = tcp_socket_ID3.recv(24)
                            try:
                                x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar)
                            except:
                                print("前24个字节解析错误")
                            ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2
                            # print("该段字节流包长", x5)  # 查看包长是否正确

                            # 如果是ID为1的车发送的数据则进行接收
                            # if (x8 == 3):
                            if (x5 == 44):  # 如果上发的是44字节的数据（请求下发经纬度时设下位机发送数据块为空）
                                # 发送数据示例 dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18  00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                print(" 请求下发经纬度数据")
                                dataFromCar_jingwei_to_car = tcp_socket_ID3.recv(16)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                # print("读取余下的字节为：", dataFromCar_jingwei_to_car)
                                baotou1 = 0xff  # char
                                baotou2 = 0xff  # char
                                baotou3 = 0xff  # char
                                baotou4 = 0xff  # char
                                baochang = 128  # int  i包长 字节对齐会在double前面加上四个字节00000000
                                baoxuhao = i  # int  i发送次数
                                shijianchuo = 0  # int  i上位机下发设为0
                                # zhongduanID = 1  # int  i终端ID
                                shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
                                shujuyu_2 = 84  # int  I 5个经纬度数组，一共80字节
                                dianshu = 5  # Uint32 I 下发5个点

                                ## 数据块之前的内容
                                data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,

                                          shujuyu_1, shujuyu_2, dianshu]

                                #####################################--------------------------------------------数据域
                                file_path = "jingweidu.txt"  # 经纬度存储文件名

                                with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                    t_sum = len(f.readlines())  # 总共有的经纬度组数

                                    # print("ccccccc文档的总行数为：", t_sum)
                                    if 5 * i + 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
                                        for j in range(5 * i + 1, 5 * i + 6):
                                            line_number = j  # 文件行数从1开始，而i初始值为0
                                            fread_j = linecache.getline(file_path,
                                                                        line_number).strip()  # 读取对应行数的经纬度
                                            fread_j_num = fread_j.strip("()")  # 删去字符串中左右两边的括号
                                            fread_split = fread_j_num.split(",")
                                            fread_j_jingdu = fread_split[0]  # 每行的经度str
                                            fread_j_weidu = fread_split[1]  # 每行的纬度str
                                            print(type(fread_j_jingdu))
                                            print(fread_j_jingdu)

                                            jingdu = float(fread_j_jingdu)
                                            weidu = float(fread_j_weidu)
                                            data_1.append(jingdu)
                                            data_1.append(weidu)
                                    else:
                                        print("已经发送完毕所有数据")
                                f.close()
                                # 加入数据块后的数据包
                                # print("data_1", data_1)

                                yuliu = 0x00
                                # 循环加入12个0x00表示预留位和CRC32位
                                for n in range(0, 12):
                                    data_1.append(yuliu)

                                baowei = 0xee
                                # 循环加入四个0xee表示包尾
                                for m in range(0, 4):
                                    data_1.append(baowei)
                                    # print(data_1)

                                # 显示完整数据包
                                # print(data_1)

                                ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                                # 为大端接收模式
                                dataTobytes = struct.pack('4B3i3I10d16B', data_1[0], data_1[1], data_1[2], data_1[3],
                                                          data_1[4],
                                                          data_1[5]
                                                          , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10],
                                                          data_1[11]
                                                          , data_1[12], data_1[13], data_1[14], data_1[15],
                                                          data_1[16],
                                                          data_1[17], data_1[18], data_1[19]
                                                          , data_1[20], data_1[21], data_1[22], data_1[23],
                                                          data_1[24],
                                                          data_1[25], data_1[26], data_1[27]
                                                          , data_1[28], data_1[29], data_1[30], data_1[31],
                                                          data_1[32],
                                                          data_1[33], data_1[34], data_1[35]

                                                          )
                                # print(type(dataTobytes), len(dataTobytes))

                                tcp_socket_ID3.send(dataTobytes)
                                # print(i)
                                i += 1

                                # 0xff, 0xff, 0xff, 0xff, 128, 0, 0, 1, 1, 80, 5, 120.04208246406465, 30.231343807768763, \
                                # 120.04207836129298, 30.23134029404531, 120.04207425852078, 30.231336780321374, \
                                # 120.04207015574802, 30.231333266596973, 120.0420660529747, 30.231329752872096, \
                                # 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xee, 0xee, 0xee
                            # ==========================================下传经纬度数据

                            ####-------------------  接收下位机上传数据
                            ##================================更新车辆状态数据以及检测废数据
                            elif (x5 == 68):  # 小车上发车辆状态数据
                                # print("该段字节流包长：", x5)
                                print("这是上发的车辆的状态信息")
                                # 1. 如果数据域前四个字节为0，则上传的为无效的废数据
                                # 2. 如果数据域前四个字节为1，则上传的是车辆的状态信息，分别更新GUI界面上的数据
                                # 3. 如果数据域前四个字节为2，则上传的是GPS的定位信息，提取经纬度数据用于控制算法
                                # 4. 如果数据区前四个字节为3，则上传的是图像信息，更新GUI界面上的图像数据
                                # 上传结构体数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                dataFromCar_state_from_car = tcp_socket_ID3.recv(40)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                if (x9 == 0):  # 数据域前四个字节为0x000x000x000x00,对应情况1
                                    print("这是无效的废数据")
                                else:
                                    try:
                                        x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32 \
                                            = struct.unpack(
                                            'I2fIfI16B',
                                            dataFromCar_state_from_car)  # 4B4i3I2fIfI16B  解包C的结构体数据，大端格式加！（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                    except:
                                        print("解析状态数据出错")

                                    ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                    # print("接收数据转换成字符串为：", x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14,
                                    #       x15, x16,
                                    #       x17,
                                    #       x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32)

                                    ##==============================更新车辆状态数据
                                    # elif (len(dataFromCar) == 68):  # 数据域前四个字节为0x000x000x000x01,对应情况2
                                    self.serverFlag = 1  # 启动多线程服务器？

                                    ID = x8
                                    LPWM = x11  # 车辆状态
                                    RPWM = x15  # 电池电压
                                    L2v = x12  # 左轮电机转速
                                    R2V = x13  # 右轮电机转速
                                    angle = x14

                                    self.sigID_ID3.emit(str(ID))  # 往GUI界面中传入数据,注意ID传入的参数为int型要与Listener属性定义处的sigID类型一致

                                    self.sigL2v_ID3.emit(float(L2v))

                                    self.sigR2v_ID3.emit(float(R2V))

                                    self.sigangle_ID3.emit(float(angle))

                                    self.sigLPWM_ID3.emit(LPWM)

                                    self.sigRPWM_ID3.emit(RPWM)

                                    Ay = 111
                                    Yaw = 111
                                    Tn = 111
                                    Vy = 111

                                    self.sigAy_ID3.emit(Ay)
                                    self.sigYaw_ID3.emit(Yaw)
                                    self.sigTn_ID3.emit(Tn)
                                    self.sigVy_ID3.emit(Vy)



                                    # ================写入数据库
                                    conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                           autocommit=True)

                                    # 使用cursor()方法获取操作游标
                                    cursor1 = conn.cursor()

                                    # SQL语句：向数据表中插入数据
                                    # sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                    #                                              VALUES (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)"""  # 修改这一行数据，可多次插入
                                    sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                                                                values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""  # 修改这一行数据，可多次插入
                                    data_state = (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)
                                    # 异常处理
                                    try:
                                        # 执行SQL语句
                                        cursor1.execute(sql1, data_state)
                                        # 提交事务到数据库执行
                                        conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                        print("状态数据写入数据库")
                                    except:
                                        # 如果发生错误则执行回滚操作
                                        conn.rollback()

                                    # 关闭数据库连接
                                    conn.close()
                                    ##############写入数据库

                                    # self.stateButton.setCheckable(False)
                                ##==============================更新车辆状态数据
                            ##================================更新车辆状态数据以及检测废数据

                            ##================================获取车辆上传的GPS定位数据
                            elif (x5 == 64):  # 如果上传的数据为64字节，则对应车辆目前GPS获取的经纬度数据
                                Start_LngLat = time.time()  # 开始读取经纬度的时间点
                                print("这是车辆所处的经纬度")
                                # 上传数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                # 数据块：N 的十六进制为4E; P的十六进制为50；L为4C；B为42；卫星个数：01；填充数据： 00 00
                                # 经度：（120.04208246406465）40 5E 02 B1 7A A5 B9 23  纬度：（30.231343807768763）40 3E 3B 39 59 08 7F BB
                                # 120.04862759640338  \x40\x5e\x03\x1c\xb6\xec\x0f\x14  30.237128736109234  \x40\x3e\x3c\xb4\x78\x06\x87\xee
                                # 120.0457642526888  \x40\x5e\x02\xed\xcd\x30\x27\xf4  30.23500645123769  \x40\x3e\x3c\x29\x61\xfe\x6a\x37
                                dataFromCar_jingwei_from_car = tcp_socket_ID3.recv(4)  # 接收GPS等
                                try:
                                    y11, y12, y13, y14 = struct.unpack('4B', dataFromCar_jingwei_from_car)
                                except:
                                    print("解析GPS/卫星数据出错")
                                GPS = y11  # GPS协议类型
                                Star = y12  # 卫星个数
                                print("GPS:", str(GPS))
                                print("卫星个数：", int(Star))

                                dataFromCar_jingwei_from_car = tcp_socket_ID3.recv(32)
                                try:
                                    y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31, y32\
                                        = struct.unpack(
                                        '2d16B',
                                        dataFromCar_jingwei_from_car)  # 4B4i2I4B2d16B 解包C的结构体数据,大端格式加！,h表示两个字节的short型数据（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                except:
                                    print("解析经纬度数据出错")

                                ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                # print("接收数据转换成字符串为：", y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14,
                                #       y15, y16,
                                #       y17,
                                #       y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31,y32)

                                jingdu_Car = y15  # 小车所处经度
                                weidu_Car = y16  # 小车所处纬度
                                lng = y15
                                lat = y16
                                converted = []
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))


                                #================写入数据库
                                conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                       autocommit=True)

                                # 使用cursor()方法获取操作游标
                                cursor2 = conn.cursor()

                                # SQL语句：向数据表中插入数据
                                # sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)VALUES (x6, y11,y15,y16)"""  # 修改这一行数据，可多次插入
                                # VALUES 里的数据的类型一定要与定义表时的类型一致,该方法适合传入给定数据，如果是变量则要用（"%s",%d）等格式字符
                                sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)values("%s","%s","%s","%s")"""  # 修改这一行数据，可多次插入
                                data_lnglat = (x8, y11, y15, y16)

                                # 异常处理
                                try:
                                    # 执行SQL语句
                                    cursor2.execute(sql2, data_lnglat)
                                    # 提交事务到数据库执行
                                    conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                    print("经纬度数据写入数据库")
                                except:
                                    # 如果发生错误则执行回滚操作
                                    conn.rollback()

                                # 关闭数据库连接
                                conn.close()
                                ##############写入数据库


                                converted = wgs84_to_bd09_change.gcj02_to_bd09(y15,
                                                                               y16)  # 调用外部函数将谷歌地图GPS经纬度数据转换成百度地图格式

                                fun_time_ID3(converted[0], converted[1])

                                # ti = threading.Thread(target=fun_time, args=(converted[0], converted[1])) ##传入经纬度和车辆ID，将其写入对应的json文件
                                # ti.start()

                                self.siglng_ID3.emit(float(converted[0]))
                                self.siglat_ID3.emit(float(converted[1]))
                                # time.sleep(1)

                                End_Lnglat = time.time()
                                print("执行一次经纬度数据读取用时", End_Lnglat - Start_LngLat)
                                # print("GPS:", str(GPS))
                                # print("卫星个数：", int(Star))
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))
                            ##================================获取车辆上传的GPS定位数据

                            elif (x9 == 3 ):  # 如果上传数据字节数过多，则为图像信息

                                print("上传的是图像数据")
                                # def ImageRead():
                                StartImage = time.time()  # 开始读取图片数据

                                data_image = tcp_socket_ID3.recv(1)
                                try:
                                    image_geshi = struct.unpack('B', data_image)
                                except:
                                    print("解析图像格式出错")
                                # print("图像格式为：", image_geshi)
                                data_image = tcp_socket_ID3.recv(4)
                                try:
                                    image_len = struct.unpack('1I', data_image)
                                except:
                                    print("解析图像字节数出错")
                                print("图像字节数：", image_len)

                                image_msg = b''
                                # print("帧中读取的图像数据块字节数，未转化成int型前：", image_len)
                                len1 = int(image_len[0])  # 图像数据的字节长度
                                # print("转化成int型后：", len1)
                                image_length = len1
                                readlength = 0  # 从缓冲区读取的字节数
                                while (len1 > 0):
                                    if len1 > 20000:  # 如果剩余图像字节数大于20000
                                        buffer = tcp_socket_ID3.recv(20000,
                                                                     socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                        # print("本次recv收到的字节是否为20000，", len(buffer))  # 检查每次recv是否收到完整的1024个字节
                                        image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                        len1 = len1 - 20000
                                        readlength += 20000
                                    else:
                                        buffer = tcp_socket_ID3.recv(len1, socket.MSG_WAITALL)
                                        # print("剩余不满20000的字节数为", len1, "读取的字节数为", len(buffer))  # 检查最后一次读取的字节数
                                        image_msg += buffer
                                        readlength += len1
                                        break

                                try:
                                    # 将读取到的字节流存储到图像文件中
                                    start = time.time()
                                    with open("image_file_ID3.jpg", "wb+") as img_file:
                                        img_file.write(image_msg)
                                    end = time.time()
                                    print("写入图片用时", end - start)
                                    imge = "image_file_ID3.jpg"
                                    self.sigImage.emit(imge)


                                except:
                                    print("图像数据出错")

                                # 继续检测包尾
                                left = tcp_socket_ID3.recv(1)
                                while 1:
                                    try:
                                        left_baowei = struct.unpack('B', left)
                                        # print("检测包尾读到的数据为", left_baowei)
                                    except:
                                        print("检测包尾第一个字节解析错误")

                                    # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                                    if (left_baowei == (204,)):  # 如果读到包尾则一次性读完包尾
                                        left = tcp_socket_ID3.recv(3)
                                        print("读完四个包尾")
                                        break
                                    else:
                                        left = tcp_socket_ID3.recv(1)

                                EndImage = time.time()  # 发送完图片时间
                                print("一次图片操作用时", EndImage - StartImage)

                            else:
                                    print("上传数据出错")
                            # 如果是ID为1的车发送的数据则进行接收


                while True:
                    # 创建一个线程去读取数据
                    read_thread = threading.Thread(target=read_thread_method)
                    # read_thread.setDaemon(True)  # 守护线程，read_thread作为一个守护线程，主线程结束，其立马也随之结束
                    read_thread.start()
                    # 要在线程执行完毕后在关闭套接字，不然会报错：在一个非套接字上尝试了一个操作
                    # read_thread.join()  # join 设置为主线程等待子线程结束后再继续执行主线程


                    #
                    #     askimage_thread = threading.Thread(target=askimage_method)
                    #     askimage_thread.start()
                    #     print("开启主动请求图像线程")

                    while True:

                        j = 0  # 请求状态数据时的计数
                        h = 0  # 请求图像数据时的计数

                        ###=======================上位机主动下发第一组经纬度数据
                        if (sendFlag_ID3 == 1):
                            print("下发第一组数据")
                            baotou_1 = 0xff  # char
                            baotou_2 = 0xff  # char
                            baotou_3 = 0xff  # char
                            baotou_4 = 0xff  # char
                            baochang_1 = 128  # int  包长  字节对齐会在double前面加上四个字节00000000
                            baoxuhao_1 = 1  # int  发送次数
                            shijianchuo_1 = 0  # int  上位机下发设为0
                            # zhongduanID_1 = 1  # int  终端ID
                            shujuyu_11 = 1  # int  类型1表示下发经纬度
                            shujuyu_21 = 84  # int  5个经纬度数组，一共80字节
                            dianshu_11 = 5  # I 下发5个点

                            ## 数据块之前的内容
                            data_11 = [baotou_1, baotou_2, baotou_3, baotou_4, baochang_1, baoxuhao_1, shijianchuo_1,

                                       shujuyu_11, shujuyu_21, dianshu_11]

                            #####################################--------------------------------------------数据域
                            file_path = "jingweidu.txt"  # 经纬度存储文件名

                            with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                t_sum1 = len(f.readlines())  # 总共有的经纬度组数

                                if 6 < t_sum1:  # 保证文档里经纬度数据大于五个

                                    for n in range(1, 6):
                                        line_number_1 = n  # 文件行数从1开始
                                        fread_n = linecache.getline(file_path, line_number_1).strip()  # 读取对应行数的经纬度
                                        fread_n_num = fread_n.strip("()")  # 删去字符串中左右两边的括号
                                        fread_split = fread_n_num.split(",")
                                        fread_n_jingdu = fread_split[0]  # 每行的经度str
                                        fread_n_weidu = fread_split[1]  # 每行的纬度str

                                        jingdu_1 = float(fread_n_jingdu)
                                        weidu_1 = float(fread_n_weidu)
                                        data_11.append(jingdu_1)
                                        data_11.append(weidu_1)
                                else:
                                    print("已经发送完毕所有数据")
                            f.close()

                            yuliu_1 = 0x00
                            # 循环加入12个0x00表示预留位和CRC32位
                            for s in range(0, 12):
                                data_11.append(yuliu_1)

                            baowei_1 = 0xee
                            # 循环加入四个0xee表示包尾
                            for t in range(0, 4):
                                data_11.append(baowei_1)

                            ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                            # 为小端接收模式
                            dataTobytes_1 = struct.pack('4B6i10d16B', data_11[0], data_11[1], data_11[2], data_11[3],
                                                        data_11[4], data_11[5]
                                                        , data_11[6], data_11[7], data_11[8], data_11[9], data_11[10],
                                                        data_11[11]
                                                        , data_11[12], data_11[13], data_11[14], data_11[15],
                                                        data_11[16],
                                                        data_11[17], data_11[18], data_11[19]
                                                        , data_11[20], data_11[21], data_11[22], data_11[23],
                                                        data_11[24],
                                                        data_11[25], data_11[26], data_11[27]
                                                        , data_11[28], data_11[29], data_11[30], data_11[31],
                                                        data_11[32],
                                                        data_11[33], data_11[34], data_11[35]

                                                        )
                            # print(type(dataTobytes_1), len(dataTobytes_1))

                            tcp_socket_ID3.send(dataTobytes_1)
                            sendFlag_ID3 = 0
                            ###=======================上位机主动下发第一组经纬度数据


                        if (askstateFlag_ID3 == 1):  # 如果请求状态按钮被激活则 下发请求状态指令，小车发送任意指令上位机均可以下发请求指令
                            askstate_thread_ID3 = threading.Thread(target=askstate_method_ID3)
                            askstate_thread_ID3.start()
                            print("开启主动请求状态线程")
                            print("askstateFlag_ID3:", askstateFlag_ID3)

                        if (askstateFlag_ID3 == 2):
                            print("开始请求车辆状态的数据")

                            send_state_baotou = 0xff  # 包头
                            send_state_baochang = 44  # 包长度，请求时数据域为0字节
                            send_state_xuhao = j  # 包序号
                            send_state_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_state_ID = 1  # int 固定车辆ID号
                            send_state_shujuyu_1 = 2  # int 第二类终端状态请求
                            send_state_shujuyu_2 = 0  # int 请求状态时L为0
                            send_state_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_state_yuliu = 0x00  # 保留帧暂时填充
                            send_state_baowei = 0xee  # 结束帧暂时填充

                            send_state_dataTobytes = []
                            for state_i in range(0, 4):
                                send_state_dataTobytes.append(send_state_baotou)
                            send_state_dataTobytes.append(send_state_baochang)
                            send_state_dataTobytes.append(send_state_xuhao)
                            send_state_dataTobytes.append(send_state_timechuo)
                            # send_state_dataTobytes.append(send_state_ID)
                            send_state_dataTobytes.append(send_state_shujuyu_1)
                            send_state_dataTobytes.append(send_state_shujuyu_2)
                            for state_j in range(0, 8):
                                send_state_dataTobytes.append(send_state_yuliu)

                            for state_k in range(0, 4):
                                send_state_dataTobytes.append(send_state_CRC32)

                            for state_l in range(0, 4):
                                send_state_dataTobytes.append(send_state_baowei)

                            dataTobytes_state = struct.pack('4B3i2I16B', send_state_dataTobytes[0],
                                                            send_state_dataTobytes[1], send_state_dataTobytes[2],
                                                            send_state_dataTobytes[3]
                                                            , send_state_dataTobytes[4], send_state_dataTobytes[5],
                                                            send_state_dataTobytes[6], send_state_dataTobytes[7]
                                                            , send_state_dataTobytes[8], send_state_dataTobytes[9],
                                                            send_state_dataTobytes[10], send_state_dataTobytes[11]
                                                            , send_state_dataTobytes[12], send_state_dataTobytes[13],
                                                            send_state_dataTobytes[14], send_state_dataTobytes[15]
                                                            , send_state_dataTobytes[16], send_state_dataTobytes[17],
                                                            send_state_dataTobytes[18], send_state_dataTobytes[19]
                                                            , send_state_dataTobytes[20], send_state_dataTobytes[21],
                                                            send_state_dataTobytes[22], send_state_dataTobytes[23]
                                                            , send_state_dataTobytes[24])

                            tcp_socket_ID3.send(dataTobytes_state)
                            askstateFlag_ID3 = 0  # 发送完后重新把标志位置零
                            j += 1
                        ####======================上位机向下位机发送请求状态数据的请求

                        ##==========================上位机向下位机请求图像数据
                        if (askimageFlag_ID3 == 1):  # 请求图像按钮被按下时激活，向下发送请求图像指令，小车发送任意数据上位机均可以下发请求指令
                            askimage_thread_ID3 = threading.Thread(target=askimage_method_ID3)
                            askimage_thread_ID3.start()
                            print("开启主动请求图像线程")
                            print("askimageFlag_ID3:", askimageFlag_ID3)

                        if (askimageFlag_ID3 == 2):
                            print("开始请求图像的数据")
                            send_image_baotou = 0xff  # 包头
                            send_image_baochang = 44  # 包长度，请求时数据域为0字节
                            send_image_xuhao = h  # 包序号
                            send_image_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_image_ID = 1  # int 固定车辆ID号
                            send_image_shujuyu_1 = 3  # int 第三类终端状态请求
                            send_image_shujuyu_2 = 0  # int 请求图像时L为0
                            send_image_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_image_yuliu = 0x00  # 保留帧暂时填充
                            send_image_baowei = 0xee  # 结束帧暂时填充

                            send_image_dataTobytes = []
                            for image_i in range(0, 4):
                                send_image_dataTobytes.append(send_image_baotou)
                            send_image_dataTobytes.append(send_image_baochang)
                            send_image_dataTobytes.append(send_image_xuhao)
                            send_image_dataTobytes.append(send_image_timechuo)
                            # send_image_dataTobytes.append(send_image_ID)
                            send_image_dataTobytes.append(send_image_shujuyu_1)
                            send_image_dataTobytes.append(send_image_shujuyu_2)
                            for image_j in range(0, 8):
                                send_image_dataTobytes.append(send_image_yuliu)

                            for state_k in range(0, 4):
                                send_image_dataTobytes.append(send_image_CRC32)

                            for state_l in range(0, 4):
                                send_image_dataTobytes.append(send_image_baowei)

                            dataTobytes_image = struct.pack('4B3i2I16B', send_image_dataTobytes[0],
                                                            send_image_dataTobytes[1], send_image_dataTobytes[2],
                                                            send_image_dataTobytes[3]
                                                            , send_image_dataTobytes[4], send_image_dataTobytes[5],
                                                            send_image_dataTobytes[6], send_image_dataTobytes[7]
                                                            , send_image_dataTobytes[8], send_image_dataTobytes[9],
                                                            send_image_dataTobytes[10], send_image_dataTobytes[11]
                                                            , send_image_dataTobytes[12], send_image_dataTobytes[13],
                                                            send_image_dataTobytes[14], send_image_dataTobytes[15]
                                                            , send_image_dataTobytes[16], send_image_dataTobytes[17],
                                                            send_image_dataTobytes[18], send_image_dataTobytes[19]
                                                            , send_image_dataTobytes[20], send_image_dataTobytes[21],
                                                            send_image_dataTobytes[22], send_image_dataTobytes[23]
                                                            , send_image_dataTobytes[24])

                            # client.send(dataTobytes_image)  # 发送请求的信号的数据格式
                            tcp_socket_ID3.send(dataTobytes_image)
                            askimageFlag_ID3 = 0  # 发送后标志位重新置零
                            h += 1
                        ##==========================上位机向下位机请求图像数据

                    # 清理socket，同样道理，这里需要锁定和解锁
                    # socket_lock.acquire()
                    # read_thread.join()
                    tcp_socket_ID3.close()
                    tcp_socket_ID3 = None
                    # socket_lock.release()
                    # break

    def upSend(self, flag):
        pass

# 第四辆车的监听线程
class Listener_ID4(QThread):  # 创建子线程类
    listenFlag = 1
    connectFlag = 1
    sigID_ID4 = pyqtSignal(str)  # run方法中用来将上位机的数据传送到GUI界面上
    sigState_ID4 = pyqtSignal(str)
    sigL2v_ID4 = pyqtSignal(float)
    sigR2v_ID4 = pyqtSignal(float)
    sigU_ID4 = pyqtSignal(float)
    sigangle_ID4 = pyqtSignal(float)
    sigImage_ID4 = pyqtSignal(str)

    sigAy_ID4 = pyqtSignal(float)
    sigYaw_ID4 = pyqtSignal(float)
    sigTn_ID4 = pyqtSignal(float)
    sigVy_ID4 = pyqtSignal(float)


    sigLPWM_ID4 = pyqtSignal(float)
    sigRPWM_ID4 = pyqtSignal(float)

    siglat_ID4 = pyqtSignal(float)
    siglng_ID4 = pyqtSignal(float)



    def __init__(self, ip, port, serverIP, serverPort, length, weight, maxV,
                 minV, maxA, maxD):
        super(Listener_ID4, self).__init__()  # 继承父类的属性和方法

        self.L2vArr = []
        self.R2vArr = []
        self.dataFromCarDecode = ''
        self.serverFlag = 0
        self.flag = 1



    def run(self):
        global sendFlag_ID4  # 因为sendFlag是在方法外定义的变量，所以要在方法内使用的话加上global成为全局变量
        global startFlag
        global askstateFlag_ID4
        global askimageFlag_ID4
        global frame
        global askstate_imageFlag_ID4



        sendFlag_ID4 = 0
        startFlag = 0
        askstateFlag_ID4 = 0
        askimageFlag_ID4 = 0
        askstate_imageFlag_ID4 = 0

        def askimage_method_ID4():
            global askimageFlag_ID4
            while True:
                askimageFlag_ID4 = 2
                time.sleep(10)  # 每隔10秒主动请求一次图像数据

        def askstate_method_ID4():
            global askstateFlag_ID4
            while True:
                askstateFlag_ID4 = 2
                time.sleep(5)  # 每隔5秒主动请求一次状态数据

        # ===================================接收上传经纬度数据并写入json文件
        # i=0
        def fun_time_ID4(lng_ID1, lat_ID2):  # 将上传的经纬度数据写入json文件中供BD_map.html文件读取
            # global i
            with open("weather4.json", "w", encoding='utf-8') as f:  # 打开对应车辆的json文件写入数据

                dicts = {"lng": lng_ID1, "lat": lat_ID2}
                f.write(json.dumps(dicts, indent=4))  # Indent表示隔开四个单位
                # i = i + 2
                # if i > 2000:
                #     i = 0

        # ===================================接收上传经纬度数据并写入json文件

        while True:

            while (self.listenFlag):
                print("连接云端服务器")

                tcp_socket_ID4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # STREAM表示TCP传输
                tcp_socket_ID4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

                # 2.链接服务器
                # server_ip = input("请输入服务器ip地址：")
                # server_port = input("请输入服务器端口:")
                # tcp_socket.connect((str(server_ip), server_port))
                # tcp_socket.connect(("10.80.7.157", 8080))
                tcp_socket_ID4.connect(("47.102.36.187", 8088))   # 链接云端服务器

                # 创建线程锁，防止主线程socket被close了，子线程还在recv而引发的异常
                # socket_lock = threading.Lock()
                def read_thread_method():  # 读取数据的方法
                    print("接收线程开启")

                    while True:
                        if not tcp_socket_ID4:  # 如果socket关闭，退出
                            break
                        dataFromCar = tcp_socket_ID4.recv(1)  # 缓冲区大小，接收文件的个数

                        i = 1  # 下发经纬度数据时的计数,前五个数已经主动下发

                        if not dataFromCar:
                            print("小车停止上传数据")
                        else:
                            while True:
                                print("逐个读取字节")
                                try:
                                    z1 = struct.unpack('B', dataFromCar)
                                except:
                                    print("第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包头
                                if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                                    dataFromCar = tcp_socket_ID4.recv(3)
                                    break
                                else:
                                    dataFromCar = tcp_socket_ID4.recv(1)
                            # print("dataFromCar的长度", len(dataFromCar))
                            try:
                                x2, x3, x4 = struct.unpack('3B', dataFromCar)  # 包头
                            except:
                                print("包头解析错误")

                            dataFromCar = tcp_socket_ID4.recv(24)
                            try:
                                x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar)
                            except:
                                print("前24个字节解析错误")
                            ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2
                            # print("该段字节流包长", x5)  # 查看包长是否正确

                            # 如果是ID为1的车发送的数据则进行接收
                            # if (x8 == 4):
                            if (x5 == 44):  # 如果上发的是44字节的数据（请求下发经纬度时设下位机发送数据块为空）
                                # 发送数据示例 dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18  00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                print(" 请求下发经纬度数据")
                                dataFromCar_jingwei_to_car = tcp_socket_ID4.recv(16)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                # print("读取余下的字节为：", dataFromCar_jingwei_to_car)
                                baotou1 = 0xff  # char
                                baotou2 = 0xff  # char
                                baotou3 = 0xff  # char
                                baotou4 = 0xff  # char
                                baochang = 128  # int  i包长 字节对齐会在double前面加上四个字节00000000
                                baoxuhao = i  # int  i发送次数
                                shijianchuo = 0  # int  i上位机下发设为0
                                # zhongduanID = 1  # int  i终端ID
                                shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
                                shujuyu_2 = 84  # int  I 5个经纬度数组，一共80字节
                                dianshu = 5  # Uint32 I 下发5个点

                                ## 数据块之前的内容
                                data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,

                                          shujuyu_1, shujuyu_2, dianshu]

                                #####################################--------------------------------------------数据域
                                file_path = "jingweidu.txt"  # 经纬度存储文件名

                                with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                    t_sum = len(f.readlines())  # 总共有的经纬度组数

                                    # print("ccccccc文档的总行数为：", t_sum)
                                    if 5 * i + 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
                                        for j in range(5 * i + 1, 5 * i + 6):
                                            line_number = j  # 文件行数从1开始，而i初始值为0
                                            fread_j = linecache.getline(file_path,
                                                                        line_number).strip()  # 读取对应行数的经纬度
                                            fread_j_num = fread_j.strip("()")  # 删去字符串中左右两边的括号
                                            fread_split = fread_j_num.split(",")
                                            fread_j_jingdu = fread_split[0]  # 每行的经度str
                                            fread_j_weidu = fread_split[1]  # 每行的纬度str
                                            print(type(fread_j_jingdu))
                                            print(fread_j_jingdu)

                                            jingdu = float(fread_j_jingdu)
                                            weidu = float(fread_j_weidu)
                                            data_1.append(jingdu)
                                            data_1.append(weidu)
                                    else:
                                        print("已经发送完毕所有数据")
                                f.close()
                                # 加入数据块后的数据包
                                # print("data_1", data_1)

                                yuliu = 0x00
                                # 循环加入12个0x00表示预留位和CRC32位
                                for n in range(0, 12):
                                    data_1.append(yuliu)

                                baowei = 0xee
                                # 循环加入四个0xee表示包尾
                                for m in range(0, 4):
                                    data_1.append(baowei)
                                    # print(data_1)

                                # 显示完整数据包
                                # print(data_1)

                                ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                                # 为大端接收模式
                                dataTobytes = struct.pack('4B3i3I10d16B', data_1[0], data_1[1], data_1[2], data_1[3],
                                                          data_1[4],
                                                          data_1[5]
                                                          , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10],
                                                          data_1[11]
                                                          , data_1[12], data_1[13], data_1[14], data_1[15],
                                                          data_1[16],
                                                          data_1[17], data_1[18], data_1[19]
                                                          , data_1[20], data_1[21], data_1[22], data_1[23],
                                                          data_1[24],
                                                          data_1[25], data_1[26], data_1[27]
                                                          , data_1[28], data_1[29], data_1[30], data_1[31],
                                                          data_1[32],
                                                          data_1[33], data_1[34], data_1[35]

                                                          )
                                # print(type(dataTobytes), len(dataTobytes))

                                tcp_socket_ID4.send(dataTobytes)
                                # print(i)
                                i += 1

                                # 0xff, 0xff, 0xff, 0xff, 128, 0, 0, 1, 1, 80, 5, 120.04208246406465, 30.231343807768763, \
                                # 120.04207836129298, 30.23134029404531, 120.04207425852078, 30.231336780321374, \
                                # 120.04207015574802, 30.231333266596973, 120.0420660529747, 30.231329752872096, \
                                # 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xee, 0xee, 0xee
                            # ==========================================下传经纬度数据

                            ####-------------------  接收下位机上传数据
                            ##================================更新车辆状态数据以及检测废数据
                            elif (x5 == 68):  # 小车上发车辆状态数据
                                # print("该段字节流包长：", x5)
                                print("这是上发的车辆的状态信息")
                                # 1. 如果数据域前四个字节为0，则上传的为无效的废数据
                                # 2. 如果数据域前四个字节为1，则上传的是车辆的状态信息，分别更新GUI界面上的数据
                                # 3. 如果数据域前四个字节为2，则上传的是GPS的定位信息，提取经纬度数据用于控制算法
                                # 4. 如果数据区前四个字节为3，则上传的是图像信息，更新GUI界面上的图像数据
                                # 上传结构体数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                dataFromCar_state_from_car = tcp_socket_ID4.recv(40)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                if (x9 == 0):  # 数据域前四个字节为0x000x000x000x00,对应情况1
                                    print("这是无效的废数据")
                                else:
                                    try:
                                        x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32\
                                            = struct.unpack(
                                            'I2fIfI16B',
                                            dataFromCar_state_from_car)  # 4B4i3I2fIfI16B  解包C的结构体数据，大端格式加！（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                    except:
                                        print("解析状态数据出错")

                                    ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                    # print("接收数据转换成字符串为：", x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14,
                                    #       x15, x16,
                                    #       x17,
                                    #       x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32)

                                    ##==============================更新车辆状态数据
                                    # elif (len(dataFromCar) == 68):  # 数据域前四个字节为0x000x000x000x01,对应情况2
                                    self.serverFlag = 1  # 启动多线程服务器？

                                    ID = x8
                                    LPWM = x11  # 车辆状态
                                    RPWM = x15  # 电池电压
                                    L2v = x12  # 左轮电机转速
                                    R2V = x13  # 右轮电机转速
                                    angle = x14

                                    self.sigID_ID4.emit(str(ID))  # 往GUI界面中传入数据,注意ID传入的参数为int型要与Listener属性定义处的sigID类型一致

                                    self.sigL2v_ID4.emit(float(L2v))

                                    self.sigR2v_ID4.emit(float(R2V))

                                    self.sigangle_ID4.emit(float(angle))

                                    self.sigLPWM_ID4.emit(LPWM)

                                    self.sigRPWM_ID4.emit(RPWM)

                                    Ay = 111
                                    Yaw = 111
                                    Tn = 111
                                    Vy = 111

                                    self.sigAy_ID4.emit(Ay)
                                    self.sigYaw_ID4.emit(Yaw)
                                    self.sigTn_ID4.emit(Tn)
                                    self.sigVy_ID4.emit(Vy)



                                    # ================写入数据库
                                    conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                           autocommit=True)

                                    # 使用cursor()方法获取操作游标
                                    cursor1 = conn.cursor()

                                    # SQL语句：向数据表中插入数据
                                    # sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                    #                                              VALUES (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)"""  # 修改这一行数据，可多次插入
                                    sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                                                                values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""  # 修改这一行数据，可多次插入
                                    data_state = (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)
                                    # 异常处理
                                    try:
                                        # 执行SQL语句
                                        cursor1.execute(sql1, data_state)
                                        # 提交事务到数据库执行
                                        conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                        print("状态数据写入数据库")
                                    except:
                                        # 如果发生错误则执行回滚操作
                                        conn.rollback()

                                    # 关闭数据库连接
                                    conn.close()
                                    ##############写入数据库

                                    # self.stateButton.setCheckable(False)
                                ##==============================更新车辆状态数据
                            ##================================更新车辆状态数据以及检测废数据

                            ##================================获取车辆上传的GPS定位数据
                            elif (x5 == 64):  # 如果上传的数据为64字节，则对应车辆目前GPS获取的经纬度数据
                                Start_LngLat = time.time()  # 开始读取经纬度的时间点
                                print("这是车辆所处的经纬度")
                                # 上传数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                # 数据块：N 的十六进制为4E; P的十六进制为50；L为4C；B为42；卫星个数：01；填充数据： 00 00
                                # 经度：（120.04208246406465）40 5E 02 B1 7A A5 B9 23  纬度：（30.231343807768763）40 3E 3B 39 59 08 7F BB
                                # 120.04862759640338  \x40\x5e\x03\x1c\xb6\xec\x0f\x14  30.237128736109234  \x40\x3e\x3c\xb4\x78\x06\x87\xee
                                # 120.0457642526888  \x40\x5e\x02\xed\xcd\x30\x27\xf4  30.23500645123769  \x40\x3e\x3c\x29\x61\xfe\x6a\x37
                                dataFromCar_jingwei_from_car = tcp_socket_ID4.recv(4)  # 接收GPS等
                                try:
                                    y11, y12, y13, y14 = struct.unpack('4B', dataFromCar_jingwei_from_car)
                                except:
                                    print("解析GPS/卫星数据出错")
                                GPS = y11  # GPS协议类型
                                Star = y12  # 卫星个数
                                print("GPS:", str(GPS))
                                print("卫星个数：", int(Star))

                                dataFromCar_jingwei_from_car = tcp_socket_ID4.recv(32)
                                try:
                                    y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31, y32 \
                                        = struct.unpack(
                                        '2d16B',
                                        dataFromCar_jingwei_from_car)  # 4B4i2I4B2d16B 解包C的结构体数据,大端格式加！,h表示两个字节的short型数据（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                except:
                                    print("解析经纬度数据出错")

                                ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                # print("接收数据转换成字符串为：", y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14,
                                #       y15, y16,
                                #       y17,
                                #       y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31,y32)

                                jingdu_Car = y15  # 小车所处经度
                                weidu_Car = y16  # 小车所处纬度
                                lng = y15
                                lat = y16
                                converted = []
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))


                                #================写入数据库
                                conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                       autocommit=True)

                                # 使用cursor()方法获取操作游标
                                cursor2 = conn.cursor()

                                # SQL语句：向数据表中插入数据
                                # sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)VALUES (x6, y11,y15,y16)"""  # 修改这一行数据，可多次插入
                                # VALUES 里的数据的类型一定要与定义表时的类型一致,该方法适合传入给定数据，如果是变量则要用（"%s",%d）等格式字符
                                sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)values("%s","%s","%s","%s")"""  # 修改这一行数据，可多次插入
                                data_lnglat = (x8, y11, y15, y16)

                                # 异常处理
                                try:
                                    # 执行SQL语句
                                    cursor2.execute(sql2, data_lnglat)
                                    # 提交事务到数据库执行
                                    conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                    print("经纬度数据写入数据库")
                                except:
                                    # 如果发生错误则执行回滚操作
                                    conn.rollback()

                                # 关闭数据库连接
                                conn.close()
                                ##############写入数据库


                                converted = wgs84_to_bd09_change.gcj02_to_bd09(y15,
                                                                               y16)  # 调用外部函数将谷歌地图GPS经纬度数据转换成百度地图格式

                                fun_time_ID4(converted[0], converted[1])

                                # ti = threading.Thread(target=fun_time, args=(converted[0], converted[1])) ##传入经纬度和车辆ID，将其写入对应的json文件
                                # ti.start()

                                self.siglng_ID4.emit(float(converted[0]))
                                self.siglat_ID4.emit(float(converted[1]))
                                # time.sleep(1)

                                End_Lnglat = time.time()
                                print("执行一次经纬度数据读取用时", End_Lnglat - Start_LngLat)

                                # print("GPS:", str(GPS))
                                # print("卫星个数：", int(Star))
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))
                            ##================================获取车辆上传的GPS定位数据

                            elif (x9 == 3 ):  # 如果上传数据字节数过多，则为图像信息

                                print("上传的是图像数据")
                                # def ImageRead():
                                StartImage = time.time()  # 开始读取图片数据

                                data_image = tcp_socket_ID4.recv(1)
                                try:
                                    image_geshi = struct.unpack('B', data_image)
                                except:
                                    print("解析图像格式出错")
                                # print("图像格式为：", image_geshi)
                                data_image = tcp_socket_ID4.recv(4)
                                try:
                                    image_len = struct.unpack('1I', data_image)
                                except:
                                    print("解析图像字节数出错")
                                print("图像字节数：", image_len)

                                image_msg = b''
                                # print("帧中读取的图像数据块字节数，未转化成int型前：", image_len)
                                len1 = int(image_len[0])  # 图像数据的字节长度
                                # print("转化成int型后：", len1)
                                image_length = len1
                                readlength = 0  # 从缓冲区读取的字节数
                                while (len1 > 0):
                                    if len1 > 20000:  # 如果剩余图像字节数大于20000
                                        buffer = tcp_socket_ID4.recv(20000,
                                                                     socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                        # print("本次recv收到的字节是否为20000，", len(buffer))  # 检查每次recv是否收到完整的1024个字节
                                        image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                        len1 = len1 - 20000
                                        readlength += 20000
                                    else:
                                        buffer = tcp_socket_ID4.recv(len1, socket.MSG_WAITALL)
                                        # print("剩余不满20000的字节数为", len1, "读取的字节数为", len(buffer))  # 检查最后一次读取的字节数
                                        image_msg += buffer
                                        readlength += len1
                                        break

                                try:
                                    # 将读取到的字节流存储到图像文件中
                                    start = time.time()
                                    with open("image_file_ID4.jpg", "wb+") as img_file:
                                        img_file.write(image_msg)
                                    end = time.time()
                                    print("写入图片用时", end - start)
                                    imge = "image_file_ID4.jpg"
                                    self.sigImage.emit(imge)


                                except:
                                    print("图像数据出错")

                                # 继续检测包尾
                                left = tcp_socket_ID4.recv(1)
                                while 1:
                                    try:
                                        left_baowei = struct.unpack('B', left)
                                        # print("检测包尾读到的数据为", left_baowei)
                                    except:
                                        print("检测包尾第一个字节解析错误")

                                    # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                                    if (left_baowei == (204,)):  # 如果读到包尾则一次性读完包尾
                                        left = tcp_socket_ID4.recv(3)
                                        print("读完四个包尾")
                                        break
                                    else:
                                        left = tcp_socket_ID4.recv(1)

                                EndImage = time.time()  # 发送完图片时间
                                print("一次图片操作用时", EndImage - StartImage)

                            else:
                                    print("上传数据出错")
                            # 如果是ID为1的车发送的数据则进行接收


                while True:
                    # 创建一个线程去读取数据
                    read_thread = threading.Thread(target=read_thread_method)
                    # read_thread.setDaemon(True)  # 守护线程，read_thread作为一个守护线程，主线程结束，其立马也随之结束
                    read_thread.start()
                    # 要在线程执行完毕后在关闭套接字，不然会报错：在一个非套接字上尝试了一个操作
                    # read_thread.join()  # join 设置为主线程等待子线程结束后再继续执行主线程


                    #
                    #     askimage_thread = threading.Thread(target=askimage_method)
                    #     askimage_thread.start()
                    #     print("开启主动请求图像线程")

                    while True:

                        j = 0  # 请求状态数据时的计数
                        h = 0  # 请求图像数据时的计数

                        ###=======================上位机主动下发第一组经纬度数据
                        if (sendFlag_ID4 == 1):
                            print("下发第一组数据")
                            baotou_1 = 0xff  # char
                            baotou_2 = 0xff  # char
                            baotou_3 = 0xff  # char
                            baotou_4 = 0xff  # char
                            baochang_1 = 128  # int  包长  字节对齐会在double前面加上四个字节00000000
                            baoxuhao_1 = 1  # int  发送次数
                            shijianchuo_1 = 0  # int  上位机下发设为0
                            # zhongduanID_1 = 1  # int  终端ID
                            shujuyu_11 = 1  # int  类型1表示下发经纬度
                            shujuyu_21 = 84  # int  5个经纬度数组，一共80字节
                            dianshu_11 = 5  # I 下发5个点

                            ## 数据块之前的内容
                            data_11 = [baotou_1, baotou_2, baotou_3, baotou_4, baochang_1, baoxuhao_1, shijianchuo_1,

                                       shujuyu_11, shujuyu_21, dianshu_11]

                            #####################################--------------------------------------------数据域
                            file_path = "jingweidu.txt"  # 经纬度存储文件名

                            with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                t_sum1 = len(f.readlines())  # 总共有的经纬度组数

                                if 6 < t_sum1:  # 保证文档里经纬度数据大于五个

                                    for n in range(1, 6):
                                        line_number_1 = n  # 文件行数从1开始
                                        fread_n = linecache.getline(file_path, line_number_1).strip()  # 读取对应行数的经纬度
                                        fread_n_num = fread_n.strip("()")  # 删去字符串中左右两边的括号
                                        fread_split = fread_n_num.split(",")
                                        fread_n_jingdu = fread_split[0]  # 每行的经度str
                                        fread_n_weidu = fread_split[1]  # 每行的纬度str

                                        jingdu_1 = float(fread_n_jingdu)
                                        weidu_1 = float(fread_n_weidu)
                                        data_11.append(jingdu_1)
                                        data_11.append(weidu_1)
                                else:
                                    print("已经发送完毕所有数据")
                            f.close()

                            yuliu_1 = 0x00
                            # 循环加入12个0x00表示预留位和CRC32位
                            for s in range(0, 12):
                                data_11.append(yuliu_1)

                            baowei_1 = 0xee
                            # 循环加入四个0xee表示包尾
                            for t in range(0, 4):
                                data_11.append(baowei_1)

                            ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                            # 为小端接收模式
                            dataTobytes_1 = struct.pack('4B6i10d16B', data_11[0], data_11[1], data_11[2], data_11[3],
                                                        data_11[4], data_11[5]
                                                        , data_11[6], data_11[7], data_11[8], data_11[9], data_11[10],
                                                        data_11[11]
                                                        , data_11[12], data_11[13], data_11[14], data_11[15],
                                                        data_11[16],
                                                        data_11[17], data_11[18], data_11[19]
                                                        , data_11[20], data_11[21], data_11[22], data_11[23],
                                                        data_11[24],
                                                        data_11[25], data_11[26], data_11[27]
                                                        , data_11[28], data_11[29], data_11[30], data_11[31],
                                                        data_11[32],
                                                        data_11[33], data_11[34], data_11[35]

                                                        )
                            # print(type(dataTobytes_1), len(dataTobytes_1))

                            tcp_socket_ID4.send(dataTobytes_1)
                            sendFlag_ID4 = 0
                            ###=======================上位机主动下发第一组经纬度数据


                        if (askstateFlag_ID4 == 1):  # 如果请求状态按钮被激活则 下发请求状态指令，小车发送任意指令上位机均可以下发请求指令
                            askstate_thread_ID4 = threading.Thread(target=askstate_method_ID4)
                            askstate_thread_ID4.start()
                            print("开启主动请求状态线程")
                            print("askstateFlag_ID4:", askstateFlag_ID4)

                        if (askstateFlag_ID4 == 2):
                            print("开始请求车辆状态的数据")

                            send_state_baotou = 0xff  # 包头
                            send_state_baochang = 44  # 包长度，请求时数据域为0字节
                            send_state_xuhao = j  # 包序号
                            send_state_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_state_ID = 1  # int 固定车辆ID号
                            send_state_shujuyu_1 = 2  # int 第二类终端状态请求
                            send_state_shujuyu_2 = 0  # int 请求状态时L为0
                            send_state_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_state_yuliu = 0x00  # 保留帧暂时填充
                            send_state_baowei = 0xee  # 结束帧暂时填充

                            send_state_dataTobytes = []
                            for state_i in range(0, 4):
                                send_state_dataTobytes.append(send_state_baotou)
                            send_state_dataTobytes.append(send_state_baochang)
                            send_state_dataTobytes.append(send_state_xuhao)
                            send_state_dataTobytes.append(send_state_timechuo)
                            # send_state_dataTobytes.append(send_state_ID)
                            send_state_dataTobytes.append(send_state_shujuyu_1)
                            send_state_dataTobytes.append(send_state_shujuyu_2)
                            for state_j in range(0, 8):
                                send_state_dataTobytes.append(send_state_yuliu)

                            for state_k in range(0, 4):
                                send_state_dataTobytes.append(send_state_CRC32)

                            for state_l in range(0, 4):
                                send_state_dataTobytes.append(send_state_baowei)

                            dataTobytes_state = struct.pack('4B3i2I16B', send_state_dataTobytes[0],
                                                            send_state_dataTobytes[1], send_state_dataTobytes[2],
                                                            send_state_dataTobytes[3]
                                                            , send_state_dataTobytes[4], send_state_dataTobytes[5],
                                                            send_state_dataTobytes[6], send_state_dataTobytes[7]
                                                            , send_state_dataTobytes[8], send_state_dataTobytes[9],
                                                            send_state_dataTobytes[10], send_state_dataTobytes[11]
                                                            , send_state_dataTobytes[12], send_state_dataTobytes[13],
                                                            send_state_dataTobytes[14], send_state_dataTobytes[15]
                                                            , send_state_dataTobytes[16], send_state_dataTobytes[17],
                                                            send_state_dataTobytes[18], send_state_dataTobytes[19]
                                                            , send_state_dataTobytes[20], send_state_dataTobytes[21],
                                                            send_state_dataTobytes[22], send_state_dataTobytes[23]
                                                            , send_state_dataTobytes[24])

                            tcp_socket_ID4.send(dataTobytes_state)
                            askstateFlag_ID4 = 0  # 发送完后重新把标志位置零
                            j += 1
                        ####======================上位机向下位机发送请求状态数据的请求

                        ##==========================上位机向下位机请求图像数据
                        if (askimageFlag_ID4 == 1):  # 请求图像按钮被按下时激活，向下发送请求图像指令，小车发送任意数据上位机均可以下发请求指令
                            askimage_thread_ID4 = threading.Thread(target=askimage_method_ID4)
                            askimage_thread_ID4.start()
                            print("开启主动请求图像线程")
                            print("askimageFlag_ID4:", askimageFlag_ID4)

                        if (askimageFlag_ID4 == 2):
                            print("开始请求图像的数据")
                            send_image_baotou = 0xff  # 包头
                            send_image_baochang = 44  # 包长度，请求时数据域为0字节
                            send_image_xuhao = h  # 包序号
                            send_image_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_image_ID = 1  # int 固定车辆ID号
                            send_image_shujuyu_1 = 3  # int 第三类终端状态请求
                            send_image_shujuyu_2 = 0  # int 请求图像时L为0
                            send_image_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_image_yuliu = 0x00  # 保留帧暂时填充
                            send_image_baowei = 0xee  # 结束帧暂时填充

                            send_image_dataTobytes = []
                            for image_i in range(0, 4):
                                send_image_dataTobytes.append(send_image_baotou)
                            send_image_dataTobytes.append(send_image_baochang)
                            send_image_dataTobytes.append(send_image_xuhao)
                            send_image_dataTobytes.append(send_image_timechuo)
                            # send_image_dataTobytes.append(send_image_ID)
                            send_image_dataTobytes.append(send_image_shujuyu_1)
                            send_image_dataTobytes.append(send_image_shujuyu_2)
                            for image_j in range(0, 8):
                                send_image_dataTobytes.append(send_image_yuliu)

                            for state_k in range(0, 4):
                                send_image_dataTobytes.append(send_image_CRC32)

                            for state_l in range(0, 4):
                                send_image_dataTobytes.append(send_image_baowei)

                            dataTobytes_image = struct.pack('4B3i2I16B', send_image_dataTobytes[0],
                                                            send_image_dataTobytes[1], send_image_dataTobytes[2],
                                                            send_image_dataTobytes[3]
                                                            , send_image_dataTobytes[4], send_image_dataTobytes[5],
                                                            send_image_dataTobytes[6], send_image_dataTobytes[7]
                                                            , send_image_dataTobytes[8], send_image_dataTobytes[9],
                                                            send_image_dataTobytes[10], send_image_dataTobytes[11]
                                                            , send_image_dataTobytes[12], send_image_dataTobytes[13],
                                                            send_image_dataTobytes[14], send_image_dataTobytes[15]
                                                            , send_image_dataTobytes[16], send_image_dataTobytes[17],
                                                            send_image_dataTobytes[18], send_image_dataTobytes[19]
                                                            , send_image_dataTobytes[20], send_image_dataTobytes[21],
                                                            send_image_dataTobytes[22], send_image_dataTobytes[23]
                                                            , send_image_dataTobytes[24])

                            # client.send(dataTobytes_image)  # 发送请求的信号的数据格式
                            tcp_socket_ID4.send(dataTobytes_image)
                            askimageFlag_ID4 = 0  # 发送后标志位重新置零
                            h += 1
                        ##==========================上位机向下位机请求图像数据

                    # 清理socket，同样道理，这里需要锁定和解锁
                    # socket_lock.acquire()
                    # read_thread.join()
                    tcp_socket_ID4.close()
                    tcp_socket_ID4 = None
                    # socket_lock.release()
                    # break

    def upSend(self, flag):
        pass

# 第五辆车的监听线程
class Listener_ID5(QThread):  # 创建子线程类
    listenFlag = 1
    connectFlag = 1
    sigID_ID5 = pyqtSignal(str)  # run方法中用来将上位机的数据传送到GUI界面上
    sigState_ID5 = pyqtSignal(str)
    sigL2v_ID5 = pyqtSignal(float)
    sigR2v_ID5 = pyqtSignal(float)
    sigU_ID5 = pyqtSignal(float)
    sigangle_ID5 = pyqtSignal(float)
    sigImage_ID5 = pyqtSignal(str)

    sigAy_ID5 = pyqtSignal(float)
    sigYaw_ID5 = pyqtSignal(float)
    sigTn_ID5 = pyqtSignal(float)
    sigVy_ID5 = pyqtSignal(float)


    sigLPWM_ID5 = pyqtSignal(float)
    sigRPWM_ID5 = pyqtSignal(float)

    siglat_ID5 = pyqtSignal(float)
    siglng_ID5 = pyqtSignal(float)



    def __init__(self, ip, port, serverIP, serverPort, length, weight, maxV,
                 minV, maxA, maxD):
        super(Listener_ID5, self).__init__()  # 继承父类的属性和方法

        self.L2vArr = []
        self.R2vArr = []
        self.dataFromCarDecode = ''
        self.serverFlag = 0
        self.flag = 1



    def run(self):
        global sendFlag_ID5  # 因为sendFlag是在方法外定义的变量，所以要在方法内使用的话加上global成为全局变量
        global startFlag
        global askstateFlag_ID5
        global askimageFlag_ID5
        global frame
        global askstate_imageFlag_ID5



        sendFlag_ID5 = 0
        startFlag = 0
        askstateFlag_ID5 = 0
        askimageFlag_ID5 = 0
        askstate_imageFlag_ID5 = 0

        def askimage_method_ID5():
            global askimageFlag_ID5
            while True:
                askimageFlag_ID5 = 2
                time.sleep(10)  # 每隔10秒主动请求一次图像数据

        def askstate_method_ID5():
            global askstateFlag_ID5
            while True:
                askstateFlag_ID5 = 2
                time.sleep(5)  # 每隔5秒主动请求一次状态数据

        # ===================================接收上传经纬度数据并写入json文件
        # i=0
        def fun_time_ID5(lng_ID1, lat_ID2):  # 将上传的经纬度数据写入json文件中供BD_map.html文件读取
            # global i
            with open("weather5.json", "w", encoding='utf-8') as f:  # 打开对应车辆的json文件写入数据

                dicts = {"lng": lng_ID1, "lat": lat_ID2}
                f.write(json.dumps(dicts, indent=4))  # Indent表示隔开四个单位
                # i = i + 2
                # if i > 2000:
                #     i = 0

        # ===================================接收上传经纬度数据并写入json文件

        while True:

            while (self.listenFlag):
                print("连接云端服务器")

                tcp_socket_ID5 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # STREAM表示TCP传输
                tcp_socket_ID5.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

                # 2.链接服务器
                # server_ip = input("请输入服务器ip地址：")
                # server_port = input("请输入服务器端口:")
                # tcp_socket.connect((str(server_ip), server_port))
                # tcp_socket.connect(("10.80.7.157", 8080))
                tcp_socket_ID5.connect(("47.102.36.187", 8090))   # 链接云端服务器

                # 创建线程锁，防止主线程socket被close了，子线程还在recv而引发的异常
                # socket_lock = threading.Lock()
                def read_thread_method():  # 读取数据的方法
                    print("接收线程开启")

                    while True:
                        if not tcp_socket_ID5:  # 如果socket关闭，退出
                            break
                        dataFromCar = tcp_socket_ID5.recv(1)  # 缓冲区大小，接收文件的个数

                        i = 1  # 下发经纬度数据时的计数,前五个数已经主动下发

                        if not dataFromCar:
                            print("小车停止上传数据")
                        else:
                            while True:
                                print("逐个读取字节")
                                try:
                                    z1 = struct.unpack('B', dataFromCar)
                                except:
                                    print("第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包头
                                if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                                    dataFromCar = tcp_socket_ID5.recv(3)
                                    break
                                else:
                                    dataFromCar = tcp_socket_ID5.recv(1)
                            # print("dataFromCar的长度", len(dataFromCar))
                            try:
                                x2, x3, x4 = struct.unpack('3B', dataFromCar)  # 包头
                            except:
                                print("包头解析错误")

                            dataFromCar = tcp_socket_ID5.recv(24)
                            try:
                                x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar)
                            except:
                                print("前24个字节解析错误")
                            ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2
                            # print("该段字节流包长", x5)  # 查看包长是否正确

                            # 如果是ID为1的车发送的数据则进行接收
                            # if (x8 == 5):
                            if (x5 == 44):  # 如果上发的是44字节的数据（请求下发经纬度时设下位机发送数据块为空）
                                # 发送数据示例 dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18  00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                print(" 请求下发经纬度数据")
                                dataFromCar_jingwei_to_car = tcp_socket_ID5.recv(16)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                # print("读取余下的字节为：", dataFromCar_jingwei_to_car)
                                baotou1 = 0xff  # char
                                baotou2 = 0xff  # char
                                baotou3 = 0xff  # char
                                baotou4 = 0xff  # char
                                baochang = 128  # int  i包长 字节对齐会在double前面加上四个字节00000000
                                baoxuhao = i  # int  i发送次数
                                shijianchuo = 0  # int  i上位机下发设为0
                                # zhongduanID = 1  # int  i终端ID
                                shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
                                shujuyu_2 = 84  # int  I 5个经纬度数组，一共80字节
                                dianshu = 5  # Uint32 I 下发5个点

                                ## 数据块之前的内容
                                data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,

                                          shujuyu_1, shujuyu_2, dianshu]

                                #####################################--------------------------------------------数据域
                                file_path = "jingweidu.txt"  # 经纬度存储文件名

                                with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                    t_sum = len(f.readlines())  # 总共有的经纬度组数

                                    # print("ccccccc文档的总行数为：", t_sum)
                                    if 5 * i + 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
                                        for j in range(5 * i + 1, 5 * i + 6):
                                            line_number = j  # 文件行数从1开始，而i初始值为0
                                            fread_j = linecache.getline(file_path,
                                                                        line_number).strip()  # 读取对应行数的经纬度
                                            fread_j_num = fread_j.strip("()")  # 删去字符串中左右两边的括号
                                            fread_split = fread_j_num.split(",")
                                            fread_j_jingdu = fread_split[0]  # 每行的经度str
                                            fread_j_weidu = fread_split[1]  # 每行的纬度str
                                            print(type(fread_j_jingdu))
                                            print(fread_j_jingdu)

                                            jingdu = float(fread_j_jingdu)
                                            weidu = float(fread_j_weidu)
                                            data_1.append(jingdu)
                                            data_1.append(weidu)
                                    else:
                                        print("已经发送完毕所有数据")
                                f.close()
                                # 加入数据块后的数据包
                                # print("data_1", data_1)

                                yuliu = 0x00
                                # 循环加入12个0x00表示预留位和CRC32位
                                for n in range(0, 12):
                                    data_1.append(yuliu)

                                baowei = 0xee
                                # 循环加入四个0xee表示包尾
                                for m in range(0, 4):
                                    data_1.append(baowei)
                                    # print(data_1)

                                # 显示完整数据包
                                # print(data_1)

                                ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                                # 为大端接收模式
                                dataTobytes = struct.pack('4B3i3I10d16B', data_1[0], data_1[1], data_1[2], data_1[3],
                                                          data_1[4],
                                                          data_1[5]
                                                          , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10],
                                                          data_1[11]
                                                          , data_1[12], data_1[13], data_1[14], data_1[15],
                                                          data_1[16],
                                                          data_1[17], data_1[18], data_1[19]
                                                          , data_1[20], data_1[21], data_1[22], data_1[23],
                                                          data_1[24],
                                                          data_1[25], data_1[26], data_1[27]
                                                          , data_1[28], data_1[29], data_1[30], data_1[31],
                                                          data_1[32],
                                                          data_1[33], data_1[34], data_1[35]

                                                          )
                                # print(type(dataTobytes), len(dataTobytes))

                                tcp_socket_ID5.send(dataTobytes)
                                # print(i)
                                i += 1

                                # 0xff, 0xff, 0xff, 0xff, 128, 0, 0, 1, 1, 80, 5, 120.04208246406465, 30.231343807768763, \
                                # 120.04207836129298, 30.23134029404531, 120.04207425852078, 30.231336780321374, \
                                # 120.04207015574802, 30.231333266596973, 120.0420660529747, 30.231329752872096, \
                                # 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xee, 0xee, 0xee
                            # ==========================================下传经纬度数据

                            ####-------------------  接收下位机上传数据
                            ##================================更新车辆状态数据以及检测废数据
                            elif (x5 == 68):  # 小车上发车辆状态数据
                                # print("该段字节流包长：", x5)
                                print("这是上发的车辆的状态信息")
                                # 1. 如果数据域前四个字节为0，则上传的为无效的废数据
                                # 2. 如果数据域前四个字节为1，则上传的是车辆的状态信息，分别更新GUI界面上的数据
                                # 3. 如果数据域前四个字节为2，则上传的是GPS的定位信息，提取经纬度数据用于控制算法
                                # 4. 如果数据区前四个字节为3，则上传的是图像信息，更新GUI界面上的图像数据
                                # 上传结构体数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                dataFromCar_state_from_car = tcp_socket_ID5.recv(40)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                if (x9 == 0):  # 数据域前四个字节为0x000x000x000x00,对应情况1
                                    print("这是无效的废数据")
                                else:
                                    try:
                                        x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32\
                                            = struct.unpack(
                                            'I2fIfI16B',
                                            dataFromCar_state_from_car)  # 4B4i3I2fIfI16B  解包C的结构体数据，大端格式加！（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                    except:
                                        print("解析状态数据出错")

                                    ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                    # print("接收数据转换成字符串为：", x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14,
                                    #       x15, x16,
                                    #       x17,
                                    #       x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32)

                                    ##==============================更新车辆状态数据
                                    # elif (len(dataFromCar) == 68):  # 数据域前四个字节为0x000x000x000x01,对应情况2
                                    self.serverFlag = 1  # 启动多线程服务器？

                                    ID = x8
                                    LPWM = x11  # 车辆状态
                                    RPWM = x15  # 电池电压
                                    L2v = x12  # 左轮电机转速
                                    R2V = x13  # 右轮电机转速
                                    angle = x14

                                    self.sigID_ID5.emit(str(ID))  # 往GUI界面中传入数据,注意ID传入的参数为int型要与Listener属性定义处的sigID类型一致

                                    self.sigL2v_ID5.emit(float(L2v))

                                    self.sigR2v_ID5.emit(float(R2V))

                                    self.sigangle_ID5.emit(float(angle))

                                    self.sigLPWM_ID5.emit(LPWM)

                                    self.sigRPWM_ID5.emit(RPWM)

                                    Ay = 111
                                    Yaw = 111
                                    Tn = 111
                                    Vy = 111

                                    self.sigAy_ID5.emit(Ay)
                                    self.sigYaw_ID5.emit(Yaw)
                                    self.sigTn_ID5.emit(Tn)
                                    self.sigVy_ID5.emit(Vy)



                                    # ================写入数据库
                                    conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                           autocommit=True)

                                    # 使用cursor()方法获取操作游标
                                    cursor1 = conn.cursor()

                                    # SQL语句：向数据表中插入数据
                                    # sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                    #                                              VALUES (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)"""  # 修改这一行数据，可多次插入
                                    sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                                                                values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""  # 修改这一行数据，可多次插入
                                    data_state = (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)
                                    # 异常处理
                                    try:
                                        # 执行SQL语句
                                        cursor1.execute(sql1, data_state)
                                        # 提交事务到数据库执行
                                        conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                        print("状态数据写入数据库")
                                    except:
                                        # 如果发生错误则执行回滚操作
                                        conn.rollback()

                                    # 关闭数据库连接
                                    conn.close()
                                    ##############写入数据库

                                    # self.stateButton.setCheckable(False)
                                ##==============================更新车辆状态数据
                            ##================================更新车辆状态数据以及检测废数据

                            ##================================获取车辆上传的GPS定位数据
                            elif (x5 == 64):  # 如果上传的数据为64字节，则对应车辆目前GPS获取的经纬度数据
                                Start_LngLat = time.time()  # 开始读取经纬度的时间点
                                print("这是车辆所处的经纬度")
                                # 上传数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                # 数据块：N 的十六进制为4E; P的十六进制为50；L为4C；B为42；卫星个数：01；填充数据： 00 00
                                # 经度：（120.04208246406465）40 5E 02 B1 7A A5 B9 23  纬度：（30.231343807768763）40 3E 3B 39 59 08 7F BB
                                # 120.04862759640338  \x40\x5e\x03\x1c\xb6\xec\x0f\x14  30.237128736109234  \x40\x3e\x3c\xb4\x78\x06\x87\xee
                                # 120.0457642526888  \x40\x5e\x02\xed\xcd\x30\x27\xf4  30.23500645123769  \x40\x3e\x3c\x29\x61\xfe\x6a\x37
                                dataFromCar_jingwei_from_car = tcp_socket_ID5.recv(4)  # 接收GPS等
                                try:
                                    y11, y12, y13, y14 = struct.unpack('4B', dataFromCar_jingwei_from_car)
                                except:
                                    print("解析GPS/卫星数据出错")
                                GPS = y11  # GPS协议类型
                                Star = y12  # 卫星个数
                                print("GPS:", str(GPS))
                                print("卫星个数：", int(Star))

                                dataFromCar_jingwei_from_car = tcp_socket_ID5.recv(32)
                                try:
                                    y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31, y32 \
                                        = struct.unpack(
                                        '2d16B',
                                        dataFromCar_jingwei_from_car)  # 4B4i2I4B2d16B 解包C的结构体数据,大端格式加！,h表示两个字节的short型数据（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                except:
                                    print("解析经纬度数据出错")

                                ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                # print("接收数据转换成字符串为：", y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14,
                                #       y15, y16,
                                #       y17,
                                #       y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31,y32)

                                jingdu_Car = y15  # 小车所处经度
                                weidu_Car = y16  # 小车所处纬度
                                lng = y15
                                lat = y16
                                converted = []
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))


                                #================写入数据库
                                conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                       autocommit=True)

                                # 使用cursor()方法获取操作游标
                                cursor2 = conn.cursor()

                                # SQL语句：向数据表中插入数据
                                # sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)VALUES (x6, y11,y15,y16)"""  # 修改这一行数据，可多次插入
                                # VALUES 里的数据的类型一定要与定义表时的类型一致,该方法适合传入给定数据，如果是变量则要用（"%s",%d）等格式字符
                                sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)values("%s","%s","%s","%s")"""  # 修改这一行数据，可多次插入
                                data_lnglat = (x8, y11, y15, y16)

                                # 异常处理
                                try:
                                    # 执行SQL语句
                                    cursor2.execute(sql2, data_lnglat)
                                    # 提交事务到数据库执行
                                    conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                    print("经纬度数据写入数据库")
                                except:
                                    # 如果发生错误则执行回滚操作
                                    conn.rollback()

                                # 关闭数据库连接
                                conn.close()
                                ##############写入数据库


                                converted = wgs84_to_bd09_change.gcj02_to_bd09(y15,
                                                                               y16)  # 调用外部函数将谷歌地图GPS经纬度数据转换成百度地图格式

                                fun_time_ID5(converted[0], converted[1])

                                # ti = threading.Thread(target=fun_time, args=(converted[0], converted[1])) ##传入经纬度和车辆ID，将其写入对应的json文件
                                # ti.start()

                                self.siglng_ID5.emit(float(converted[0]))
                                self.siglat_ID5.emit(float(converted[1]))
                                # time.sleep(1)

                                End_Lnglat = time.time()
                                print("执行一次经纬度数据读取用时", End_Lnglat - Start_LngLat)

                                # print("GPS:", str(GPS))
                                # print("卫星个数：", int(Star))
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))
                            ##================================获取车辆上传的GPS定位数据

                            elif (x9 == 3 ):  # 如果上传数据字节数过多，则为图像信息

                                print("上传的是图像数据")
                                # def ImageRead():
                                StartImage = time.time()  # 开始读取图片数据

                                data_image = tcp_socket_ID5.recv(1)
                                try:
                                    image_geshi = struct.unpack('B', data_image)
                                except:
                                    print("解析图像格式出错")
                                # print("图像格式为：", image_geshi)
                                data_image = tcp_socket_ID5.recv(4)
                                try:
                                    image_len = struct.unpack('1I', data_image)
                                except:
                                    print("解析图像字节数出错")
                                print("图像字节数：", image_len)

                                image_msg = b''
                                # print("帧中读取的图像数据块字节数，未转化成int型前：", image_len)
                                len1 = int(image_len[0])  # 图像数据的字节长度
                                # print("转化成int型后：", len1)
                                image_length = len1
                                readlength = 0  # 从缓冲区读取的字节数
                                while (len1 > 0):
                                    if len1 > 20000:  # 如果剩余图像字节数大于20000
                                        buffer = tcp_socket_ID5.recv(20000,
                                                                     socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                        # print("本次recv收到的字节是否为20000，", len(buffer))  # 检查每次recv是否收到完整的1024个字节
                                        image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                        len1 = len1 - 20000
                                        readlength += 20000
                                    else:
                                        buffer = tcp_socket_ID5.recv(len1, socket.MSG_WAITALL)
                                        # print("剩余不满20000的字节数为", len1, "读取的字节数为", len(buffer))  # 检查最后一次读取的字节数
                                        image_msg += buffer
                                        readlength += len1
                                        break

                                try:
                                    # 将读取到的字节流存储到图像文件中
                                    start = time.time()
                                    with open("image_file_ID5.jpg", "wb+") as img_file:
                                        img_file.write(image_msg)
                                    end = time.time()
                                    print("写入图片用时", end - start)
                                    imge = "image_file_ID5.jpg"
                                    self.sigImage.emit(imge)


                                except:
                                    print("图像数据出错")

                                # 继续检测包尾
                                left = tcp_socket_ID5.recv(1)
                                while 1:
                                    try:
                                        left_baowei = struct.unpack('B', left)
                                        # print("检测包尾读到的数据为", left_baowei)
                                    except:
                                        print("检测包尾第一个字节解析错误")

                                    # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                                    if (left_baowei == (204,)):  # 如果读到包尾则一次性读完包尾
                                        left = tcp_socket_ID5.recv(3)
                                        print("读完四个包尾")
                                        break
                                    else:
                                        left = tcp_socket_ID5.recv(1)

                                EndImage = time.time()  # 发送完图片时间
                                print("一次图片操作用时", EndImage - StartImage)

                            else:
                                    print("上传数据出错")
                            # 如果是ID为1的车发送的数据则进行接收


                while True:
                    # 创建一个线程去读取数据
                    read_thread = threading.Thread(target=read_thread_method)
                    # read_thread.setDaemon(True)  # 守护线程，read_thread作为一个守护线程，主线程结束，其立马也随之结束
                    read_thread.start()
                    # 要在线程执行完毕后在关闭套接字，不然会报错：在一个非套接字上尝试了一个操作
                    # read_thread.join()  # join 设置为主线程等待子线程结束后再继续执行主线程


                    #
                    #     askimage_thread = threading.Thread(target=askimage_method)
                    #     askimage_thread.start()
                    #     print("开启主动请求图像线程")

                    while True:

                        j = 0  # 请求状态数据时的计数
                        h = 0  # 请求图像数据时的计数

                        ###=======================上位机主动下发第一组经纬度数据
                        if (sendFlag_ID5 == 1):
                            print("下发第一组数据")
                            baotou_1 = 0xff  # char
                            baotou_2 = 0xff  # char
                            baotou_3 = 0xff  # char
                            baotou_4 = 0xff  # char
                            baochang_1 = 128  # int  包长  字节对齐会在double前面加上四个字节00000000
                            baoxuhao_1 = 1  # int  发送次数
                            shijianchuo_1 = 0  # int  上位机下发设为0
                            # zhongduanID_1 = 1  # int  终端ID
                            shujuyu_11 = 1  # int  类型1表示下发经纬度
                            shujuyu_21 = 84  # int  5个经纬度数组，一共80字节
                            dianshu_11 = 5  # I 下发5个点

                            ## 数据块之前的内容
                            data_11 = [baotou_1, baotou_2, baotou_3, baotou_4, baochang_1, baoxuhao_1, shijianchuo_1,

                                       shujuyu_11, shujuyu_21, dianshu_11]

                            #####################################--------------------------------------------数据域
                            file_path = "jingweidu.txt"  # 经纬度存储文件名

                            with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                t_sum1 = len(f.readlines())  # 总共有的经纬度组数

                                if 6 < t_sum1:  # 保证文档里经纬度数据大于五个

                                    for n in range(1, 6):
                                        line_number_1 = n  # 文件行数从1开始
                                        fread_n = linecache.getline(file_path, line_number_1).strip()  # 读取对应行数的经纬度
                                        fread_n_num = fread_n.strip("()")  # 删去字符串中左右两边的括号
                                        fread_split = fread_n_num.split(",")
                                        fread_n_jingdu = fread_split[0]  # 每行的经度str
                                        fread_n_weidu = fread_split[1]  # 每行的纬度str

                                        jingdu_1 = float(fread_n_jingdu)
                                        weidu_1 = float(fread_n_weidu)
                                        data_11.append(jingdu_1)
                                        data_11.append(weidu_1)
                                else:
                                    print("已经发送完毕所有数据")
                            f.close()

                            yuliu_1 = 0x00
                            # 循环加入12个0x00表示预留位和CRC32位
                            for s in range(0, 12):
                                data_11.append(yuliu_1)

                            baowei_1 = 0xee
                            # 循环加入四个0xee表示包尾
                            for t in range(0, 4):
                                data_11.append(baowei_1)

                            ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                            # 为小端接收模式
                            dataTobytes_1 = struct.pack('4B6i10d16B', data_11[0], data_11[1], data_11[2], data_11[3],
                                                        data_11[4], data_11[5]
                                                        , data_11[6], data_11[7], data_11[8], data_11[9], data_11[10],
                                                        data_11[11]
                                                        , data_11[12], data_11[13], data_11[14], data_11[15],
                                                        data_11[16],
                                                        data_11[17], data_11[18], data_11[19]
                                                        , data_11[20], data_11[21], data_11[22], data_11[23],
                                                        data_11[24],
                                                        data_11[25], data_11[26], data_11[27]
                                                        , data_11[28], data_11[29], data_11[30], data_11[31],
                                                        data_11[32],
                                                        data_11[33], data_11[34], data_11[35]

                                                        )
                            # print(type(dataTobytes_1), len(dataTobytes_1))

                            tcp_socket_ID5.send(dataTobytes_1)
                            sendFlag_ID5 = 0
                            ###=======================上位机主动下发第一组经纬度数据


                        if (askstateFlag_ID5 == 1):  # 如果请求状态按钮被激活则 下发请求状态指令，小车发送任意指令上位机均可以下发请求指令
                            askstate_thread_ID5 = threading.Thread(target=askstate_method_ID5)
                            askstate_thread_ID5.start()
                            print("开启主动请求状态线程")
                            print("askstateFlag_ID5:", askstateFlag_ID5)

                        if (askstateFlag_ID5 == 2):
                            print("开始请求车辆状态的数据")

                            send_state_baotou = 0xff  # 包头
                            send_state_baochang = 44  # 包长度，请求时数据域为0字节
                            send_state_xuhao = j  # 包序号
                            send_state_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_state_ID = 1  # int 固定车辆ID号
                            send_state_shujuyu_1 = 2  # int 第二类终端状态请求
                            send_state_shujuyu_2 = 0  # int 请求状态时L为0
                            send_state_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_state_yuliu = 0x00  # 保留帧暂时填充
                            send_state_baowei = 0xee  # 结束帧暂时填充

                            send_state_dataTobytes = []
                            for state_i in range(0, 4):
                                send_state_dataTobytes.append(send_state_baotou)
                            send_state_dataTobytes.append(send_state_baochang)
                            send_state_dataTobytes.append(send_state_xuhao)
                            send_state_dataTobytes.append(send_state_timechuo)
                            # send_state_dataTobytes.append(send_state_ID)
                            send_state_dataTobytes.append(send_state_shujuyu_1)
                            send_state_dataTobytes.append(send_state_shujuyu_2)
                            for state_j in range(0, 8):
                                send_state_dataTobytes.append(send_state_yuliu)

                            for state_k in range(0, 4):
                                send_state_dataTobytes.append(send_state_CRC32)

                            for state_l in range(0, 4):
                                send_state_dataTobytes.append(send_state_baowei)

                            dataTobytes_state = struct.pack('4B3i2I16B', send_state_dataTobytes[0],
                                                            send_state_dataTobytes[1], send_state_dataTobytes[2],
                                                            send_state_dataTobytes[3]
                                                            , send_state_dataTobytes[4], send_state_dataTobytes[5],
                                                            send_state_dataTobytes[6], send_state_dataTobytes[7]
                                                            , send_state_dataTobytes[8], send_state_dataTobytes[9],
                                                            send_state_dataTobytes[10], send_state_dataTobytes[11]
                                                            , send_state_dataTobytes[12], send_state_dataTobytes[13],
                                                            send_state_dataTobytes[14], send_state_dataTobytes[15]
                                                            , send_state_dataTobytes[16], send_state_dataTobytes[17],
                                                            send_state_dataTobytes[18], send_state_dataTobytes[19]
                                                            , send_state_dataTobytes[20], send_state_dataTobytes[21],
                                                            send_state_dataTobytes[22], send_state_dataTobytes[23]
                                                            , send_state_dataTobytes[24])

                            tcp_socket_ID5.send(dataTobytes_state)
                            askstateFlag_ID5 = 0  # 发送完后重新把标志位置零
                            j += 1
                        ####======================上位机向下位机发送请求状态数据的请求

                        ##==========================上位机向下位机请求图像数据
                        if (askimageFlag_ID5 == 1):  # 请求图像按钮被按下时激活，向下发送请求图像指令，小车发送任意数据上位机均可以下发请求指令
                            askimage_thread_ID5 = threading.Thread(target=askimage_method_ID5)
                            askimage_thread_ID5.start()
                            print("开启主动请求图像线程")
                            print("askimageFlag_ID5:", askimageFlag_ID5)

                        if (askimageFlag_ID5 == 2):
                            print("开始请求图像的数据")
                            send_image_baotou = 0xff  # 包头
                            send_image_baochang = 44  # 包长度，请求时数据域为0字节
                            send_image_xuhao = h  # 包序号
                            send_image_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_image_ID = 1  # int 固定车辆ID号
                            send_image_shujuyu_1 = 3  # int 第三类终端状态请求
                            send_image_shujuyu_2 = 0  # int 请求图像时L为0
                            send_image_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_image_yuliu = 0x00  # 保留帧暂时填充
                            send_image_baowei = 0xee  # 结束帧暂时填充

                            send_image_dataTobytes = []
                            for image_i in range(0, 4):
                                send_image_dataTobytes.append(send_image_baotou)
                            send_image_dataTobytes.append(send_image_baochang)
                            send_image_dataTobytes.append(send_image_xuhao)
                            send_image_dataTobytes.append(send_image_timechuo)
                            # send_image_dataTobytes.append(send_image_ID)
                            send_image_dataTobytes.append(send_image_shujuyu_1)
                            send_image_dataTobytes.append(send_image_shujuyu_2)
                            for image_j in range(0, 8):
                                send_image_dataTobytes.append(send_image_yuliu)

                            for state_k in range(0, 4):
                                send_image_dataTobytes.append(send_image_CRC32)

                            for state_l in range(0, 4):
                                send_image_dataTobytes.append(send_image_baowei)

                            dataTobytes_image = struct.pack('4B3i2I16B', send_image_dataTobytes[0],
                                                            send_image_dataTobytes[1], send_image_dataTobytes[2],
                                                            send_image_dataTobytes[3]
                                                            , send_image_dataTobytes[4], send_image_dataTobytes[5],
                                                            send_image_dataTobytes[6], send_image_dataTobytes[7]
                                                            , send_image_dataTobytes[8], send_image_dataTobytes[9],
                                                            send_image_dataTobytes[10], send_image_dataTobytes[11]
                                                            , send_image_dataTobytes[12], send_image_dataTobytes[13],
                                                            send_image_dataTobytes[14], send_image_dataTobytes[15]
                                                            , send_image_dataTobytes[16], send_image_dataTobytes[17],
                                                            send_image_dataTobytes[18], send_image_dataTobytes[19]
                                                            , send_image_dataTobytes[20], send_image_dataTobytes[21],
                                                            send_image_dataTobytes[22], send_image_dataTobytes[23]
                                                            , send_image_dataTobytes[24])

                            # client.send(dataTobytes_image)  # 发送请求的信号的数据格式
                            tcp_socket_ID5.send(dataTobytes_image)
                            askimageFlag_ID5 = 0  # 发送后标志位重新置零
                            h += 1
                        ##==========================上位机向下位机请求图像数据

                    # 清理socket，同样道理，这里需要锁定和解锁
                    # socket_lock.acquire()
                    # read_thread.join()
                    tcp_socket_ID5.close()
                    tcp_socket_ID5 = None
                    # socket_lock.release()
                    # break

    def upSend(self, flag):
        pass

# 第六辆车的监听线程
class Listener_ID6(QThread):  # 创建子线程类
    listenFlag = 1
    connectFlag = 1
    sigID_ID6 = pyqtSignal(str)  # run方法中用来将上位机的数据传送到GUI界面上
    sigState_ID6 = pyqtSignal(str)
    sigL2v_ID6 = pyqtSignal(float)
    sigR2v_ID6 = pyqtSignal(float)
    sigU_ID6 = pyqtSignal(float)
    sigangle_ID6 = pyqtSignal(float)
    sigImage_ID6 = pyqtSignal(str)

    sigAy_ID6 = pyqtSignal(float)
    sigYaw_ID6 = pyqtSignal(float)
    sigTn_ID6 = pyqtSignal(float)
    sigVy_ID6 = pyqtSignal(float)


    sigLPWM_ID6 = pyqtSignal(float)
    sigRPWM_ID6 = pyqtSignal(float)

    siglat_ID6 = pyqtSignal(float)
    siglng_ID6 = pyqtSignal(float)



    def __init__(self, ip, port, serverIP, serverPort, length, weight, maxV,
                 minV, maxA, maxD):
        super(Listener_ID6, self).__init__()  # 继承父类的属性和方法

        self.L2vArr = []
        self.R2vArr = []
        self.dataFromCarDecode = ''
        self.serverFlag = 0
        self.flag = 1



    def run(self):
        global sendFlag_ID6  # 因为sendFlag是在方法外定义的变量，所以要在方法内使用的话加上global成为全局变量
        global startFlag
        global askstateFlag_ID6
        global askimageFlag_ID6
        global frame
        global askstate_imageFlag_ID6



        sendFlag_ID6 = 0
        startFlag = 0
        askstateFlag_ID6 = 0
        askimageFlag_ID6 = 0
        askstate_imageFlag_ID6 = 0

        def askimage_method_ID6():
            global askimageFlag_ID6
            while True:
                askimageFlag_ID6 = 2
                time.sleep(10)  # 每隔10秒主动请求一次图像数据

        def askstate_method_ID6():
            global askstateFlag_ID6
            while True:
                askstateFlag_ID6 = 2
                time.sleep(5)  # 每隔5秒主动请求一次状态数据

        # ===================================接收上传经纬度数据并写入json文件
        # i=0
        def fun_time_ID6(lng_ID1, lat_ID2):  # 将上传的经纬度数据写入json文件中供BD_map.html文件读取
            # global i
            with open("weather6.json", "w", encoding='utf-8') as f:  # 打开对应车辆的json文件写入数据

                dicts = {"lng": lng_ID1, "lat": lat_ID2}
                f.write(json.dumps(dicts, indent=4))  # Indent表示隔开四个单位
                # i = i + 2
                # if i > 2000:
                #     i = 0

        # ===================================接收上传经纬度数据并写入json文件

        while True:

            while (self.listenFlag):
                print("连接云端服务器")

                tcp_socket_ID6 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # STREAM表示TCP传输
                tcp_socket_ID6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

                # 2.链接服务器
                # server_ip = input("请输入服务器ip地址：")
                # server_port = input("请输入服务器端口:")
                # tcp_socket.connect((str(server_ip), server_port))
                # tcp_socket.connect(("10.80.7.157", 8080))
                tcp_socket_ID6.connect(("47.102.36.187", 8092))   # 链接云端服务器

                # 创建线程锁，防止主线程socket被close了，子线程还在recv而引发的异常
                # socket_lock = threading.Lock()
                def read_thread_method():  # 读取数据的方法
                    print("接收线程开启")

                    while True:
                        if not tcp_socket_ID6:  # 如果socket关闭，退出
                            break
                        dataFromCar = tcp_socket_ID6.recv(1)  # 缓冲区大小，接收文件的个数

                        i = 1  # 下发经纬度数据时的计数,前五个数已经主动下发

                        if not dataFromCar:
                            print("小车停止上传数据")
                        else:
                            while True:
                                print("逐个读取字节")
                                try:
                                    z1 = struct.unpack('B', dataFromCar)
                                except:
                                    print("第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包头
                                if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                                    dataFromCar = tcp_socket_ID6.recv(3)
                                    break
                                else:
                                    dataFromCar = tcp_socket_ID6.recv(1)
                            # print("dataFromCar的长度", len(dataFromCar))
                            try:
                                x2, x3, x4 = struct.unpack('3B', dataFromCar)  # 包头
                            except:
                                print("包头解析错误")

                            dataFromCar = tcp_socket_ID6.recv(24)
                            try:
                                x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar)
                            except:
                                print("前24个字节解析错误")
                            ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2
                            # print("该段字节流包长", x5)  # 查看包长是否正确

                            # 如果是ID为1的车发送的数据则进行接收
                            # if (x8 == 6):
                            if (x5 == 44):  # 如果上发的是44字节的数据（请求下发经纬度时设下位机发送数据块为空）
                                # 发送数据示例 dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18  00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                print(" 请求下发经纬度数据")
                                dataFromCar_jingwei_to_car = tcp_socket_ID6.recv(16)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                # print("读取余下的字节为：", dataFromCar_jingwei_to_car)
                                baotou1 = 0xff  # char
                                baotou2 = 0xff  # char
                                baotou3 = 0xff  # char
                                baotou4 = 0xff  # char
                                baochang = 128  # int  i包长 字节对齐会在double前面加上四个字节00000000
                                baoxuhao = i  # int  i发送次数
                                shijianchuo = 0  # int  i上位机下发设为0
                                # zhongduanID = 1  # int  i终端ID
                                shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
                                shujuyu_2 = 84  # int  I 5个经纬度数组，一共80字节
                                dianshu = 5  # Uint32 I 下发5个点

                                ## 数据块之前的内容
                                data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,

                                          shujuyu_1, shujuyu_2, dianshu]

                                #####################################--------------------------------------------数据域
                                file_path = "jingweidu.txt"  # 经纬度存储文件名

                                with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                    t_sum = len(f.readlines())  # 总共有的经纬度组数

                                    # print("ccccccc文档的总行数为：", t_sum)
                                    if 5 * i + 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
                                        for j in range(5 * i + 1, 5 * i + 6):
                                            line_number = j  # 文件行数从1开始，而i初始值为0
                                            fread_j = linecache.getline(file_path,
                                                                        line_number).strip()  # 读取对应行数的经纬度
                                            fread_j_num = fread_j.strip("()")  # 删去字符串中左右两边的括号
                                            fread_split = fread_j_num.split(",")
                                            fread_j_jingdu = fread_split[0]  # 每行的经度str
                                            fread_j_weidu = fread_split[1]  # 每行的纬度str
                                            print(type(fread_j_jingdu))
                                            print(fread_j_jingdu)

                                            jingdu = float(fread_j_jingdu)
                                            weidu = float(fread_j_weidu)
                                            data_1.append(jingdu)
                                            data_1.append(weidu)
                                    else:
                                        print("已经发送完毕所有数据")
                                f.close()
                                # 加入数据块后的数据包
                                # print("data_1", data_1)

                                yuliu = 0x00
                                # 循环加入12个0x00表示预留位和CRC32位
                                for n in range(0, 12):
                                    data_1.append(yuliu)

                                baowei = 0xee
                                # 循环加入四个0xee表示包尾
                                for m in range(0, 4):
                                    data_1.append(baowei)
                                    # print(data_1)

                                # 显示完整数据包
                                # print(data_1)

                                ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                                # 为大端接收模式
                                dataTobytes = struct.pack('4B3i3I10d16B', data_1[0], data_1[1], data_1[2], data_1[3],
                                                          data_1[4],
                                                          data_1[5]
                                                          , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10],
                                                          data_1[11]
                                                          , data_1[12], data_1[13], data_1[14], data_1[15],
                                                          data_1[16],
                                                          data_1[17], data_1[18], data_1[19]
                                                          , data_1[20], data_1[21], data_1[22], data_1[23],
                                                          data_1[24],
                                                          data_1[25], data_1[26], data_1[27]
                                                          , data_1[28], data_1[29], data_1[30], data_1[31],
                                                          data_1[32],
                                                          data_1[33], data_1[34], data_1[35]

                                                          )
                                # print(type(dataTobytes), len(dataTobytes))

                                tcp_socket_ID6.send(dataTobytes)
                                # print(i)
                                i += 1

                                # 0xff, 0xff, 0xff, 0xff, 128, 0, 0, 1, 1, 80, 5, 120.04208246406465, 30.231343807768763, \
                                # 120.04207836129298, 30.23134029404531, 120.04207425852078, 30.231336780321374, \
                                # 120.04207015574802, 30.231333266596973, 120.0420660529747, 30.231329752872096, \
                                # 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xee, 0xee, 0xee
                            # ==========================================下传经纬度数据

                            ####-------------------  接收下位机上传数据
                            ##================================更新车辆状态数据以及检测废数据
                            elif (x5 == 68):  # 小车上发车辆状态数据
                                # print("该段字节流包长：", x5)
                                print("这是上发的车辆的状态信息")
                                # 1. 如果数据域前四个字节为0，则上传的为无效的废数据
                                # 2. 如果数据域前四个字节为1，则上传的是车辆的状态信息，分别更新GUI界面上的数据
                                # 3. 如果数据域前四个字节为2，则上传的是GPS的定位信息，提取经纬度数据用于控制算法
                                # 4. 如果数据区前四个字节为3，则上传的是图像信息，更新GUI界面上的图像数据
                                # 上传结构体数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                dataFromCar_state_from_car = tcp_socket_ID6.recv(40)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                if (x9 == 0):  # 数据域前四个字节为0x000x000x000x00,对应情况1
                                    print("这是无效的废数据")
                                else:
                                    try:
                                        x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32 \
                                            = struct.unpack(
                                            'I2fIfI16B',
                                            dataFromCar_state_from_car)  # 4B4i3I2fIfI16B  解包C的结构体数据，大端格式加！（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                    except:
                                        print("解析状态数据出错")

                                    ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                    # print("接收数据转换成字符串为：", x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14,
                                    #       x15, x16,
                                    #       x17,
                                    #       x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32)

                                    ##==============================更新车辆状态数据
                                    # elif (len(dataFromCar) == 68):  # 数据域前四个字节为0x000x000x000x01,对应情况2
                                    self.serverFlag = 1  # 启动多线程服务器？

                                    ID = x8
                                    LPWM = x11  # 车辆状态
                                    RPWM = x15  # 电池电压
                                    L2v = x12  # 左轮电机转速
                                    R2V = x13  # 右轮电机转速
                                    angle = x14

                                    self.sigID_ID6.emit(str(ID))  # 往GUI界面中传入数据,注意ID传入的参数为int型要与Listener属性定义处的sigID类型一致

                                    self.sigL2v_ID6.emit(float(L2v))

                                    self.sigR2v_ID6.emit(float(R2V))

                                    self.sigangle_ID6.emit(float(angle))

                                    self.sigLPWM_ID6.emit(LPWM)

                                    self.sigRPWM_ID6.emit(RPWM)

                                    Ay = 111
                                    Yaw = 111
                                    Tn = 111
                                    Vy = 111

                                    self.sigAy_ID6.emit(Ay)
                                    self.sigYaw_ID6.emit(Yaw)
                                    self.sigTn_ID6.emit(Tn)
                                    self.sigVy_ID6.emit(Vy)



                                    # ================写入数据库
                                    conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                           autocommit=True)

                                    # 使用cursor()方法获取操作游标
                                    cursor1 = conn.cursor()

                                    # SQL语句：向数据表中插入数据
                                    # sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                    #                                              VALUES (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)"""  # 修改这一行数据，可多次插入
                                    sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                                                                values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""  # 修改这一行数据，可多次插入
                                    data_state = (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)
                                    # 异常处理
                                    try:
                                        # 执行SQL语句
                                        cursor1.execute(sql1, data_state)
                                        # 提交事务到数据库执行
                                        conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                        print("状态数据写入数据库")
                                    except:
                                        # 如果发生错误则执行回滚操作
                                        conn.rollback()

                                    # 关闭数据库连接
                                    conn.close()
                                    ##############写入数据库

                                    # self.stateButton.setCheckable(False)
                                ##==============================更新车辆状态数据
                            ##================================更新车辆状态数据以及检测废数据

                            ##================================获取车辆上传的GPS定位数据
                            elif (x5 == 64):  # 如果上传的数据为64字节，则对应车辆目前GPS获取的经纬度数据
                                Start_LngLat = time.time()  # 开始读取经纬度的时间点
                                print("这是车辆所处的经纬度")
                                # 上传数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                # 数据块：N 的十六进制为4E; P的十六进制为50；L为4C；B为42；卫星个数：01；填充数据： 00 00
                                # 经度：（120.04208246406465）40 5E 02 B1 7A A5 B9 23  纬度：（30.231343807768763）40 3E 3B 39 59 08 7F BB
                                # 120.04862759640338  \x40\x5e\x03\x1c\xb6\xec\x0f\x14  30.237128736109234  \x40\x3e\x3c\xb4\x78\x06\x87\xee
                                # 120.0457642526888  \x40\x5e\x02\xed\xcd\x30\x27\xf4  30.23500645123769  \x40\x3e\x3c\x29\x61\xfe\x6a\x37
                                dataFromCar_jingwei_from_car = tcp_socket_ID6.recv(4)  # 接收GPS等
                                try:
                                    y11, y12, y13, y14 = struct.unpack('4B', dataFromCar_jingwei_from_car)
                                except:
                                    print("解析GPS/卫星数据出错")
                                GPS = y11  # GPS协议类型
                                Star = y12  # 卫星个数
                                print("GPS:", str(GPS))
                                print("卫星个数：", int(Star))

                                dataFromCar_jingwei_from_car = tcp_socket_ID6.recv(32)
                                try:
                                    y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31, y32 \
                                        = struct.unpack(
                                        '2d16B',
                                        dataFromCar_jingwei_from_car)  # 4B4i2I4B2d16B 解包C的结构体数据,大端格式加！,h表示两个字节的short型数据（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                except:
                                    print("解析经纬度数据出错")

                                ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                # print("接收数据转换成字符串为：", y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14,
                                #       y15, y16,
                                #       y17,
                                #       y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31,y32)

                                jingdu_Car = y15  # 小车所处经度
                                weidu_Car = y16  # 小车所处纬度
                                lng = y15
                                lat = y16
                                converted = []
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))


                                #================写入数据库
                                conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                       autocommit=True)

                                # 使用cursor()方法获取操作游标
                                cursor2 = conn.cursor()

                                # SQL语句：向数据表中插入数据
                                # sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)VALUES (x6, y11,y15,y16)"""  # 修改这一行数据，可多次插入
                                # VALUES 里的数据的类型一定要与定义表时的类型一致,该方法适合传入给定数据，如果是变量则要用（"%s",%d）等格式字符
                                sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)values("%s","%s","%s","%s")"""  # 修改这一行数据，可多次插入
                                data_lnglat = (x8, y11, y15, y16)

                                # 异常处理
                                try:
                                    # 执行SQL语句
                                    cursor2.execute(sql2, data_lnglat)
                                    # 提交事务到数据库执行
                                    conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                    print("经纬度数据写入数据库")
                                except:
                                    # 如果发生错误则执行回滚操作
                                    conn.rollback()

                                # 关闭数据库连接
                                conn.close()
                                ##############写入数据库


                                converted = wgs84_to_bd09_change.gcj02_to_bd09(y15,
                                                                               y16)  # 调用外部函数将谷歌地图GPS经纬度数据转换成百度地图格式

                                fun_time_ID6(converted[0], converted[1])

                                # ti = threading.Thread(target=fun_time, args=(converted[0], converted[1])) ##传入经纬度和车辆ID，将其写入对应的json文件
                                # ti.start()

                                self.siglng_ID6.emit(float(converted[0]))
                                self.siglat_ID6.emit(float(converted[1]))
                                # time.sleep(1)

                                End_Lnglat = time.time()
                                print("执行一次经纬度数据读取用时", End_Lnglat - Start_LngLat)

                                # print("GPS:", str(GPS))
                                # print("卫星个数：", int(Star))
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))
                            ##================================获取车辆上传的GPS定位数据

                            elif (x9 == 3 ):  # 如果上传数据字节数过多，则为图像信息

                                print("上传的是图像数据")
                                # def ImageRead():
                                StartImage = time.time()  # 开始读取图片数据

                                data_image = tcp_socket_ID6.recv(1)
                                try:
                                    image_geshi = struct.unpack('B', data_image)
                                except:
                                    print("解析图像格式出错")
                                # print("图像格式为：", image_geshi)
                                data_image = tcp_socket_ID6.recv(4)
                                try:
                                    image_len = struct.unpack('1I', data_image)
                                except:
                                    print("解析图像字节数出错")
                                print("图像字节数：", image_len)

                                image_msg = b''
                                # print("帧中读取的图像数据块字节数，未转化成int型前：", image_len)
                                len1 = int(image_len[0])  # 图像数据的字节长度
                                # print("转化成int型后：", len1)
                                image_length = len1
                                readlength = 0  # 从缓冲区读取的字节数
                                while (len1 > 0):
                                    if len1 > 20000:  # 如果剩余图像字节数大于20000
                                        buffer = tcp_socket_ID6.recv(20000,
                                                                     socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                        # print("本次recv收到的字节是否为20000，", len(buffer))  # 检查每次recv是否收到完整的1024个字节
                                        image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                        len1 = len1 - 20000
                                        readlength += 20000
                                    else:
                                        buffer = tcp_socket_ID6.recv(len1, socket.MSG_WAITALL)
                                        # print("剩余不满20000的字节数为", len1, "读取的字节数为", len(buffer))  # 检查最后一次读取的字节数
                                        image_msg += buffer
                                        readlength += len1
                                        break

                                try:
                                    # 将读取到的字节流存储到图像文件中
                                    start = time.time()
                                    with open("image_file_ID6.jpg", "wb+") as img_file:
                                        img_file.write(image_msg)
                                    end = time.time()
                                    print("写入图片用时", end - start)
                                    imge = "image_file_ID6.jpg"
                                    self.sigImage.emit(imge)


                                except:
                                    print("图像数据出错")

                                # 继续检测包尾
                                left = tcp_socket_ID6.recv(1)
                                while 1:
                                    try:
                                        left_baowei = struct.unpack('B', left)
                                        # print("检测包尾读到的数据为", left_baowei)
                                    except:
                                        print("检测包尾第一个字节解析错误")

                                    # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                                    if (left_baowei == (204,)):  # 如果读到包尾则一次性读完包尾
                                        left = tcp_socket_ID6.recv(3)
                                        print("读完四个包尾")
                                        break
                                    else:
                                        left = tcp_socket_ID6.recv(1)

                                EndImage = time.time()  # 发送完图片时间
                                print("一次图片操作用时", EndImage - StartImage)
                            else:
                                    print("上传数据出错")
                            # 如果是ID为1的车发送的数据则进行接收


                while True:
                    # 创建一个线程去读取数据
                    read_thread = threading.Thread(target=read_thread_method)
                    # read_thread.setDaemon(True)  # 守护线程，read_thread作为一个守护线程，主线程结束，其立马也随之结束
                    read_thread.start()
                    # 要在线程执行完毕后在关闭套接字，不然会报错：在一个非套接字上尝试了一个操作
                    # read_thread.join()  # join 设置为主线程等待子线程结束后再继续执行主线程


                    #
                    #     askimage_thread = threading.Thread(target=askimage_method)
                    #     askimage_thread.start()
                    #     print("开启主动请求图像线程")

                    while True:

                        j = 0  # 请求状态数据时的计数
                        h = 0  # 请求图像数据时的计数

                        ###=======================上位机主动下发第一组经纬度数据
                        if (sendFlag_ID6 == 1):
                            print("下发第一组数据")
                            baotou_1 = 0xff  # char
                            baotou_2 = 0xff  # char
                            baotou_3 = 0xff  # char
                            baotou_4 = 0xff  # char
                            baochang_1 = 128  # int  包长  字节对齐会在double前面加上四个字节00000000
                            baoxuhao_1 = 1  # int  发送次数
                            shijianchuo_1 = 0  # int  上位机下发设为0
                            # zhongduanID_1 = 1  # int  终端ID
                            shujuyu_11 = 1  # int  类型1表示下发经纬度
                            shujuyu_21 = 84  # int  5个经纬度数组，一共80字节
                            dianshu_11 = 5  # I 下发5个点

                            ## 数据块之前的内容
                            data_11 = [baotou_1, baotou_2, baotou_3, baotou_4, baochang_1, baoxuhao_1, shijianchuo_1,

                                       shujuyu_11, shujuyu_21, dianshu_11]

                            #####################################--------------------------------------------数据域
                            file_path = "jingweidu.txt"  # 经纬度存储文件名

                            with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                t_sum1 = len(f.readlines())  # 总共有的经纬度组数

                                if 6 < t_sum1:  # 保证文档里经纬度数据大于五个

                                    for n in range(1, 6):
                                        line_number_1 = n  # 文件行数从1开始
                                        fread_n = linecache.getline(file_path, line_number_1).strip()  # 读取对应行数的经纬度
                                        fread_n_num = fread_n.strip("()")  # 删去字符串中左右两边的括号
                                        fread_split = fread_n_num.split(",")
                                        fread_n_jingdu = fread_split[0]  # 每行的经度str
                                        fread_n_weidu = fread_split[1]  # 每行的纬度str

                                        jingdu_1 = float(fread_n_jingdu)
                                        weidu_1 = float(fread_n_weidu)
                                        data_11.append(jingdu_1)
                                        data_11.append(weidu_1)
                                else:
                                    print("已经发送完毕所有数据")
                            f.close()

                            yuliu_1 = 0x00
                            # 循环加入12个0x00表示预留位和CRC32位
                            for s in range(0, 12):
                                data_11.append(yuliu_1)

                            baowei_1 = 0xee
                            # 循环加入四个0xee表示包尾
                            for t in range(0, 4):
                                data_11.append(baowei_1)

                            ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                            # 为小端接收模式
                            dataTobytes_1 = struct.pack('4B6i10d16B', data_11[0], data_11[1], data_11[2], data_11[3],
                                                        data_11[4], data_11[5]
                                                        , data_11[6], data_11[7], data_11[8], data_11[9], data_11[10],
                                                        data_11[11]
                                                        , data_11[12], data_11[13], data_11[14], data_11[15],
                                                        data_11[16],
                                                        data_11[17], data_11[18], data_11[19]
                                                        , data_11[20], data_11[21], data_11[22], data_11[23],
                                                        data_11[24],
                                                        data_11[25], data_11[26], data_11[27]
                                                        , data_11[28], data_11[29], data_11[30], data_11[31],
                                                        data_11[32],
                                                        data_11[33], data_11[34], data_11[35]

                                                        )
                            # print(type(dataTobytes_1), len(dataTobytes_1))

                            tcp_socket_ID6.send(dataTobytes_1)
                            sendFlag_ID6 = 0
                            ###=======================上位机主动下发第一组经纬度数据


                        if (askstateFlag_ID6 == 1):  # 如果请求状态按钮被激活则 下发请求状态指令，小车发送任意指令上位机均可以下发请求指令
                            askstate_thread_ID6 = threading.Thread(target=askstate_method_ID6)
                            askstate_thread_ID6.start()
                            print("开启主动请求状态线程")
                            print("askstateFlag_ID6:", askstateFlag_ID6)

                        if (askstateFlag_ID6 == 2):
                            print("开始请求车辆状态的数据")

                            send_state_baotou = 0xff  # 包头
                            send_state_baochang = 44  # 包长度，请求时数据域为0字节
                            send_state_xuhao = j  # 包序号
                            send_state_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_state_ID = 1  # int 固定车辆ID号
                            send_state_shujuyu_1 = 2  # int 第二类终端状态请求
                            send_state_shujuyu_2 = 0  # int 请求状态时L为0
                            send_state_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_state_yuliu = 0x00  # 保留帧暂时填充
                            send_state_baowei = 0xee  # 结束帧暂时填充

                            send_state_dataTobytes = []
                            for state_i in range(0, 4):
                                send_state_dataTobytes.append(send_state_baotou)
                            send_state_dataTobytes.append(send_state_baochang)
                            send_state_dataTobytes.append(send_state_xuhao)
                            send_state_dataTobytes.append(send_state_timechuo)
                            # send_state_dataTobytes.append(send_state_ID)
                            send_state_dataTobytes.append(send_state_shujuyu_1)
                            send_state_dataTobytes.append(send_state_shujuyu_2)
                            for state_j in range(0, 8):
                                send_state_dataTobytes.append(send_state_yuliu)

                            for state_k in range(0, 4):
                                send_state_dataTobytes.append(send_state_CRC32)

                            for state_l in range(0, 4):
                                send_state_dataTobytes.append(send_state_baowei)

                            dataTobytes_state = struct.pack('4B3i2I16B', send_state_dataTobytes[0],
                                                            send_state_dataTobytes[1], send_state_dataTobytes[2],
                                                            send_state_dataTobytes[3]
                                                            , send_state_dataTobytes[4], send_state_dataTobytes[5],
                                                            send_state_dataTobytes[6], send_state_dataTobytes[7]
                                                            , send_state_dataTobytes[8], send_state_dataTobytes[9],
                                                            send_state_dataTobytes[10], send_state_dataTobytes[11]
                                                            , send_state_dataTobytes[12], send_state_dataTobytes[13],
                                                            send_state_dataTobytes[14], send_state_dataTobytes[15]
                                                            , send_state_dataTobytes[16], send_state_dataTobytes[17],
                                                            send_state_dataTobytes[18], send_state_dataTobytes[19]
                                                            , send_state_dataTobytes[20], send_state_dataTobytes[21],
                                                            send_state_dataTobytes[22], send_state_dataTobytes[23]
                                                            , send_state_dataTobytes[24])

                            tcp_socket_ID6.send(dataTobytes_state)
                            askstateFlag_ID6 = 0  # 发送完后重新把标志位置零
                            j += 1
                        ####======================上位机向下位机发送请求状态数据的请求

                        ##==========================上位机向下位机请求图像数据
                        if (askimageFlag_ID6 == 1):  # 请求图像按钮被按下时激活，向下发送请求图像指令，小车发送任意数据上位机均可以下发请求指令
                            askimage_thread_ID6 = threading.Thread(target=askimage_method_ID6)
                            askimage_thread_ID6.start()
                            print("开启主动请求图像线程")
                            print("askimageFlag_ID6:", askimageFlag_ID6)

                        if (askimageFlag_ID6 == 2):
                            print("开始请求图像的数据")
                            send_image_baotou = 0xff  # 包头
                            send_image_baochang = 44  # 包长度，请求时数据域为0字节
                            send_image_xuhao = h  # 包序号
                            send_image_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_image_ID = 1  # int 固定车辆ID号
                            send_image_shujuyu_1 = 3  # int 第三类终端状态请求
                            send_image_shujuyu_2 = 0  # int 请求图像时L为0
                            send_image_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_image_yuliu = 0x00  # 保留帧暂时填充
                            send_image_baowei = 0xee  # 结束帧暂时填充

                            send_image_dataTobytes = []
                            for image_i in range(0, 4):
                                send_image_dataTobytes.append(send_image_baotou)
                            send_image_dataTobytes.append(send_image_baochang)
                            send_image_dataTobytes.append(send_image_xuhao)
                            send_image_dataTobytes.append(send_image_timechuo)
                            # send_image_dataTobytes.append(send_image_ID)
                            send_image_dataTobytes.append(send_image_shujuyu_1)
                            send_image_dataTobytes.append(send_image_shujuyu_2)
                            for image_j in range(0, 8):
                                send_image_dataTobytes.append(send_image_yuliu)

                            for state_k in range(0, 4):
                                send_image_dataTobytes.append(send_image_CRC32)

                            for state_l in range(0, 4):
                                send_image_dataTobytes.append(send_image_baowei)

                            dataTobytes_image = struct.pack('4B3i2I16B', send_image_dataTobytes[0],
                                                            send_image_dataTobytes[1], send_image_dataTobytes[2],
                                                            send_image_dataTobytes[3]
                                                            , send_image_dataTobytes[4], send_image_dataTobytes[5],
                                                            send_image_dataTobytes[6], send_image_dataTobytes[7]
                                                            , send_image_dataTobytes[8], send_image_dataTobytes[9],
                                                            send_image_dataTobytes[10], send_image_dataTobytes[11]
                                                            , send_image_dataTobytes[12], send_image_dataTobytes[13],
                                                            send_image_dataTobytes[14], send_image_dataTobytes[15]
                                                            , send_image_dataTobytes[16], send_image_dataTobytes[17],
                                                            send_image_dataTobytes[18], send_image_dataTobytes[19]
                                                            , send_image_dataTobytes[20], send_image_dataTobytes[21],
                                                            send_image_dataTobytes[22], send_image_dataTobytes[23]
                                                            , send_image_dataTobytes[24])

                            # client.send(dataTobytes_image)  # 发送请求的信号的数据格式
                            tcp_socket_ID6.send(dataTobytes_image)
                            askimageFlag_ID6 = 0  # 发送后标志位重新置零
                            h += 1
                        ##==========================上位机向下位机请求图像数据

                    # 清理socket，同样道理，这里需要锁定和解锁
                    # socket_lock.acquire()
                    # read_thread.join()
                    tcp_socket_ID6.close()
                    tcp_socket_ID6 = None
                    # socket_lock.release()
                    # break

    def upSend(self, flag):
        pass

# 第七辆车的监听线程
class Listener_ID7(QThread):  # 创建子线程类
    listenFlag = 1
    connectFlag = 1
    sigID_ID7 = pyqtSignal(str)  # run方法中用来将上位机的数据传送到GUI界面上
    sigState_ID7 = pyqtSignal(str)
    sigL2v_ID7 = pyqtSignal(float)
    sigR2v_ID7 = pyqtSignal(float)
    sigU_ID7 = pyqtSignal(float)
    sigangle_ID7 = pyqtSignal(float)
    sigImage_ID7 = pyqtSignal(str)

    sigAy_ID7 = pyqtSignal(float)
    sigYaw_ID7 = pyqtSignal(float)
    sigTn_ID7 = pyqtSignal(float)
    sigVy_ID7 = pyqtSignal(float)


    sigLPWM_ID7 = pyqtSignal(float)
    sigRPWM_ID7 = pyqtSignal(float)

    siglat_ID7 = pyqtSignal(float)
    siglng_ID7 = pyqtSignal(float)



    def __init__(self, ip, port, serverIP, serverPort, length, weight, maxV,
                 minV, maxA, maxD):
        super(Listener_ID7, self).__init__()  # 继承父类的属性和方法

        self.L2vArr = []
        self.R2vArr = []
        self.dataFromCarDecode = ''
        self.serverFlag = 0
        self.flag = 1



    def run(self):
        global sendFlag_ID7  # 因为sendFlag是在方法外定义的变量，所以要在方法内使用的话加上global成为全局变量
        global startFlag
        global askstateFlag_ID7
        global askimageFlag_ID7
        global frame
        global askstate_imageFlag_ID7



        sendFlag_ID7 = 0
        startFlag = 0
        askstateFlag_ID7 = 0
        askimageFlag_ID7 = 0
        askstate_imageFlag_ID7 = 0

        def askimage_method_ID7():
            global askimageFlag_ID7
            while True:
                askimageFlag_ID7 = 2
                time.sleep(10)  # 每隔10秒主动请求一次图像数据

        def askstate_method_ID7():
            global askstateFlag_ID7
            while True:
                askstateFlag_ID7 = 2
                time.sleep(5)  # 每隔5秒主动请求一次状态数据

        # ===================================接收上传经纬度数据并写入json文件
        # i=0
        def fun_time_ID7(lng_ID1, lat_ID2):  # 将上传的经纬度数据写入json文件中供BD_map.html文件读取
            # global i
            with open("weather7.json", "w", encoding='utf-8') as f:  # 打开对应车辆的json文件写入数据

                dicts = {"lng": lng_ID1, "lat": lat_ID2}
                f.write(json.dumps(dicts, indent=4))  # Indent表示隔开四个单位
                # i = i + 2
                # if i > 2000:
                #     i = 0

        # ===================================接收上传经纬度数据并写入json文件

        while True:

            while (self.listenFlag):
                print("连接云端服务器")

                tcp_socket_ID7 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # STREAM表示TCP传输
                tcp_socket_ID7.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

                # 2.链接服务器
                # server_ip = input("请输入服务器ip地址：")
                # server_port = input("请输入服务器端口:")
                # tcp_socket.connect((str(server_ip), server_port))
                # tcp_socket.connect(("10.80.7.157", 8080))
                tcp_socket_ID7.connect(("47.102.36.187", 8094))   # 链接云端服务器

                # 创建线程锁，防止主线程socket被close了，子线程还在recv而引发的异常
                # socket_lock = threading.Lock()
                def read_thread_method():  # 读取数据的方法
                    print("接收线程开启")

                    while True:
                        if not tcp_socket_ID7:  # 如果socket关闭，退出
                            break
                        dataFromCar = tcp_socket_ID7.recv(1)  # 缓冲区大小，接收文件的个数

                        i = 1  # 下发经纬度数据时的计数,前五个数已经主动下发

                        if not dataFromCar:
                            print("小车停止上传数据")
                        else:
                            while True:
                                print("逐个读取字节")
                                try:
                                    z1 = struct.unpack('B', dataFromCar)
                                except:
                                    print("第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包头
                                if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                                    dataFromCar = tcp_socket_ID7.recv(3)
                                    break
                                else:
                                    dataFromCar = tcp_socket_ID7.recv(1)
                            # print("dataFromCar的长度", len(dataFromCar))
                            try:
                                x2, x3, x4 = struct.unpack('3B', dataFromCar)  # 包头
                            except:
                                print("包头解析错误")

                            dataFromCar = tcp_socket_ID7.recv(24)
                            try:
                                x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar)
                            except:
                                print("前24个字节解析错误")
                            ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2
                            # print("该段字节流包长", x5)  # 查看包长是否正确

                            # 如果是ID为1的车发送的数据则进行接收
                            # if (x8 == 7):
                            if (x5 == 44):  # 如果上发的是44字节的数据（请求下发经纬度时设下位机发送数据块为空）
                                # 发送数据示例 dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18  00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                print(" 请求下发经纬度数据")
                                dataFromCar_jingwei_to_car = tcp_socket_ID7.recv(16)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                # print("读取余下的字节为：", dataFromCar_jingwei_to_car)
                                baotou1 = 0xff  # char
                                baotou2 = 0xff  # char
                                baotou3 = 0xff  # char
                                baotou4 = 0xff  # char
                                baochang = 128  # int  i包长 字节对齐会在double前面加上四个字节00000000
                                baoxuhao = i  # int  i发送次数
                                shijianchuo = 0  # int  i上位机下发设为0
                                # zhongduanID = 1  # int  i终端ID
                                shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
                                shujuyu_2 = 84  # int  I 5个经纬度数组，一共80字节
                                dianshu = 5  # Uint32 I 下发5个点

                                ## 数据块之前的内容
                                data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,

                                          shujuyu_1, shujuyu_2, dianshu]

                                #####################################--------------------------------------------数据域
                                file_path = "jingweidu.txt"  # 经纬度存储文件名

                                with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                    t_sum = len(f.readlines())  # 总共有的经纬度组数

                                    # print("ccccccc文档的总行数为：", t_sum)
                                    if 5 * i + 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
                                        for j in range(5 * i + 1, 5 * i + 6):
                                            line_number = j  # 文件行数从1开始，而i初始值为0
                                            fread_j = linecache.getline(file_path,
                                                                        line_number).strip()  # 读取对应行数的经纬度
                                            fread_j_num = fread_j.strip("()")  # 删去字符串中左右两边的括号
                                            fread_split = fread_j_num.split(",")
                                            fread_j_jingdu = fread_split[0]  # 每行的经度str
                                            fread_j_weidu = fread_split[1]  # 每行的纬度str
                                            print(type(fread_j_jingdu))
                                            print(fread_j_jingdu)

                                            jingdu = float(fread_j_jingdu)
                                            weidu = float(fread_j_weidu)
                                            data_1.append(jingdu)
                                            data_1.append(weidu)
                                    else:
                                        print("已经发送完毕所有数据")
                                f.close()
                                # 加入数据块后的数据包
                                # print("data_1", data_1)

                                yuliu = 0x00
                                # 循环加入12个0x00表示预留位和CRC32位
                                for n in range(0, 12):
                                    data_1.append(yuliu)

                                baowei = 0xee
                                # 循环加入四个0xee表示包尾
                                for m in range(0, 4):
                                    data_1.append(baowei)
                                    # print(data_1)

                                # 显示完整数据包
                                # print(data_1)

                                ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                                # 为大端接收模式
                                dataTobytes = struct.pack('4B3i3I10d16B', data_1[0], data_1[1], data_1[2], data_1[3],
                                                          data_1[4],
                                                          data_1[5]
                                                          , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10],
                                                          data_1[11]
                                                          , data_1[12], data_1[13], data_1[14], data_1[15],
                                                          data_1[16],
                                                          data_1[17], data_1[18], data_1[19]
                                                          , data_1[20], data_1[21], data_1[22], data_1[23],
                                                          data_1[24],
                                                          data_1[25], data_1[26], data_1[27]
                                                          , data_1[28], data_1[29], data_1[30], data_1[31],
                                                          data_1[32],
                                                          data_1[33], data_1[34], data_1[35]

                                                          )
                                # print(type(dataTobytes), len(dataTobytes))

                                tcp_socket_ID7.send(dataTobytes)
                                # print(i)
                                i += 1

                                # 0xff, 0xff, 0xff, 0xff, 128, 0, 0, 1, 1, 80, 5, 120.04208246406465, 30.231343807768763, \
                                # 120.04207836129298, 30.23134029404531, 120.04207425852078, 30.231336780321374, \
                                # 120.04207015574802, 30.231333266596973, 120.0420660529747, 30.231329752872096, \
                                # 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xee, 0xee, 0xee
                            # ==========================================下传经纬度数据

                            ####-------------------  接收下位机上传数据
                            ##================================更新车辆状态数据以及检测废数据
                            elif (x5 == 68):  # 小车上发车辆状态数据
                                # print("该段字节流包长：", x5)
                                print("这是上发的车辆的状态信息")
                                # 1. 如果数据域前四个字节为0，则上传的为无效的废数据
                                # 2. 如果数据域前四个字节为1，则上传的是车辆的状态信息，分别更新GUI界面上的数据
                                # 3. 如果数据域前四个字节为2，则上传的是GPS的定位信息，提取经纬度数据用于控制算法
                                # 4. 如果数据区前四个字节为3，则上传的是图像信息，更新GUI界面上的图像数据
                                # 上传结构体数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                dataFromCar_state_from_car = tcp_socket_ID7.recv(40)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                if (x9 == 0):  # 数据域前四个字节为0x000x000x000x00,对应情况1
                                    print("这是无效的废数据")
                                else:
                                    try:
                                        x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32 \
                                            = struct.unpack(
                                            'I2fIfI16B',
                                            dataFromCar_state_from_car)  # 4B4i3I2fIfI16B  解包C的结构体数据，大端格式加！（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                    except:
                                        print("解析状态数据出错")

                                    ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                    # print("接收数据转换成字符串为：", x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14,
                                    #       x15, x16,
                                    #       x17,
                                    #       x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32)

                                    ##==============================更新车辆状态数据
                                    # elif (len(dataFromCar) == 68):  # 数据域前四个字节为0x000x000x000x01,对应情况2
                                    self.serverFlag = 1  # 启动多线程服务器？

                                    ID = x8
                                    LPWM = x11  # 车辆状态
                                    RPWM = x15  # 电池电压
                                    L2v = x12  # 左轮电机转速
                                    R2V = x13  # 右轮电机转速
                                    angle = x14

                                    self.sigID_ID7.emit(str(ID))  # 往GUI界面中传入数据,注意ID传入的参数为int型要与Listener属性定义处的sigID类型一致

                                    self.sigL2v_ID7.emit(float(L2v))

                                    self.sigR2v_ID7.emit(float(R2V))

                                    self.sigangle_ID7.emit(float(angle))

                                    self.sigLPWM_ID7.emit(LPWM)

                                    self.sigRPWM_ID7.emit(RPWM)

                                    Ay = 111
                                    Yaw = 111
                                    Tn = 111
                                    Vy = 111

                                    self.sigAy_ID7.emit(Ay)
                                    self.sigYaw_ID7.emit(Yaw)
                                    self.sigTn_ID7.emit(Tn)
                                    self.sigVy_ID7.emit(Vy)



                                    # ================写入数据库
                                    conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                           autocommit=True)

                                    # 使用cursor()方法获取操作游标
                                    cursor1 = conn.cursor()

                                    # SQL语句：向数据表中插入数据
                                    # sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                    #                                              VALUES (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)"""  # 修改这一行数据，可多次插入
                                    sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                                                                values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""  # 修改这一行数据，可多次插入
                                    data_state = (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)
                                    # 异常处理
                                    try:
                                        # 执行SQL语句
                                        cursor1.execute(sql1, data_state)
                                        # 提交事务到数据库执行
                                        conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                        print("状态数据写入数据库")
                                    except:
                                        # 如果发生错误则执行回滚操作
                                        conn.rollback()

                                    # 关闭数据库连接
                                    conn.close()
                                    ##############写入数据库

                                    # self.stateButton.setCheckable(False)
                                ##==============================更新车辆状态数据
                            ##================================更新车辆状态数据以及检测废数据

                            ##================================获取车辆上传的GPS定位数据
                            elif (x5 == 64):  # 如果上传的数据为64字节，则对应车辆目前GPS获取的经纬度数据
                                Start_LngLat = time.time()  # 开始读取经纬度的时间点
                                print("这是车辆所处的经纬度")
                                # 上传数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                # 数据块：N 的十六进制为4E; P的十六进制为50；L为4C；B为42；卫星个数：01；填充数据： 00 00
                                # 经度：（120.04208246406465）40 5E 02 B1 7A A5 B9 23  纬度：（30.231343807768763）40 3E 3B 39 59 08 7F BB
                                # 120.04862759640338  \x40\x5e\x03\x1c\xb6\xec\x0f\x14  30.237128736109234  \x40\x3e\x3c\xb4\x78\x06\x87\xee
                                # 120.0457642526888  \x40\x5e\x02\xed\xcd\x30\x27\xf4  30.23500645123769  \x40\x3e\x3c\x29\x61\xfe\x6a\x37
                                dataFromCar_jingwei_from_car = tcp_socket_ID7.recv(4)  # 接收GPS等
                                try:
                                    y11, y12, y13, y14 = struct.unpack('4B', dataFromCar_jingwei_from_car)
                                except:
                                    print("解析GPS/卫星数据出错")
                                GPS = y11  # GPS协议类型
                                Star = y12  # 卫星个数
                                print("GPS:", str(GPS))
                                print("卫星个数：", int(Star))

                                dataFromCar_jingwei_from_car = tcp_socket_ID7.recv(32)
                                try:
                                    y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31, y32 \
                                        = struct.unpack(
                                        '2d16B',
                                        dataFromCar_jingwei_from_car)  # 4B4i2I4B2d16B 解包C的结构体数据,大端格式加！,h表示两个字节的short型数据（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                except:
                                    print("解析经纬度数据出错")

                                ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                # print("接收数据转换成字符串为：", y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14,
                                #       y15, y16,
                                #       y17,
                                #       y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31,y32)

                                jingdu_Car = y15  # 小车所处经度
                                weidu_Car = y16  # 小车所处纬度
                                lng = y15
                                lat = y16
                                converted = []
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))


                                #================写入数据库
                                conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                       autocommit=True)

                                # 使用cursor()方法获取操作游标
                                cursor2 = conn.cursor()

                                # SQL语句：向数据表中插入数据
                                # sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)VALUES (x6, y11,y15,y16)"""  # 修改这一行数据，可多次插入
                                # VALUES 里的数据的类型一定要与定义表时的类型一致,该方法适合传入给定数据，如果是变量则要用（"%s",%d）等格式字符
                                sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)values("%s","%s","%s","%s")"""  # 修改这一行数据，可多次插入
                                data_lnglat = (x8, y11, y15, y16)

                                # 异常处理
                                try:
                                    # 执行SQL语句
                                    cursor2.execute(sql2, data_lnglat)
                                    # 提交事务到数据库执行
                                    conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                    print("经纬度数据写入数据库")
                                except:
                                    # 如果发生错误则执行回滚操作
                                    conn.rollback()

                                # 关闭数据库连接
                                conn.close()
                                ##############写入数据库


                                converted = wgs84_to_bd09_change.gcj02_to_bd09(y15,
                                                                               y16)  # 调用外部函数将谷歌地图GPS经纬度数据转换成百度地图格式

                                fun_time_ID7(converted[0], converted[1])

                                # ti = threading.Thread(target=fun_time, args=(converted[0], converted[1])) ##传入经纬度和车辆ID，将其写入对应的json文件
                                # ti.start()

                                self.siglng_ID7.emit(float(converted[0]))
                                self.siglat_ID7.emit(float(converted[1]))
                                # time.sleep(1)

                                End_Lnglat = time.time()
                                print("执行一次经纬度数据读取用时", End_Lnglat - Start_LngLat)

                                # print("GPS:", str(GPS))
                                # print("卫星个数：", int(Star))
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))
                            ##================================获取车辆上传的GPS定位数据

                            elif (x9 == 3 ):  # 如果上传数据字节数过多，则为图像信息

                                print("上传的是图像数据")
                                # def ImageRead():
                                StartImage = time.time()  # 开始读取图片数据

                                data_image = tcp_socket_ID7.recv(1)
                                try:
                                    image_geshi = struct.unpack('B', data_image)
                                except:
                                    print("解析图像格式出错")
                                # print("图像格式为：", image_geshi)
                                data_image = tcp_socket_ID7.recv(4)
                                try:
                                    image_len = struct.unpack('1I', data_image)
                                except:
                                    print("解析图像字节数出错")
                                print("图像字节数：", image_len)

                                image_msg = b''
                                # print("帧中读取的图像数据块字节数，未转化成int型前：", image_len)
                                len1 = int(image_len[0])  # 图像数据的字节长度
                                # print("转化成int型后：", len1)
                                image_length = len1
                                readlength = 0  # 从缓冲区读取的字节数
                                while (len1 > 0):
                                    if len1 > 20000:  # 如果剩余图像字节数大于20000
                                        buffer = tcp_socket_ID7.recv(20000,
                                                                     socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                        # print("本次recv收到的字节是否为20000，", len(buffer))  # 检查每次recv是否收到完整的1024个字节
                                        image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                        len1 = len1 - 20000
                                        readlength += 20000
                                    else:
                                        buffer = tcp_socket_ID7.recv(len1, socket.MSG_WAITALL)
                                        # print("剩余不满20000的字节数为", len1, "读取的字节数为", len(buffer))  # 检查最后一次读取的字节数
                                        image_msg += buffer
                                        readlength += len1
                                        break

                                try:
                                    # 将读取到的字节流存储到图像文件中
                                    start = time.time()
                                    with open("image_file_ID7.jpg", "wb+") as img_file:
                                        img_file.write(image_msg)
                                    end = time.time()
                                    print("写入图片用时", end - start)
                                    imge = "image_file_ID7.jpg"
                                    self.sigImage.emit(imge)


                                except:
                                    print("图像数据出错")

                                # 继续检测包尾
                                left = tcp_socket_ID7.recv(1)
                                while 1:
                                    try:
                                        left_baowei = struct.unpack('B', left)
                                        # print("检测包尾读到的数据为", left_baowei)
                                    except:
                                        print("检测包尾第一个字节解析错误")

                                    # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                                    if (left_baowei == (204,)):  # 如果读到包尾则一次性读完包尾
                                        left = tcp_socket_ID7.recv(3)
                                        print("读完四个包尾")
                                        break
                                    else:
                                        left = tcp_socket_ID7.recv(1)

                                EndImage = time.time()  # 发送完图片时间
                                print("一次图片操作用时", EndImage - StartImage)
                            else:
                                    print("上传数据出错")
                            # 如果是ID为1的车发送的数据则进行接收


                while True:
                    # 创建一个线程去读取数据
                    read_thread = threading.Thread(target=read_thread_method)
                    # read_thread.setDaemon(True)  # 守护线程，read_thread作为一个守护线程，主线程结束，其立马也随之结束
                    read_thread.start()
                    # 要在线程执行完毕后在关闭套接字，不然会报错：在一个非套接字上尝试了一个操作
                    # read_thread.join()  # join 设置为主线程等待子线程结束后再继续执行主线程


                    #
                    #     askimage_thread = threading.Thread(target=askimage_method)
                    #     askimage_thread.start()
                    #     print("开启主动请求图像线程")

                    while True:

                        j = 0  # 请求状态数据时的计数
                        h = 0  # 请求图像数据时的计数

                        ###=======================上位机主动下发第一组经纬度数据
                        if (sendFlag_ID7 == 1):
                            print("下发第一组数据")
                            baotou_1 = 0xff  # char
                            baotou_2 = 0xff  # char
                            baotou_3 = 0xff  # char
                            baotou_4 = 0xff  # char
                            baochang_1 = 128  # int  包长  字节对齐会在double前面加上四个字节00000000
                            baoxuhao_1 = 1  # int  发送次数
                            shijianchuo_1 = 0  # int  上位机下发设为0
                            # zhongduanID_1 = 1  # int  终端ID
                            shujuyu_11 = 1  # int  类型1表示下发经纬度
                            shujuyu_21 = 84  # int  5个经纬度数组，一共80字节
                            dianshu_11 = 5  # I 下发5个点

                            ## 数据块之前的内容
                            data_11 = [baotou_1, baotou_2, baotou_3, baotou_4, baochang_1, baoxuhao_1, shijianchuo_1,

                                       shujuyu_11, shujuyu_21, dianshu_11]

                            #####################################--------------------------------------------数据域
                            file_path = "jingweidu.txt"  # 经纬度存储文件名

                            with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                t_sum1 = len(f.readlines())  # 总共有的经纬度组数

                                if 6 < t_sum1:  # 保证文档里经纬度数据大于五个

                                    for n in range(1, 6):
                                        line_number_1 = n  # 文件行数从1开始
                                        fread_n = linecache.getline(file_path, line_number_1).strip()  # 读取对应行数的经纬度
                                        fread_n_num = fread_n.strip("()")  # 删去字符串中左右两边的括号
                                        fread_split = fread_n_num.split(",")
                                        fread_n_jingdu = fread_split[0]  # 每行的经度str
                                        fread_n_weidu = fread_split[1]  # 每行的纬度str

                                        jingdu_1 = float(fread_n_jingdu)
                                        weidu_1 = float(fread_n_weidu)
                                        data_11.append(jingdu_1)
                                        data_11.append(weidu_1)
                                else:
                                    print("已经发送完毕所有数据")
                            f.close()

                            yuliu_1 = 0x00
                            # 循环加入12个0x00表示预留位和CRC32位
                            for s in range(0, 12):
                                data_11.append(yuliu_1)

                            baowei_1 = 0xee
                            # 循环加入四个0xee表示包尾
                            for t in range(0, 4):
                                data_11.append(baowei_1)

                            ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                            # 为小端接收模式
                            dataTobytes_1 = struct.pack('4B6i10d16B', data_11[0], data_11[1], data_11[2], data_11[3],
                                                        data_11[4], data_11[5]
                                                        , data_11[6], data_11[7], data_11[8], data_11[9], data_11[10],
                                                        data_11[11]
                                                        , data_11[12], data_11[13], data_11[14], data_11[15],
                                                        data_11[16],
                                                        data_11[17], data_11[18], data_11[19]
                                                        , data_11[20], data_11[21], data_11[22], data_11[23],
                                                        data_11[24],
                                                        data_11[25], data_11[26], data_11[27]
                                                        , data_11[28], data_11[29], data_11[30], data_11[31],
                                                        data_11[32],
                                                        data_11[33], data_11[34], data_11[35]

                                                        )
                            # print(type(dataTobytes_1), len(dataTobytes_1))

                            tcp_socket_ID7.send(dataTobytes_1)
                            sendFlag_ID7 = 0
                            ###=======================上位机主动下发第一组经纬度数据


                        if (askstateFlag_ID7 == 1):  # 如果请求状态按钮被激活则 下发请求状态指令，小车发送任意指令上位机均可以下发请求指令
                            askstate_thread_ID7 = threading.Thread(target=askstate_method_ID7)
                            askstate_thread_ID7.start()
                            print("开启主动请求状态线程")
                            print("askstateFlag_ID7:", askstateFlag_ID7)

                        if (askstateFlag_ID7 == 2):
                            print("开始请求车辆状态的数据")

                            send_state_baotou = 0xff  # 包头
                            send_state_baochang = 44  # 包长度，请求时数据域为0字节
                            send_state_xuhao = j  # 包序号
                            send_state_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_state_ID = 1  # int 固定车辆ID号
                            send_state_shujuyu_1 = 2  # int 第二类终端状态请求
                            send_state_shujuyu_2 = 0  # int 请求状态时L为0
                            send_state_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_state_yuliu = 0x00  # 保留帧暂时填充
                            send_state_baowei = 0xee  # 结束帧暂时填充

                            send_state_dataTobytes = []
                            for state_i in range(0, 4):
                                send_state_dataTobytes.append(send_state_baotou)
                            send_state_dataTobytes.append(send_state_baochang)
                            send_state_dataTobytes.append(send_state_xuhao)
                            send_state_dataTobytes.append(send_state_timechuo)
                            # send_state_dataTobytes.append(send_state_ID)
                            send_state_dataTobytes.append(send_state_shujuyu_1)
                            send_state_dataTobytes.append(send_state_shujuyu_2)
                            for state_j in range(0, 8):
                                send_state_dataTobytes.append(send_state_yuliu)

                            for state_k in range(0, 4):
                                send_state_dataTobytes.append(send_state_CRC32)

                            for state_l in range(0, 4):
                                send_state_dataTobytes.append(send_state_baowei)

                            dataTobytes_state = struct.pack('4B3i2I16B', send_state_dataTobytes[0],
                                                            send_state_dataTobytes[1], send_state_dataTobytes[2],
                                                            send_state_dataTobytes[3]
                                                            , send_state_dataTobytes[4], send_state_dataTobytes[5],
                                                            send_state_dataTobytes[6], send_state_dataTobytes[7]
                                                            , send_state_dataTobytes[8], send_state_dataTobytes[9],
                                                            send_state_dataTobytes[10], send_state_dataTobytes[11]
                                                            , send_state_dataTobytes[12], send_state_dataTobytes[13],
                                                            send_state_dataTobytes[14], send_state_dataTobytes[15]
                                                            , send_state_dataTobytes[16], send_state_dataTobytes[17],
                                                            send_state_dataTobytes[18], send_state_dataTobytes[19]
                                                            , send_state_dataTobytes[20], send_state_dataTobytes[21],
                                                            send_state_dataTobytes[22], send_state_dataTobytes[23]
                                                            , send_state_dataTobytes[24])

                            tcp_socket_ID7.send(dataTobytes_state)
                            askstateFlag_ID7 = 0  # 发送完后重新把标志位置零
                            j += 1
                        ####======================上位机向下位机发送请求状态数据的请求

                        ##==========================上位机向下位机请求图像数据
                        if (askimageFlag_ID7 == 1):  # 请求图像按钮被按下时激活，向下发送请求图像指令，小车发送任意数据上位机均可以下发请求指令
                            askimage_thread_ID7 = threading.Thread(target=askimage_method_ID7)
                            askimage_thread_ID7.start()
                            print("开启主动请求图像线程")
                            print("askimageFlag_ID7:", askimageFlag_ID7)

                        if (askimageFlag_ID7 == 2):
                            print("开始请求图像的数据")
                            send_image_baotou = 0xff  # 包头
                            send_image_baochang = 44  # 包长度，请求时数据域为0字节
                            send_image_xuhao = h  # 包序号
                            send_image_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_image_ID = 1  # int 固定车辆ID号
                            send_image_shujuyu_1 = 3  # int 第三类终端状态请求
                            send_image_shujuyu_2 = 0  # int 请求图像时L为0
                            send_image_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_image_yuliu = 0x00  # 保留帧暂时填充
                            send_image_baowei = 0xee  # 结束帧暂时填充

                            send_image_dataTobytes = []
                            for image_i in range(0, 4):
                                send_image_dataTobytes.append(send_image_baotou)
                            send_image_dataTobytes.append(send_image_baochang)
                            send_image_dataTobytes.append(send_image_xuhao)
                            send_image_dataTobytes.append(send_image_timechuo)
                            # send_image_dataTobytes.append(send_image_ID)
                            send_image_dataTobytes.append(send_image_shujuyu_1)
                            send_image_dataTobytes.append(send_image_shujuyu_2)
                            for image_j in range(0, 8):
                                send_image_dataTobytes.append(send_image_yuliu)

                            for state_k in range(0, 4):
                                send_image_dataTobytes.append(send_image_CRC32)

                            for state_l in range(0, 4):
                                send_image_dataTobytes.append(send_image_baowei)

                            dataTobytes_image = struct.pack('4B3i2I16B', send_image_dataTobytes[0],
                                                            send_image_dataTobytes[1], send_image_dataTobytes[2],
                                                            send_image_dataTobytes[3]
                                                            , send_image_dataTobytes[4], send_image_dataTobytes[5],
                                                            send_image_dataTobytes[6], send_image_dataTobytes[7]
                                                            , send_image_dataTobytes[8], send_image_dataTobytes[9],
                                                            send_image_dataTobytes[10], send_image_dataTobytes[11]
                                                            , send_image_dataTobytes[12], send_image_dataTobytes[13],
                                                            send_image_dataTobytes[14], send_image_dataTobytes[15]
                                                            , send_image_dataTobytes[16], send_image_dataTobytes[17],
                                                            send_image_dataTobytes[18], send_image_dataTobytes[19]
                                                            , send_image_dataTobytes[20], send_image_dataTobytes[21],
                                                            send_image_dataTobytes[22], send_image_dataTobytes[23]
                                                            , send_image_dataTobytes[24])

                            # client.send(dataTobytes_image)  # 发送请求的信号的数据格式
                            tcp_socket_ID7.send(dataTobytes_image)
                            askimageFlag_ID7 = 0  # 发送后标志位重新置零
                            h += 1
                        ##==========================上位机向下位机请求图像数据

                    # 清理socket，同样道理，这里需要锁定和解锁
                    # socket_lock.acquire()
                    # read_thread.join()
                    tcp_socket_ID7.close()
                    tcp_socket_ID7 = None
                    # socket_lock.release()
                    # break

    def upSend(self, flag):
        pass

# 第八辆车的监听线程
class Listener_ID8(QThread):  # 创建子线程类
    listenFlag = 1
    connectFlag = 1
    sigID_ID8 = pyqtSignal(str)  # run方法中用来将上位机的数据传送到GUI界面上
    sigState_ID8 = pyqtSignal(str)
    sigL2v_ID8 = pyqtSignal(float)
    sigR2v_ID8 = pyqtSignal(float)
    sigU_ID8 = pyqtSignal(float)
    sigangle_ID8 = pyqtSignal(float)
    sigImage_ID8 = pyqtSignal(str)

    sigAy_ID8 = pyqtSignal(float)
    sigYaw_ID8 = pyqtSignal(float)
    sigTn_ID8 = pyqtSignal(float)
    sigVy_ID8 = pyqtSignal(float)


    sigLPWM_ID8 = pyqtSignal(float)
    sigRPWM_ID8 = pyqtSignal(float)

    siglat_ID8 = pyqtSignal(float)
    siglng_ID8 = pyqtSignal(float)



    def __init__(self, ip, port, serverIP, serverPort, length, weight, maxV,
                 minV, maxA, maxD):
        super(Listener_ID8, self).__init__()  # 继承父类的属性和方法

        self.L2vArr = []
        self.R2vArr = []
        self.dataFromCarDecode = ''
        self.serverFlag = 0
        self.flag = 1



    def run(self):
        global sendFlag_ID8  # 因为sendFlag是在方法外定义的变量，所以要在方法内使用的话加上global成为全局变量
        global startFlag
        global askstateFlag_ID8
        global askimageFlag_ID8
        global frame
        global askstate_imageFlag_ID8



        sendFlag_ID8 = 0
        startFlag = 0
        askstateFlag_ID8 = 0
        askimageFlag_ID8 = 0
        askstate_imageFlag_ID8 = 0

        def askimage_method_ID8():
            global askimageFlag_ID8
            while True:
                askimageFlag_ID8 = 2
                time.sleep(10)  # 每隔10秒主动请求一次图像数据

        def askstate_method_ID8():
            global askstateFlag_ID8
            while True:
                askstateFlag_ID8 = 2
                time.sleep(5)  # 每隔5秒主动请求一次状态数据

        # ===================================接收上传经纬度数据并写入json文件
        # i=0
        def fun_time_ID8(lng_ID1, lat_ID2):  # 将上传的经纬度数据写入json文件中供BD_map.html文件读取
            # global i
            with open("weather8.json", "w", encoding='utf-8') as f:  # 打开对应车辆的json文件写入数据

                dicts = {"lng": lng_ID1, "lat": lat_ID2}
                f.write(json.dumps(dicts, indent=4))  # Indent表示隔开四个单位
                # i = i + 2
                # if i > 2000:
                #     i = 0

        # ===================================接收上传经纬度数据并写入json文件

        while True:

            while (self.listenFlag):
                print("连接云端服务器")

                tcp_socket_ID8 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # STREAM表示TCP传输
                tcp_socket_ID8.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

                # 2.链接服务器
                # server_ip = input("请输入服务器ip地址：")
                # server_port = input("请输入服务器端口:")
                # tcp_socket.connect((str(server_ip), server_port))
                # tcp_socket.connect(("10.80.7.157", 8080))
                tcp_socket_ID8.connect(("47.102.36.187", 8096))   # 链接云端服务器

                # 创建线程锁，防止主线程socket被close了，子线程还在recv而引发的异常
                # socket_lock = threading.Lock()
                def read_thread_method():  # 读取数据的方法
                    print("接收线程开启")

                    while True:
                        if not tcp_socket_ID8:  # 如果socket关闭，退出
                            break
                        dataFromCar = tcp_socket_ID8.recv(1)  # 缓冲区大小，接收文件的个数

                        i = 1  # 下发经纬度数据时的计数,前五个数已经主动下发

                        if not dataFromCar:
                            print("小车停止上传数据")
                        else:
                            while True:
                                print("逐个读取字节")
                                try:
                                    z1 = struct.unpack('B', dataFromCar)
                                except:
                                    print("第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包头
                                if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                                    dataFromCar = tcp_socket_ID8.recv(3)
                                    break
                                else:
                                    dataFromCar = tcp_socket_ID8.recv(1)
                            # print("dataFromCar的长度", len(dataFromCar))
                            try:
                                x2, x3, x4 = struct.unpack('3B', dataFromCar)  # 包头
                            except:
                                print("包头解析错误")

                            dataFromCar = tcp_socket_ID8.recv(24)
                            try:
                                x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar)
                            except:
                                print("前24个字节解析错误")
                            ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2
                            # print("该段字节流包长", x5)  # 查看包长是否正确

                            # 如果是ID为1的车发送的数据则进行接收
                            # if (x8 == 8):
                            if (x5 == 44):  # 如果上发的是44字节的数据（请求下发经纬度时设下位机发送数据块为空）
                                # 发送数据示例 dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18  00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                print(" 请求下发经纬度数据")
                                dataFromCar_jingwei_to_car = tcp_socket_ID8.recv(16)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                # print("读取余下的字节为：", dataFromCar_jingwei_to_car)
                                baotou1 = 0xff  # char
                                baotou2 = 0xff  # char
                                baotou3 = 0xff  # char
                                baotou4 = 0xff  # char
                                baochang = 128  # int  i包长 字节对齐会在double前面加上四个字节00000000
                                baoxuhao = i  # int  i发送次数
                                shijianchuo = 0  # int  i上位机下发设为0
                                # zhongduanID = 1  # int  i终端ID
                                shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
                                shujuyu_2 = 84  # int  I 5个经纬度数组，一共80字节
                                dianshu = 5  # Uint32 I 下发5个点

                                ## 数据块之前的内容
                                data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,

                                          shujuyu_1, shujuyu_2, dianshu]

                                #####################################--------------------------------------------数据域
                                file_path = "jingweidu.txt"  # 经纬度存储文件名

                                with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                    t_sum = len(f.readlines())  # 总共有的经纬度组数

                                    # print("ccccccc文档的总行数为：", t_sum)
                                    if 5 * i + 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
                                        for j in range(5 * i + 1, 5 * i + 6):
                                            line_number = j  # 文件行数从1开始，而i初始值为0
                                            fread_j = linecache.getline(file_path,
                                                                        line_number).strip()  # 读取对应行数的经纬度
                                            fread_j_num = fread_j.strip("()")  # 删去字符串中左右两边的括号
                                            fread_split = fread_j_num.split(",")
                                            fread_j_jingdu = fread_split[0]  # 每行的经度str
                                            fread_j_weidu = fread_split[1]  # 每行的纬度str
                                            print(type(fread_j_jingdu))
                                            print(fread_j_jingdu)

                                            jingdu = float(fread_j_jingdu)
                                            weidu = float(fread_j_weidu)
                                            data_1.append(jingdu)
                                            data_1.append(weidu)
                                    else:
                                        print("已经发送完毕所有数据")
                                f.close()
                                # 加入数据块后的数据包
                                # print("data_1", data_1)

                                yuliu = 0x00
                                # 循环加入12个0x00表示预留位和CRC32位
                                for n in range(0, 12):
                                    data_1.append(yuliu)

                                baowei = 0xee
                                # 循环加入四个0xee表示包尾
                                for m in range(0, 4):
                                    data_1.append(baowei)
                                    # print(data_1)

                                # 显示完整数据包
                                # print(data_1)

                                ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                                # 为大端接收模式
                                dataTobytes = struct.pack('4B3i3I10d16B', data_1[0], data_1[1], data_1[2], data_1[3],
                                                          data_1[4],
                                                          data_1[5]
                                                          , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10],
                                                          data_1[11]
                                                          , data_1[12], data_1[13], data_1[14], data_1[15],
                                                          data_1[16],
                                                          data_1[17], data_1[18], data_1[19]
                                                          , data_1[20], data_1[21], data_1[22], data_1[23],
                                                          data_1[24],
                                                          data_1[25], data_1[26], data_1[27]
                                                          , data_1[28], data_1[29], data_1[30], data_1[31],
                                                          data_1[32],
                                                          data_1[33], data_1[34], data_1[35]

                                                          )
                                # print(type(dataTobytes), len(dataTobytes))

                                tcp_socket_ID8.send(dataTobytes)
                                # print(i)
                                i += 1

                                # 0xff, 0xff, 0xff, 0xff, 128, 0, 0, 1, 1, 80, 5, 120.04208246406465, 30.231343807768763, \
                                # 120.04207836129298, 30.23134029404531, 120.04207425852078, 30.231336780321374, \
                                # 120.04207015574802, 30.231333266596973, 120.0420660529747, 30.231329752872096, \
                                # 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xee, 0xee, 0xee
                            # ==========================================下传经纬度数据

                            ####-------------------  接收下位机上传数据
                            ##================================更新车辆状态数据以及检测废数据
                            elif (x5 == 68):  # 小车上发车辆状态数据
                                # print("该段字节流包长：", x5)
                                print("这是上发的车辆的状态信息")
                                # 1. 如果数据域前四个字节为0，则上传的为无效的废数据
                                # 2. 如果数据域前四个字节为1，则上传的是车辆的状态信息，分别更新GUI界面上的数据
                                # 3. 如果数据域前四个字节为2，则上传的是GPS的定位信息，提取经纬度数据用于控制算法
                                # 4. 如果数据区前四个字节为3，则上传的是图像信息，更新GUI界面上的图像数据
                                # 上传结构体数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                dataFromCar_state_from_car = tcp_socket_ID8.recv(40)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                if (x9 == 0):  # 数据域前四个字节为0x000x000x000x00,对应情况1
                                    print("这是无效的废数据")
                                else:
                                    try:
                                        x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32 \
                                            = struct.unpack(
                                            'I2fIfI16B',
                                            dataFromCar_state_from_car)  # 4B4i3I2fIfI16B  解包C的结构体数据，大端格式加！（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                    except:
                                        print("解析状态数据出错")

                                    ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                    # print("接收数据转换成字符串为：", x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14,
                                    #       x15, x16,
                                    #       x17,
                                    #       x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32)

                                    ##==============================更新车辆状态数据
                                    # elif (len(dataFromCar) == 68):  # 数据域前四个字节为0x000x000x000x01,对应情况2
                                    self.serverFlag = 1  # 启动多线程服务器？

                                    ID = x8
                                    LPWM = x11  # 车辆状态
                                    RPWM = x15  # 电池电压
                                    L2v = x12  # 左轮电机转速
                                    R2V = x13  # 右轮电机转速
                                    angle = x14

                                    self.sigID_ID8.emit(str(ID))  # 往GUI界面中传入数据,注意ID传入的参数为int型要与Listener属性定义处的sigID类型一致

                                    self.sigL2v_ID8.emit(float(L2v))

                                    self.sigR2v_ID8.emit(float(R2V))

                                    self.sigangle_ID8.emit(float(angle))

                                    self.sigLPWM_ID8.emit(LPWM)

                                    self.sigRPWM_ID8.emit(RPWM)

                                    Ay = 111
                                    Yaw = 111
                                    Tn = 111
                                    Vy = 111

                                    self.sigAy_ID8.emit(Ay)
                                    self.sigYaw_ID8.emit(Yaw)
                                    self.sigTn_ID8.emit(Tn)
                                    self.sigVy_ID8.emit(Vy)



                                    # ================写入数据库
                                    conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                           autocommit=True)

                                    # 使用cursor()方法获取操作游标
                                    cursor1 = conn.cursor()

                                    # SQL语句：向数据表中插入数据
                                    # sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                    #                                              VALUES (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)"""  # 修改这一行数据，可多次插入
                                    sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                                                                values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""  # 修改这一行数据，可多次插入
                                    data_state = (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)
                                    # 异常处理
                                    try:
                                        # 执行SQL语句
                                        cursor1.execute(sql1, data_state)
                                        # 提交事务到数据库执行
                                        conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                        print("状态数据写入数据库")
                                    except:
                                        # 如果发生错误则执行回滚操作
                                        conn.rollback()

                                    # 关闭数据库连接
                                    conn.close()
                                    ##############写入数据库

                                    # self.stateButton.setCheckable(False)
                                ##==============================更新车辆状态数据
                            ##================================更新车辆状态数据以及检测废数据

                            ##================================获取车辆上传的GPS定位数据
                            elif (x5 == 64):  # 如果上传的数据为64字节，则对应车辆目前GPS获取的经纬度数据
                                Start_LngLat = time.time()  # 开始读取经纬度的时间点
                                print("这是车辆所处的经纬度")
                                # 上传数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                # 数据块：N 的十六进制为4E; P的十六进制为50；L为4C；B为42；卫星个数：01；填充数据： 00 00
                                # 经度：（120.04208246406465）40 5E 02 B1 7A A5 B9 23  纬度：（30.231343807768763）40 3E 3B 39 59 08 7F BB
                                # 120.04862759640338  \x40\x5e\x03\x1c\xb6\xec\x0f\x14  30.237128736109234  \x40\x3e\x3c\xb4\x78\x06\x87\xee
                                # 120.0457642526888  \x40\x5e\x02\xed\xcd\x30\x27\xf4  30.23500645123769  \x40\x3e\x3c\x29\x61\xfe\x6a\x37
                                dataFromCar_jingwei_from_car = tcp_socket_ID8.recv(4)  # 接收GPS等
                                try:
                                    y11, y12, y13, y14 = struct.unpack('4B', dataFromCar_jingwei_from_car)
                                except:
                                    print("解析GPS/卫星数据出错")
                                GPS = y11  # GPS协议类型
                                Star = y12  # 卫星个数
                                print("GPS:", str(GPS))
                                print("卫星个数：", int(Star))

                                dataFromCar_jingwei_from_car = tcp_socket_ID8.recv(32)
                                try:
                                    y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31, y32\
                                        = struct.unpack(
                                        '2d16B',
                                        dataFromCar_jingwei_from_car)  # 4B4i2I4B2d16B 解包C的结构体数据,大端格式加！,h表示两个字节的short型数据（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                except:
                                    print("解析经纬度数据出错")

                                ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                # print("接收数据转换成字符串为：", y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14,
                                #       y15, y16,
                                #       y17,
                                #       y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31,y32)

                                jingdu_Car = y15  # 小车所处经度
                                weidu_Car = y16  # 小车所处纬度
                                lng = y15
                                lat = y16
                                converted = []
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))


                                #================写入数据库
                                conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                       autocommit=True)

                                # 使用cursor()方法获取操作游标
                                cursor2 = conn.cursor()

                                # SQL语句：向数据表中插入数据
                                # sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)VALUES (x6, y11,y15,y16)"""  # 修改这一行数据，可多次插入
                                # VALUES 里的数据的类型一定要与定义表时的类型一致,该方法适合传入给定数据，如果是变量则要用（"%s",%d）等格式字符
                                sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)values("%s","%s","%s","%s")"""  # 修改这一行数据，可多次插入
                                data_lnglat = (x8, y11, y15, y16)

                                # 异常处理
                                try:
                                    # 执行SQL语句
                                    cursor2.execute(sql2, data_lnglat)
                                    # 提交事务到数据库执行
                                    conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                    print("经纬度数据写入数据库")
                                except:
                                    # 如果发生错误则执行回滚操作
                                    conn.rollback()

                                # 关闭数据库连接
                                conn.close()
                                ##############写入数据库


                                converted = wgs84_to_bd09_change.gcj02_to_bd09(y15,
                                                                               y16)  # 调用外部函数将谷歌地图GPS经纬度数据转换成百度地图格式

                                fun_time_ID8(converted[0], converted[1])

                                # ti = threading.Thread(target=fun_time, args=(converted[0], converted[1])) ##传入经纬度和车辆ID，将其写入对应的json文件
                                # ti.start()

                                self.siglng_ID8.emit(float(converted[0]))
                                self.siglat_ID8.emit(float(converted[1]))
                                # time.sleep(1)

                                End_Lnglat = time.time()
                                print("执行一次经纬度数据读取用时", End_Lnglat - Start_LngLat)

                                # print("GPS:", str(GPS))
                                # print("卫星个数：", int(Star))
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))
                            ##================================获取车辆上传的GPS定位数据

                            elif (x9 == 3 ):  # 如果上传数据字节数过多，则为图像信息

                                print("上传的是图像数据")
                                # def ImageRead():
                                StartImage = time.time()  # 开始读取图片数据

                                data_image = tcp_socket_ID8.recv(1)
                                try:
                                    image_geshi = struct.unpack('B', data_image)
                                except:
                                    print("解析图像格式出错")
                                # print("图像格式为：", image_geshi)
                                data_image = tcp_socket_ID8.recv(4)
                                try:
                                    image_len = struct.unpack('1I', data_image)
                                except:
                                    print("解析图像字节数出错")
                                print("图像字节数：", image_len)

                                image_msg = b''
                                # print("帧中读取的图像数据块字节数，未转化成int型前：", image_len)
                                len1 = int(image_len[0])  # 图像数据的字节长度
                                # print("转化成int型后：", len1)
                                image_length = len1
                                readlength = 0  # 从缓冲区读取的字节数
                                while (len1 > 0):
                                    if len1 > 20000:  # 如果剩余图像字节数大于20000
                                        buffer = tcp_socket_ID8.recv(20000,
                                                                     socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                        # print("本次recv收到的字节是否为20000，", len(buffer))  # 检查每次recv是否收到完整的1024个字节
                                        image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                        len1 = len1 - 20000
                                        readlength += 20000
                                    else:
                                        buffer = tcp_socket_ID8.recv(len1, socket.MSG_WAITALL)
                                        # print("剩余不满20000的字节数为", len1, "读取的字节数为", len(buffer))  # 检查最后一次读取的字节数
                                        image_msg += buffer
                                        readlength += len1
                                        break

                                try:
                                    # 将读取到的字节流存储到图像文件中
                                    start = time.time()
                                    with open("image_file_ID8.jpg", "wb+") as img_file:
                                        img_file.write(image_msg)
                                    end = time.time()
                                    print("写入图片用时", end - start)
                                    imge = "image_file_ID8.jpg"
                                    self.sigImage.emit(imge)


                                except:
                                    print("图像数据出错")

                                # 继续检测包尾
                                left = tcp_socket_ID8.recv(1)
                                while 1:
                                    try:
                                        left_baowei = struct.unpack('B', left)
                                        # print("检测包尾读到的数据为", left_baowei)
                                    except:
                                        print("检测包尾第一个字节解析错误")

                                    # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                                    if (left_baowei == (204,)):  # 如果读到包尾则一次性读完包尾
                                        left = tcp_socket_ID8.recv(3)
                                        print("读完四个包尾")
                                        break
                                    else:
                                        left = tcp_socket_ID8.recv(1)

                                EndImage = time.time()  # 发送完图片时间
                                print("一次图片操作用时", EndImage - StartImage)

                            else:
                                    print("上传数据出错")
                            # 如果是ID为1的车发送的数据则进行接收


                while True:
                    # 创建一个线程去读取数据
                    read_thread = threading.Thread(target=read_thread_method)
                    # read_thread.setDaemon(True)  # 守护线程，read_thread作为一个守护线程，主线程结束，其立马也随之结束
                    read_thread.start()
                    # 要在线程执行完毕后在关闭套接字，不然会报错：在一个非套接字上尝试了一个操作
                    # read_thread.join()  # join 设置为主线程等待子线程结束后再继续执行主线程


                    #
                    #     askimage_thread = threading.Thread(target=askimage_method)
                    #     askimage_thread.start()
                    #     print("开启主动请求图像线程")

                    while True:

                        j = 0  # 请求状态数据时的计数
                        h = 0  # 请求图像数据时的计数

                        ###=======================上位机主动下发第一组经纬度数据
                        if (sendFlag_ID8 == 1):
                            print("下发第一组数据")
                            baotou_1 = 0xff  # char
                            baotou_2 = 0xff  # char
                            baotou_3 = 0xff  # char
                            baotou_4 = 0xff  # char
                            baochang_1 = 128  # int  包长  字节对齐会在double前面加上四个字节00000000
                            baoxuhao_1 = 1  # int  发送次数
                            shijianchuo_1 = 0  # int  上位机下发设为0
                            # zhongduanID_1 = 1  # int  终端ID
                            shujuyu_11 = 1  # int  类型1表示下发经纬度
                            shujuyu_21 = 84  # int  5个经纬度数组，一共80字节
                            dianshu_11 = 5  # I 下发5个点

                            ## 数据块之前的内容
                            data_11 = [baotou_1, baotou_2, baotou_3, baotou_4, baochang_1, baoxuhao_1, shijianchuo_1,

                                       shujuyu_11, shujuyu_21, dianshu_11]

                            #####################################--------------------------------------------数据域
                            file_path = "jingweidu.txt"  # 经纬度存储文件名

                            with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                t_sum1 = len(f.readlines())  # 总共有的经纬度组数

                                if 6 < t_sum1:  # 保证文档里经纬度数据大于五个

                                    for n in range(1, 6):
                                        line_number_1 = n  # 文件行数从1开始
                                        fread_n = linecache.getline(file_path, line_number_1).strip()  # 读取对应行数的经纬度
                                        fread_n_num = fread_n.strip("()")  # 删去字符串中左右两边的括号
                                        fread_split = fread_n_num.split(",")
                                        fread_n_jingdu = fread_split[0]  # 每行的经度str
                                        fread_n_weidu = fread_split[1]  # 每行的纬度str

                                        jingdu_1 = float(fread_n_jingdu)
                                        weidu_1 = float(fread_n_weidu)
                                        data_11.append(jingdu_1)
                                        data_11.append(weidu_1)
                                else:
                                    print("已经发送完毕所有数据")
                            f.close()

                            yuliu_1 = 0x00
                            # 循环加入12个0x00表示预留位和CRC32位
                            for s in range(0, 12):
                                data_11.append(yuliu_1)

                            baowei_1 = 0xee
                            # 循环加入四个0xee表示包尾
                            for t in range(0, 4):
                                data_11.append(baowei_1)

                            ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                            # 为小端接收模式
                            dataTobytes_1 = struct.pack('4B6i10d16B', data_11[0], data_11[1], data_11[2], data_11[3],
                                                        data_11[4], data_11[5]
                                                        , data_11[6], data_11[7], data_11[8], data_11[9], data_11[10],
                                                        data_11[11]
                                                        , data_11[12], data_11[13], data_11[14], data_11[15],
                                                        data_11[16],
                                                        data_11[17], data_11[18], data_11[19]
                                                        , data_11[20], data_11[21], data_11[22], data_11[23],
                                                        data_11[24],
                                                        data_11[25], data_11[26], data_11[27]
                                                        , data_11[28], data_11[29], data_11[30], data_11[31],
                                                        data_11[32],
                                                        data_11[33], data_11[34], data_11[35]

                                                        )
                            # print(type(dataTobytes_1), len(dataTobytes_1))

                            tcp_socket_ID8.send(dataTobytes_1)
                            sendFlag_ID8 = 0
                            ###=======================上位机主动下发第一组经纬度数据


                        if (askstateFlag_ID8 == 1):  # 如果请求状态按钮被激活则 下发请求状态指令，小车发送任意指令上位机均可以下发请求指令
                            askstate_thread_ID8 = threading.Thread(target=askstate_method_ID8)
                            askstate_thread_ID8.start()
                            print("开启主动请求状态线程")
                            print("askstateFlag_ID8:", askstateFlag_ID8)

                        if (askstateFlag_ID8 == 2):
                            print("开始请求车辆状态的数据")

                            send_state_baotou = 0xff  # 包头
                            send_state_baochang = 44  # 包长度，请求时数据域为0字节
                            send_state_xuhao = j  # 包序号
                            send_state_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_state_ID = 1  # int 固定车辆ID号
                            send_state_shujuyu_1 = 2  # int 第二类终端状态请求
                            send_state_shujuyu_2 = 0  # int 请求状态时L为0
                            send_state_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_state_yuliu = 0x00  # 保留帧暂时填充
                            send_state_baowei = 0xee  # 结束帧暂时填充

                            send_state_dataTobytes = []
                            for state_i in range(0, 4):
                                send_state_dataTobytes.append(send_state_baotou)
                            send_state_dataTobytes.append(send_state_baochang)
                            send_state_dataTobytes.append(send_state_xuhao)
                            send_state_dataTobytes.append(send_state_timechuo)
                            # send_state_dataTobytes.append(send_state_ID)
                            send_state_dataTobytes.append(send_state_shujuyu_1)
                            send_state_dataTobytes.append(send_state_shujuyu_2)
                            for state_j in range(0, 8):
                                send_state_dataTobytes.append(send_state_yuliu)

                            for state_k in range(0, 4):
                                send_state_dataTobytes.append(send_state_CRC32)

                            for state_l in range(0, 4):
                                send_state_dataTobytes.append(send_state_baowei)

                            dataTobytes_state = struct.pack('4B3i2I16B', send_state_dataTobytes[0],
                                                            send_state_dataTobytes[1], send_state_dataTobytes[2],
                                                            send_state_dataTobytes[3]
                                                            , send_state_dataTobytes[4], send_state_dataTobytes[5],
                                                            send_state_dataTobytes[6], send_state_dataTobytes[7]
                                                            , send_state_dataTobytes[8], send_state_dataTobytes[9],
                                                            send_state_dataTobytes[10], send_state_dataTobytes[11]
                                                            , send_state_dataTobytes[12], send_state_dataTobytes[13],
                                                            send_state_dataTobytes[14], send_state_dataTobytes[15]
                                                            , send_state_dataTobytes[16], send_state_dataTobytes[17],
                                                            send_state_dataTobytes[18], send_state_dataTobytes[19]
                                                            , send_state_dataTobytes[20], send_state_dataTobytes[21],
                                                            send_state_dataTobytes[22], send_state_dataTobytes[23]
                                                            , send_state_dataTobytes[24])

                            tcp_socket_ID8.send(dataTobytes_state)
                            askstateFlag_ID8 = 0  # 发送完后重新把标志位置零
                            j += 1
                        ####======================上位机向下位机发送请求状态数据的请求

                        ##==========================上位机向下位机请求图像数据
                        if (askimageFlag_ID8 == 1):  # 请求图像按钮被按下时激活，向下发送请求图像指令，小车发送任意数据上位机均可以下发请求指令
                            askimage_thread_ID8 = threading.Thread(target=askimage_method_ID8)
                            askimage_thread_ID8.start()
                            print("开启主动请求图像线程")
                            print("askimageFlag_ID8:", askimageFlag_ID8)

                        if (askimageFlag_ID8 == 2):
                            print("开始请求图像的数据")
                            send_image_baotou = 0xff  # 包头
                            send_image_baochang = 44  # 包长度，请求时数据域为0字节
                            send_image_xuhao = h  # 包序号
                            send_image_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_image_ID = 1  # int 固定车辆ID号
                            send_image_shujuyu_1 = 3  # int 第三类终端状态请求
                            send_image_shujuyu_2 = 0  # int 请求图像时L为0
                            send_image_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_image_yuliu = 0x00  # 保留帧暂时填充
                            send_image_baowei = 0xee  # 结束帧暂时填充

                            send_image_dataTobytes = []
                            for image_i in range(0, 4):
                                send_image_dataTobytes.append(send_image_baotou)
                            send_image_dataTobytes.append(send_image_baochang)
                            send_image_dataTobytes.append(send_image_xuhao)
                            send_image_dataTobytes.append(send_image_timechuo)
                            # send_image_dataTobytes.append(send_image_ID)
                            send_image_dataTobytes.append(send_image_shujuyu_1)
                            send_image_dataTobytes.append(send_image_shujuyu_2)
                            for image_j in range(0, 8):
                                send_image_dataTobytes.append(send_image_yuliu)

                            for state_k in range(0, 4):
                                send_image_dataTobytes.append(send_image_CRC32)

                            for state_l in range(0, 4):
                                send_image_dataTobytes.append(send_image_baowei)

                            dataTobytes_image = struct.pack('4B3i2I16B', send_image_dataTobytes[0],
                                                            send_image_dataTobytes[1], send_image_dataTobytes[2],
                                                            send_image_dataTobytes[3]
                                                            , send_image_dataTobytes[4], send_image_dataTobytes[5],
                                                            send_image_dataTobytes[6], send_image_dataTobytes[7]
                                                            , send_image_dataTobytes[8], send_image_dataTobytes[9],
                                                            send_image_dataTobytes[10], send_image_dataTobytes[11]
                                                            , send_image_dataTobytes[12], send_image_dataTobytes[13],
                                                            send_image_dataTobytes[14], send_image_dataTobytes[15]
                                                            , send_image_dataTobytes[16], send_image_dataTobytes[17],
                                                            send_image_dataTobytes[18], send_image_dataTobytes[19]
                                                            , send_image_dataTobytes[20], send_image_dataTobytes[21],
                                                            send_image_dataTobytes[22], send_image_dataTobytes[23]
                                                            , send_image_dataTobytes[24])

                            # client.send(dataTobytes_image)  # 发送请求的信号的数据格式
                            tcp_socket_ID8.send(dataTobytes_image)
                            askimageFlag_ID8 = 0  # 发送后标志位重新置零
                            h += 1
                        ##==========================上位机向下位机请求图像数据

                    # 清理socket，同样道理，这里需要锁定和解锁
                    # socket_lock.acquire()
                    # read_thread.join()
                    tcp_socket_ID8.close()
                    tcp_socket_ID8 = None
                    # socket_lock.release()
                    # break

    def upSend(self, flag):
        pass

# 第九辆车的监听线程
class Listener_ID9(QThread):  # 创建子线程类
    listenFlag = 1
    connectFlag = 1
    sigID_ID9 = pyqtSignal(str)  # run方法中用来将上位机的数据传送到GUI界面上
    sigState_ID9 = pyqtSignal(str)
    sigL2v_ID9 = pyqtSignal(float)
    sigR2v_ID9 = pyqtSignal(float)
    sigU_ID9 = pyqtSignal(float)
    sigangle_ID9 = pyqtSignal(float)
    sigImage_ID9 = pyqtSignal(str)

    sigAy_ID9 = pyqtSignal(float)
    sigYaw_ID9 = pyqtSignal(float)
    sigTn_ID9 = pyqtSignal(float)
    sigVy_ID9 = pyqtSignal(float)


    sigLPWM_ID9 = pyqtSignal(float)
    sigRPWM_ID9 = pyqtSignal(float)

    siglat_ID9 = pyqtSignal(float)
    siglng_ID9 = pyqtSignal(float)



    def __init__(self, ip, port, serverIP, serverPort, length, weight, maxV,
                 minV, maxA, maxD):
        super(Listener_ID9, self).__init__()  # 继承父类的属性和方法

        self.L2vArr = []
        self.R2vArr = []
        self.dataFromCarDecode = ''
        self.serverFlag = 0
        self.flag = 1



    def run(self):
        global sendFlag_ID9  # 因为sendFlag是在方法外定义的变量，所以要在方法内使用的话加上global成为全局变量
        global startFlag
        global askstateFlag_ID9
        global askimageFlag_ID9
        global frame
        global askstate_imageFlag_ID9



        sendFlag_ID9 = 0
        startFlag = 0
        askstateFlag_ID9 = 0
        askimageFlag_ID9 = 0
        askstate_imageFlag_ID9 = 0

        def askimage_method_ID9():
            global askimageFlag_ID9
            while True:
                askimageFlag_ID9 = 2
                time.sleep(10)  # 每隔10秒主动请求一次图像数据

        def askstate_method_ID9():
            global askstateFlag_ID9
            while True:
                askstateFlag_ID9 = 2
                time.sleep(5)  # 每隔5秒主动请求一次状态数据

        # ===================================接收上传经纬度数据并写入json文件
        # i=0
        def fun_time_ID9(lng_ID1, lat_ID2):  # 将上传的经纬度数据写入json文件中供BD_map.html文件读取
            # global i
            with open("weather9.json", "w", encoding='utf-8') as f:  # 打开对应车辆的json文件写入数据

                dicts = {"lng": lng_ID1, "lat": lat_ID2}
                f.write(json.dumps(dicts, indent=4))  # Indent表示隔开四个单位
                # i = i + 2
                # if i > 2000:
                #     i = 0

        # ===================================接收上传经纬度数据并写入json文件

        while True:

            while (self.listenFlag):
                print("连接云端服务器")

                tcp_socket_ID9 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # STREAM表示TCP传输
                tcp_socket_ID9.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

                # 2.链接服务器
                # server_ip = input("请输入服务器ip地址：")
                # server_port = input("请输入服务器端口:")
                # tcp_socket.connect((str(server_ip), server_port))
                # tcp_socket.connect(("10.80.7.157", 8080))
                tcp_socket_ID9.connect(("47.102.36.187", 8098))   # 链接云端服务器

                # 创建线程锁，防止主线程socket被close了，子线程还在recv而引发的异常
                # socket_lock = threading.Lock()
                def read_thread_method():  # 读取数据的方法
                    print("接收线程开启")

                    while True:
                        if not tcp_socket_ID9:  # 如果socket关闭，退出
                            break
                        dataFromCar = tcp_socket_ID9.recv(1)  # 缓冲区大小，接收文件的个数

                        i = 1  # 下发经纬度数据时的计数,前五个数已经主动下发

                        if not dataFromCar:
                            print("小车停止上传数据")
                        else:
                            while True:
                                print("逐个读取字节")
                                try:
                                    z1 = struct.unpack('B', dataFromCar)
                                except:
                                    print("第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包头
                                if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                                    dataFromCar = tcp_socket_ID9.recv(3)
                                    break
                                else:
                                    dataFromCar = tcp_socket_ID9.recv(1)
                            # print("dataFromCar的长度", len(dataFromCar))
                            try:
                                x2, x3, x4 = struct.unpack('3B', dataFromCar)  # 包头
                            except:
                                print("包头解析错误")

                            dataFromCar = tcp_socket_ID9.recv(24)
                            try:
                                x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar)
                            except:
                                print("前24个字节解析错误")
                            ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2
                            # print("该段字节流包长", x5)  # 查看包长是否正确

                            # 如果是ID为1的车发送的数据则进行接收
                            # if (x8 == 9):
                            if (x5 == 44):  # 如果上发的是44字节的数据（请求下发经纬度时设下位机发送数据块为空）
                                # 发送数据示例 dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18  00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                print(" 请求下发经纬度数据")
                                dataFromCar_jingwei_to_car = tcp_socket_ID9.recv(16)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                # print("读取余下的字节为：", dataFromCar_jingwei_to_car)
                                baotou1 = 0xff  # char
                                baotou2 = 0xff  # char
                                baotou3 = 0xff  # char
                                baotou4 = 0xff  # char
                                baochang = 128  # int  i包长 字节对齐会在double前面加上四个字节00000000
                                baoxuhao = i  # int  i发送次数
                                shijianchuo = 0  # int  i上位机下发设为0
                                # zhongduanID = 1  # int  i终端ID
                                shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
                                shujuyu_2 = 84  # int  I 5个经纬度数组，一共80字节
                                dianshu = 5  # Uint32 I 下发5个点

                                ## 数据块之前的内容
                                data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,

                                          shujuyu_1, shujuyu_2, dianshu]

                                #####################################--------------------------------------------数据域
                                file_path = "jingweidu.txt"  # 经纬度存储文件名

                                with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                    t_sum = len(f.readlines())  # 总共有的经纬度组数

                                    # print("ccccccc文档的总行数为：", t_sum)
                                    if 5 * i + 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
                                        for j in range(5 * i + 1, 5 * i + 6):
                                            line_number = j  # 文件行数从1开始，而i初始值为0
                                            fread_j = linecache.getline(file_path,
                                                                        line_number).strip()  # 读取对应行数的经纬度
                                            fread_j_num = fread_j.strip("()")  # 删去字符串中左右两边的括号
                                            fread_split = fread_j_num.split(",")
                                            fread_j_jingdu = fread_split[0]  # 每行的经度str
                                            fread_j_weidu = fread_split[1]  # 每行的纬度str
                                            print(type(fread_j_jingdu))
                                            print(fread_j_jingdu)

                                            jingdu = float(fread_j_jingdu)
                                            weidu = float(fread_j_weidu)
                                            data_1.append(jingdu)
                                            data_1.append(weidu)
                                    else:
                                        print("已经发送完毕所有数据")
                                f.close()
                                # 加入数据块后的数据包
                                # print("data_1", data_1)

                                yuliu = 0x00
                                # 循环加入12个0x00表示预留位和CRC32位
                                for n in range(0, 12):
                                    data_1.append(yuliu)

                                baowei = 0xee
                                # 循环加入四个0xee表示包尾
                                for m in range(0, 4):
                                    data_1.append(baowei)
                                    # print(data_1)

                                # 显示完整数据包
                                # print(data_1)

                                ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                                # 为大端接收模式
                                dataTobytes = struct.pack('4B3i3I10d16B', data_1[0], data_1[1], data_1[2], data_1[3],
                                                          data_1[4],
                                                          data_1[5]
                                                          , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10],
                                                          data_1[11]
                                                          , data_1[12], data_1[13], data_1[14], data_1[15],
                                                          data_1[16],
                                                          data_1[17], data_1[18], data_1[19]
                                                          , data_1[20], data_1[21], data_1[22], data_1[23],
                                                          data_1[24],
                                                          data_1[25], data_1[26], data_1[27]
                                                          , data_1[28], data_1[29], data_1[30], data_1[31],
                                                          data_1[32],
                                                          data_1[33], data_1[34], data_1[35]

                                                          )
                                # print(type(dataTobytes), len(dataTobytes))

                                tcp_socket_ID9.send(dataTobytes)
                                # print(i)
                                i += 1

                                # 0xff, 0xff, 0xff, 0xff, 128, 0, 0, 1, 1, 80, 5, 120.04208246406465, 30.231343807768763, \
                                # 120.04207836129298, 30.23134029404531, 120.04207425852078, 30.231336780321374, \
                                # 120.04207015574802, 30.231333266596973, 120.0420660529747, 30.231329752872096, \
                                # 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xee, 0xee, 0xee
                            # ==========================================下传经纬度数据

                            ####-------------------  接收下位机上传数据
                            ##================================更新车辆状态数据以及检测废数据
                            elif (x5 == 68):  # 小车上发车辆状态数据
                                # print("该段字节流包长：", x5)
                                print("这是上发的车辆的状态信息")
                                # 1. 如果数据域前四个字节为0，则上传的为无效的废数据
                                # 2. 如果数据域前四个字节为1，则上传的是车辆的状态信息，分别更新GUI界面上的数据
                                # 3. 如果数据域前四个字节为2，则上传的是GPS的定位信息，提取经纬度数据用于控制算法
                                # 4. 如果数据区前四个字节为3，则上传的是图像信息，更新GUI界面上的图像数据
                                # 上传结构体数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                dataFromCar_state_from_car = tcp_socket_ID9.recv(40)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                if (x9 == 0):  # 数据域前四个字节为0x000x000x000x00,对应情况1
                                    print("这是无效的废数据")
                                else:
                                    try:
                                        x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32\
                                            = struct.unpack(
                                            'I2fIfI16B',
                                            dataFromCar_state_from_car)  # 4B4i3I2fIfI16B  解包C的结构体数据，大端格式加！（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                    except:
                                        print("解析状态数据出错")

                                    ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                    # print("接收数据转换成字符串为：", x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14,
                                    #       x15, x16,
                                    #       x17,
                                    #       x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32)

                                    ##==============================更新车辆状态数据
                                    # elif (len(dataFromCar) == 68):  # 数据域前四个字节为0x000x000x000x01,对应情况2
                                    self.serverFlag = 1  # 启动多线程服务器？

                                    ID = x8
                                    LPWM = x11  # 车辆状态
                                    RPWM = x15  # 电池电压
                                    L2v = x12  # 左轮电机转速
                                    R2V = x13  # 右轮电机转速
                                    angle = x14

                                    self.sigID_ID9.emit(str(ID))  # 往GUI界面中传入数据,注意ID传入的参数为int型要与Listener属性定义处的sigID类型一致

                                    self.sigL2v_ID9.emit(float(L2v))

                                    self.sigR2v_ID9.emit(float(R2V))

                                    self.sigangle_ID9.emit(float(angle))

                                    self.sigLPWM_ID9.emit(LPWM)

                                    self.sigRPWM_ID9.emit(RPWM)

                                    Ay = 111
                                    Yaw = 111
                                    Tn = 111
                                    Vy = 111

                                    self.sigAy_ID9.emit(Ay)
                                    self.sigYaw_ID9.emit(Yaw)
                                    self.sigTn_ID9.emit(Tn)
                                    self.sigVy_ID9.emit(Vy)



                                    # ================写入数据库
                                    conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                           autocommit=True)

                                    # 使用cursor()方法获取操作游标
                                    cursor1 = conn.cursor()

                                    # SQL语句：向数据表中插入数据
                                    # sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                    #                                              VALUES (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)"""  # 修改这一行数据，可多次插入
                                    sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                                                                values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""  # 修改这一行数据，可多次插入
                                    data_state = (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)
                                    # 异常处理
                                    try:
                                        # 执行SQL语句
                                        cursor1.execute(sql1, data_state)
                                        # 提交事务到数据库执行
                                        conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                        print("状态数据写入数据库")
                                    except:
                                        # 如果发生错误则执行回滚操作
                                        conn.rollback()

                                    # 关闭数据库连接
                                    conn.close()
                                    ##############写入数据库

                                    # self.stateButton.setCheckable(False)
                                ##==============================更新车辆状态数据
                            ##================================更新车辆状态数据以及检测废数据

                            ##================================获取车辆上传的GPS定位数据
                            elif (x5 == 64):  # 如果上传的数据为64字节，则对应车辆目前GPS获取的经纬度数据
                                Start_LngLat = time.time()  # 开始读取经纬度的时间点
                                print("这是车辆所处的经纬度")
                                # 上传数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                # 数据块：N 的十六进制为4E; P的十六进制为50；L为4C；B为42；卫星个数：01；填充数据： 00 00
                                # 经度：（120.04208246406465）40 5E 02 B1 7A A5 B9 23  纬度：（30.231343807768763）40 3E 3B 39 59 08 7F BB
                                # 120.04862759640338  \x40\x5e\x03\x1c\xb6\xec\x0f\x14  30.237128736109234  \x40\x3e\x3c\xb4\x78\x06\x87\xee
                                # 120.0457642526888  \x40\x5e\x02\xed\xcd\x30\x27\xf4  30.23500645123769  \x40\x3e\x3c\x29\x61\xfe\x6a\x37
                                dataFromCar_jingwei_from_car = tcp_socket_ID9.recv(4)  # 接收GPS等
                                try:
                                    y11, y12, y13, y14 = struct.unpack('4B', dataFromCar_jingwei_from_car)
                                except:
                                    print("解析GPS/卫星数据出错")
                                GPS = y11  # GPS协议类型
                                Star = y12  # 卫星个数
                                print("GPS:", str(GPS))
                                print("卫星个数：", int(Star))

                                dataFromCar_jingwei_from_car = tcp_socket_ID9.recv(32)
                                try:
                                    y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31, y32 \
                                        = struct.unpack(
                                        '2d16B',
                                        dataFromCar_jingwei_from_car)  # 4B4i2I4B2d16B 解包C的结构体数据,大端格式加！,h表示两个字节的short型数据（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                except:
                                    print("解析经纬度数据出错")

                                ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                # print("接收数据转换成字符串为：", y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14,
                                #       y15, y16,
                                #       y17,
                                #       y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31,y32)

                                jingdu_Car = y15  # 小车所处经度
                                weidu_Car = y16  # 小车所处纬度
                                lng = y15
                                lat = y16
                                converted = []
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))


                                #================写入数据库
                                conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                       autocommit=True)

                                # 使用cursor()方法获取操作游标
                                cursor2 = conn.cursor()

                                # SQL语句：向数据表中插入数据
                                # sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)VALUES (x6, y11,y15,y16)"""  # 修改这一行数据，可多次插入
                                # VALUES 里的数据的类型一定要与定义表时的类型一致,该方法适合传入给定数据，如果是变量则要用（"%s",%d）等格式字符
                                sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)values("%s","%s","%s","%s")"""  # 修改这一行数据，可多次插入
                                data_lnglat = (x8, y11, y15, y16)

                                # 异常处理
                                try:
                                    # 执行SQL语句
                                    cursor2.execute(sql2, data_lnglat)
                                    # 提交事务到数据库执行
                                    conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                    print("经纬度数据写入数据库")
                                except:
                                    # 如果发生错误则执行回滚操作
                                    conn.rollback()

                                # 关闭数据库连接
                                conn.close()
                                ##############写入数据库


                                converted = wgs84_to_bd09_change.gcj02_to_bd09(y15,
                                                                               y16)  # 调用外部函数将谷歌地图GPS经纬度数据转换成百度地图格式

                                fun_time_ID9(converted[0], converted[1])

                                # ti = threading.Thread(target=fun_time, args=(converted[0], converted[1])) ##传入经纬度和车辆ID，将其写入对应的json文件
                                # ti.start()

                                self.siglng_ID9.emit(float(converted[0]))
                                self.siglat_ID9.emit(float(converted[1]))
                                # time.sleep(1)

                                End_Lnglat = time.time()
                                print("执行一次经纬度数据读取用时", End_Lnglat - Start_LngLat)

                                # print("GPS:", str(GPS))
                                # print("卫星个数：", int(Star))
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))
                            ##================================获取车辆上传的GPS定位数据

                            elif (x9 == 3 ):  # 如果上传数据字节数过多，则为图像信息

                                print("上传的是图像数据")
                                # def ImageRead():
                                StartImage = time.time()  # 开始读取图片数据

                                data_image = tcp_socket_ID9.recv(1)
                                try:
                                    image_geshi = struct.unpack('B', data_image)
                                except:
                                    print("解析图像格式出错")
                                # print("图像格式为：", image_geshi)
                                data_image = tcp_socket_ID9.recv(4)
                                try:
                                    image_len = struct.unpack('1I', data_image)
                                except:
                                    print("解析图像字节数出错")
                                print("图像字节数：", image_len)

                                image_msg = b''
                                # print("帧中读取的图像数据块字节数，未转化成int型前：", image_len)
                                len1 = int(image_len[0])  # 图像数据的字节长度
                                # print("转化成int型后：", len1)
                                image_length = len1
                                readlength = 0  # 从缓冲区读取的字节数
                                while (len1 > 0):
                                    if len1 > 20000:  # 如果剩余图像字节数大于20000
                                        buffer = tcp_socket_ID9.recv(20000,
                                                                     socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                        # print("本次recv收到的字节是否为20000，", len(buffer))  # 检查每次recv是否收到完整的1024个字节
                                        image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                        len1 = len1 - 20000
                                        readlength += 20000
                                    else:
                                        buffer = tcp_socket_ID9.recv(len1, socket.MSG_WAITALL)
                                        # print("剩余不满20000的字节数为", len1, "读取的字节数为", len(buffer))  # 检查最后一次读取的字节数
                                        image_msg += buffer
                                        readlength += len1
                                        break

                                try:
                                    # 将读取到的字节流存储到图像文件中
                                    start = time.time()
                                    with open("image_file_ID9.jpg", "wb+") as img_file:
                                        img_file.write(image_msg)
                                    end = time.time()
                                    print("写入图片用时", end - start)
                                    imge = "image_file_ID9.jpg"
                                    self.sigImage.emit(imge)


                                except:
                                    print("图像数据出错")

                                # 继续检测包尾
                                left = tcp_socket_ID9.recv(1)
                                while 1:
                                    try:
                                        left_baowei = struct.unpack('B', left)
                                        # print("检测包尾读到的数据为", left_baowei)
                                    except:
                                        print("检测包尾第一个字节解析错误")

                                    # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                                    if (left_baowei == (204,)):  # 如果读到包尾则一次性读完包尾
                                        left = tcp_socket_ID9.recv(3)
                                        print("读完四个包尾")
                                        break
                                    else:
                                        left = tcp_socket_ID9.recv(1)

                                EndImage = time.time()  # 发送完图片时间
                                print("一次图片操作用时", EndImage - StartImage)
                            else:
                                    print("上传数据出错")
                            # 如果是ID为1的车发送的数据则进行接收


                while True:
                    # 创建一个线程去读取数据
                    read_thread = threading.Thread(target=read_thread_method)
                    # read_thread.setDaemon(True)  # 守护线程，read_thread作为一个守护线程，主线程结束，其立马也随之结束
                    read_thread.start()
                    # 要在线程执行完毕后在关闭套接字，不然会报错：在一个非套接字上尝试了一个操作
                    # read_thread.join()  # join 设置为主线程等待子线程结束后再继续执行主线程


                    #
                    #     askimage_thread = threading.Thread(target=askimage_method)
                    #     askimage_thread.start()
                    #     print("开启主动请求图像线程")

                    while True:

                        j = 0  # 请求状态数据时的计数
                        h = 0  # 请求图像数据时的计数

                        ###=======================上位机主动下发第一组经纬度数据
                        if (sendFlag_ID9 == 1):
                            print("下发第一组数据")
                            baotou_1 = 0xff  # char
                            baotou_2 = 0xff  # char
                            baotou_3 = 0xff  # char
                            baotou_4 = 0xff  # char
                            baochang_1 = 128  # int  包长  字节对齐会在double前面加上四个字节00000000
                            baoxuhao_1 = 1  # int  发送次数
                            shijianchuo_1 = 0  # int  上位机下发设为0
                            # zhongduanID_1 = 1  # int  终端ID
                            shujuyu_11 = 1  # int  类型1表示下发经纬度
                            shujuyu_21 = 84  # int  5个经纬度数组，一共80字节
                            dianshu_11 = 5  # I 下发5个点

                            ## 数据块之前的内容
                            data_11 = [baotou_1, baotou_2, baotou_3, baotou_4, baochang_1, baoxuhao_1, shijianchuo_1,

                                       shujuyu_11, shujuyu_21, dianshu_11]

                            #####################################--------------------------------------------数据域
                            file_path = "jingweidu.txt"  # 经纬度存储文件名

                            with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                t_sum1 = len(f.readlines())  # 总共有的经纬度组数

                                if 6 < t_sum1:  # 保证文档里经纬度数据大于五个

                                    for n in range(1, 6):
                                        line_number_1 = n  # 文件行数从1开始
                                        fread_n = linecache.getline(file_path, line_number_1).strip()  # 读取对应行数的经纬度
                                        fread_n_num = fread_n.strip("()")  # 删去字符串中左右两边的括号
                                        fread_split = fread_n_num.split(",")
                                        fread_n_jingdu = fread_split[0]  # 每行的经度str
                                        fread_n_weidu = fread_split[1]  # 每行的纬度str

                                        jingdu_1 = float(fread_n_jingdu)
                                        weidu_1 = float(fread_n_weidu)
                                        data_11.append(jingdu_1)
                                        data_11.append(weidu_1)
                                else:
                                    print("已经发送完毕所有数据")
                            f.close()

                            yuliu_1 = 0x00
                            # 循环加入12个0x00表示预留位和CRC32位
                            for s in range(0, 12):
                                data_11.append(yuliu_1)

                            baowei_1 = 0xee
                            # 循环加入四个0xee表示包尾
                            for t in range(0, 4):
                                data_11.append(baowei_1)

                            ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                            # 为小端接收模式
                            dataTobytes_1 = struct.pack('4B6i10d16B', data_11[0], data_11[1], data_11[2], data_11[3],
                                                        data_11[4], data_11[5]
                                                        , data_11[6], data_11[7], data_11[8], data_11[9], data_11[10],
                                                        data_11[11]
                                                        , data_11[12], data_11[13], data_11[14], data_11[15],
                                                        data_11[16],
                                                        data_11[17], data_11[18], data_11[19]
                                                        , data_11[20], data_11[21], data_11[22], data_11[23],
                                                        data_11[24],
                                                        data_11[25], data_11[26], data_11[27]
                                                        , data_11[28], data_11[29], data_11[30], data_11[31],
                                                        data_11[32],
                                                        data_11[33], data_11[34], data_11[35]

                                                        )
                            # print(type(dataTobytes_1), len(dataTobytes_1))

                            tcp_socket_ID9.send(dataTobytes_1)
                            sendFlag_ID9 = 0
                            ###=======================上位机主动下发第一组经纬度数据


                        if (askstateFlag_ID9 == 1):  # 如果请求状态按钮被激活则 下发请求状态指令，小车发送任意指令上位机均可以下发请求指令
                            askstate_thread_ID9 = threading.Thread(target=askstate_method_ID9)
                            askstate_thread_ID9.start()
                            print("开启主动请求状态线程")
                            print("askstateFlag_ID9:", askstateFlag_ID9)

                        if (askstateFlag_ID9 == 2):
                            print("开始请求车辆状态的数据")

                            send_state_baotou = 0xff  # 包头
                            send_state_baochang = 44  # 包长度，请求时数据域为0字节
                            send_state_xuhao = j  # 包序号
                            send_state_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_state_ID = 1  # int 固定车辆ID号
                            send_state_shujuyu_1 = 2  # int 第二类终端状态请求
                            send_state_shujuyu_2 = 0  # int 请求状态时L为0
                            send_state_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_state_yuliu = 0x00  # 保留帧暂时填充
                            send_state_baowei = 0xee  # 结束帧暂时填充

                            send_state_dataTobytes = []
                            for state_i in range(0, 4):
                                send_state_dataTobytes.append(send_state_baotou)
                            send_state_dataTobytes.append(send_state_baochang)
                            send_state_dataTobytes.append(send_state_xuhao)
                            send_state_dataTobytes.append(send_state_timechuo)
                            # send_state_dataTobytes.append(send_state_ID)
                            send_state_dataTobytes.append(send_state_shujuyu_1)
                            send_state_dataTobytes.append(send_state_shujuyu_2)
                            for state_j in range(0, 8):
                                send_state_dataTobytes.append(send_state_yuliu)

                            for state_k in range(0, 4):
                                send_state_dataTobytes.append(send_state_CRC32)

                            for state_l in range(0, 4):
                                send_state_dataTobytes.append(send_state_baowei)

                            dataTobytes_state = struct.pack('4B3i2I16B', send_state_dataTobytes[0],
                                                            send_state_dataTobytes[1], send_state_dataTobytes[2],
                                                            send_state_dataTobytes[3]
                                                            , send_state_dataTobytes[4], send_state_dataTobytes[5],
                                                            send_state_dataTobytes[6], send_state_dataTobytes[7]
                                                            , send_state_dataTobytes[8], send_state_dataTobytes[9],
                                                            send_state_dataTobytes[10], send_state_dataTobytes[11]
                                                            , send_state_dataTobytes[12], send_state_dataTobytes[13],
                                                            send_state_dataTobytes[14], send_state_dataTobytes[15]
                                                            , send_state_dataTobytes[16], send_state_dataTobytes[17],
                                                            send_state_dataTobytes[18], send_state_dataTobytes[19]
                                                            , send_state_dataTobytes[20], send_state_dataTobytes[21],
                                                            send_state_dataTobytes[22], send_state_dataTobytes[23]
                                                            , send_state_dataTobytes[24])

                            tcp_socket_ID9.send(dataTobytes_state)
                            askstateFlag_ID9 = 0  # 发送完后重新把标志位置零
                            j += 1
                        ####======================上位机向下位机发送请求状态数据的请求

                        ##==========================上位机向下位机请求图像数据
                        if (askimageFlag_ID9 == 1):  # 请求图像按钮被按下时激活，向下发送请求图像指令，小车发送任意数据上位机均可以下发请求指令
                            askimage_thread_ID9 = threading.Thread(target=askimage_method_ID9)
                            askimage_thread_ID9.start()
                            print("开启主动请求图像线程")
                            print("askimageFlag_ID9:", askimageFlag_ID9)

                        if (askimageFlag_ID9 == 2):
                            print("开始请求图像的数据")
                            send_image_baotou = 0xff  # 包头
                            send_image_baochang = 44  # 包长度，请求时数据域为0字节
                            send_image_xuhao = h  # 包序号
                            send_image_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_image_ID = 1  # int 固定车辆ID号
                            send_image_shujuyu_1 = 3  # int 第三类终端状态请求
                            send_image_shujuyu_2 = 0  # int 请求图像时L为0
                            send_image_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_image_yuliu = 0x00  # 保留帧暂时填充
                            send_image_baowei = 0xee  # 结束帧暂时填充

                            send_image_dataTobytes = []
                            for image_i in range(0, 4):
                                send_image_dataTobytes.append(send_image_baotou)
                            send_image_dataTobytes.append(send_image_baochang)
                            send_image_dataTobytes.append(send_image_xuhao)
                            send_image_dataTobytes.append(send_image_timechuo)
                            # send_image_dataTobytes.append(send_image_ID)
                            send_image_dataTobytes.append(send_image_shujuyu_1)
                            send_image_dataTobytes.append(send_image_shujuyu_2)
                            for image_j in range(0, 8):
                                send_image_dataTobytes.append(send_image_yuliu)

                            for state_k in range(0, 4):
                                send_image_dataTobytes.append(send_image_CRC32)

                            for state_l in range(0, 4):
                                send_image_dataTobytes.append(send_image_baowei)

                            dataTobytes_image = struct.pack('4B3i2I16B', send_image_dataTobytes[0],
                                                            send_image_dataTobytes[1], send_image_dataTobytes[2],
                                                            send_image_dataTobytes[3]
                                                            , send_image_dataTobytes[4], send_image_dataTobytes[5],
                                                            send_image_dataTobytes[6], send_image_dataTobytes[7]
                                                            , send_image_dataTobytes[8], send_image_dataTobytes[9],
                                                            send_image_dataTobytes[10], send_image_dataTobytes[11]
                                                            , send_image_dataTobytes[12], send_image_dataTobytes[13],
                                                            send_image_dataTobytes[14], send_image_dataTobytes[15]
                                                            , send_image_dataTobytes[16], send_image_dataTobytes[17],
                                                            send_image_dataTobytes[18], send_image_dataTobytes[19]
                                                            , send_image_dataTobytes[20], send_image_dataTobytes[21],
                                                            send_image_dataTobytes[22], send_image_dataTobytes[23]
                                                            , send_image_dataTobytes[24])

                            # client.send(dataTobytes_image)  # 发送请求的信号的数据格式
                            tcp_socket_ID9.send(dataTobytes_image)
                            askimageFlag_ID9 = 0  # 发送后标志位重新置零
                            h += 1
                        ##==========================上位机向下位机请求图像数据

                    # 清理socket，同样道理，这里需要锁定和解锁
                    # socket_lock.acquire()
                    # read_thread.join()
                    tcp_socket_ID9.close()
                    tcp_socket_ID9 = None
                    # socket_lock.release()
                    # break

    def upSend(self, flag):
        pass

# 第十辆车的监听线程
class Listener_ID10(QThread):  # 创建子线程类
    listenFlag = 1
    connectFlag = 1
    sigID_ID10 = pyqtSignal(str)  # run方法中用来将上位机的数据传送到GUI界面上
    sigState_ID10 = pyqtSignal(str)
    sigL2v_ID10 = pyqtSignal(float)
    sigR2v_ID10 = pyqtSignal(float)
    sigU_ID10 = pyqtSignal(float)
    sigangle_ID10 = pyqtSignal(float)
    sigImage_ID10 = pyqtSignal(str)

    sigAy_ID10 = pyqtSignal(float)
    sigYaw_ID10 = pyqtSignal(float)
    sigTn_ID10 = pyqtSignal(float)
    sigVy_ID10 = pyqtSignal(float)


    sigLPWM_ID10 = pyqtSignal(float)
    sigRPWM_ID10 = pyqtSignal(float)

    siglat_ID10 = pyqtSignal(float)
    siglng_ID10 = pyqtSignal(float)



    def __init__(self, ip, port, serverIP, serverPort, length, weight, maxV,
                 minV, maxA, maxD):
        super(Listener_ID10, self).__init__()  # 继承父类的属性和方法

        self.L2vArr = []
        self.R2vArr = []
        self.dataFromCarDecode = ''
        self.serverFlag = 0
        self.flag = 1



    def run(self):
        global sendFlag_ID10  # 因为sendFlag是在方法外定义的变量，所以要在方法内使用的话加上global成为全局变量
        global startFlag
        global askstateFlag_ID10
        global askimageFlag_ID10
        global frame
        global askstate_imageFlag_ID10



        sendFlag_ID10 = 0
        startFlag = 0
        askstateFlag_ID10 = 0
        askimageFlag_ID10 = 0
        askstate_imageFlag_ID10 = 0

        def askimage_method_ID10():
            global askimageFlag_ID10
            while True:
                askimageFlag_ID10 = 2
                time.sleep(10)  # 每隔10秒主动请求一次图像数据

        def askstate_method_ID10():
            global askstateFlag_ID10
            while True:
                askstateFlag_ID10 = 2
                time.sleep(5)  # 每隔5秒主动请求一次状态数据

        # ===================================接收上传经纬度数据并写入json文件
        # i=0
        def fun_time_ID10(lng_ID1, lat_ID2):  # 将上传的经纬度数据写入json文件中供BD_map.html文件读取
            # global i
            with open("weather10.json", "w", encoding='utf-8') as f:  # 打开对应车辆的json文件写入数据

                dicts = {"lng": lng_ID1, "lat": lat_ID2}
                f.write(json.dumps(dicts, indent=4))  # Indent表示隔开四个单位
                # i = i + 2
                # if i > 2000:
                #     i = 0

        # ===================================接收上传经纬度数据并写入json文件

        while True:

            while (self.listenFlag):
                print("连接云端服务器")

                tcp_socket_ID10 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # STREAM表示TCP传输
                tcp_socket_ID10.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

                # 2.链接服务器
                # server_ip = input("请输入服务器ip地址：")
                # server_port = input("请输入服务器端口:")
                # tcp_socket.connect((str(server_ip), server_port))
                # tcp_socket.connect(("10.80.7.157", 8080))
                tcp_socket_ID10.connect(("47.102.36.187", 8100))   # 链接云端服务器

                # 创建线程锁，防止主线程socket被close了，子线程还在recv而引发的异常
                # socket_lock = threading.Lock()
                def read_thread_method():  # 读取数据的方法
                    print("接收线程开启")

                    while True:
                        if not tcp_socket_ID10:  # 如果socket关闭，退出
                            break
                        dataFromCar = tcp_socket_ID10.recv(1)  # 缓冲区大小，接收文件的个数

                        i = 1  # 下发经纬度数据时的计数,前五个数已经主动下发

                        if not dataFromCar:
                            print("小车停止上传数据")
                        else:
                            while True:
                                print("逐个读取字节")
                                try:
                                    z1 = struct.unpack('B', dataFromCar)
                                except:
                                    print("第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包头
                                if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                                    dataFromCar = tcp_socket_ID10.recv(3)
                                    break
                                else:
                                    dataFromCar = tcp_socket_ID10.recv(1)
                            # print("dataFromCar的长度", len(dataFromCar))
                            try:
                                x2, x3, x4 = struct.unpack('3B', dataFromCar)  # 包头
                            except:
                                print("包头解析错误")

                            dataFromCar = tcp_socket_ID10.recv(24)
                            try:
                                x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar)
                            except:
                                print("前24个字节解析错误")
                            ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2
                            # print("该段字节流包长", x5)  # 查看包长是否正确

                            # 如果是ID为1的车发送的数据则进行接收
                            # if (x8 == 10):
                            if (x5 == 44):  # 如果上发的是44字节的数据（请求下发经纬度时设下位机发送数据块为空）
                                # 发送数据示例 dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18  00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                print(" 请求下发经纬度数据")
                                dataFromCar_jingwei_to_car = tcp_socket_ID10.recv(16)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                # print("读取余下的字节为：", dataFromCar_jingwei_to_car)
                                baotou1 = 0xff  # char
                                baotou2 = 0xff  # char
                                baotou3 = 0xff  # char
                                baotou4 = 0xff  # char
                                baochang = 128  # int  i包长 字节对齐会在double前面加上四个字节00000000
                                baoxuhao = i  # int  i发送次数
                                shijianchuo = 0  # int  i上位机下发设为0
                                # zhongduanID = 1  # int  i终端ID
                                shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
                                shujuyu_2 = 84  # int  I 5个经纬度数组，一共80字节
                                dianshu = 5  # Uint32 I 下发5个点

                                ## 数据块之前的内容
                                data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,

                                          shujuyu_1, shujuyu_2, dianshu]

                                #####################################--------------------------------------------数据域
                                file_path = "jingweidu.txt"  # 经纬度存储文件名

                                with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                    t_sum = len(f.readlines())  # 总共有的经纬度组数

                                    # print("ccccccc文档的总行数为：", t_sum)
                                    if 5 * i + 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
                                        for j in range(5 * i + 1, 5 * i + 6):
                                            line_number = j  # 文件行数从1开始，而i初始值为0
                                            fread_j = linecache.getline(file_path,
                                                                        line_number).strip()  # 读取对应行数的经纬度
                                            fread_j_num = fread_j.strip("()")  # 删去字符串中左右两边的括号
                                            fread_split = fread_j_num.split(",")
                                            fread_j_jingdu = fread_split[0]  # 每行的经度str
                                            fread_j_weidu = fread_split[1]  # 每行的纬度str
                                            print(type(fread_j_jingdu))
                                            print(fread_j_jingdu)

                                            jingdu = float(fread_j_jingdu)
                                            weidu = float(fread_j_weidu)
                                            data_1.append(jingdu)
                                            data_1.append(weidu)
                                    else:
                                        print("已经发送完毕所有数据")
                                f.close()
                                # 加入数据块后的数据包
                                # print("data_1", data_1)

                                yuliu = 0x00
                                # 循环加入12个0x00表示预留位和CRC32位
                                for n in range(0, 12):
                                    data_1.append(yuliu)

                                baowei = 0xee
                                # 循环加入四个0xee表示包尾
                                for m in range(0, 4):
                                    data_1.append(baowei)
                                    # print(data_1)

                                # 显示完整数据包
                                # print(data_1)

                                ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                                # 为大端接收模式
                                dataTobytes = struct.pack('4B3i3I10d16B', data_1[0], data_1[1], data_1[2], data_1[3],
                                                          data_1[4],
                                                          data_1[5]
                                                          , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10],
                                                          data_1[11]
                                                          , data_1[12], data_1[13], data_1[14], data_1[15],
                                                          data_1[16],
                                                          data_1[17], data_1[18], data_1[19]
                                                          , data_1[20], data_1[21], data_1[22], data_1[23],
                                                          data_1[24],
                                                          data_1[25], data_1[26], data_1[27]
                                                          , data_1[28], data_1[29], data_1[30], data_1[31],
                                                          data_1[32],
                                                          data_1[33], data_1[34], data_1[35]

                                                          )
                                # print(type(dataTobytes), len(dataTobytes))

                                tcp_socket_ID10.send(dataTobytes)
                                # print(i)
                                i += 1

                                # 0xff, 0xff, 0xff, 0xff, 128, 0, 0, 1, 1, 80, 5, 120.04208246406465, 30.231343807768763, \
                                # 120.04207836129298, 30.23134029404531, 120.04207425852078, 30.231336780321374, \
                                # 120.04207015574802, 30.231333266596973, 120.0420660529747, 30.231329752872096, \
                                # 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xee, 0xee, 0xee
                            # ==========================================下传经纬度数据

                            ####-------------------  接收下位机上传数据
                            ##================================更新车辆状态数据以及检测废数据
                            elif (x5 == 68):  # 小车上发车辆状态数据
                                # print("该段字节流包长：", x5)
                                print("这是上发的车辆的状态信息")
                                # 1. 如果数据域前四个字节为0，则上传的为无效的废数据
                                # 2. 如果数据域前四个字节为1，则上传的是车辆的状态信息，分别更新GUI界面上的数据
                                # 3. 如果数据域前四个字节为2，则上传的是GPS的定位信息，提取经纬度数据用于控制算法
                                # 4. 如果数据区前四个字节为3，则上传的是图像信息，更新GUI界面上的图像数据
                                # 上传结构体数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                dataFromCar_state_from_car = tcp_socket_ID10.recv(40)  # 读取本次数据余下的字节，使得指针指向下一组上传的数据字节流开头
                                if (x9 == 0):  # 数据域前四个字节为0x000x000x000x00,对应情况1
                                    print("这是无效的废数据")
                                else:
                                    try:
                                        x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32 \
                                            = struct.unpack(
                                            'I2fIfI16B',
                                            dataFromCar_state_from_car)  # 4B4i3I2fIfI16B  解包C的结构体数据，大端格式加！（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                    except:
                                        print("解析状态数据出错")

                                    ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                    # print("接收数据转换成字符串为：", x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14,
                                    #       x15, x16,
                                    #       x17,
                                    #       x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32)

                                    ##==============================更新车辆状态数据
                                    # elif (len(dataFromCar) == 68):  # 数据域前四个字节为0x000x000x000x01,对应情况2
                                    self.serverFlag = 1  # 启动多线程服务器？

                                    ID = x8
                                    LPWM = x11  # 车辆状态
                                    RPWM = x15  # 电池电压
                                    L2v = x12  # 左轮电机转速
                                    R2V = x13  # 右轮电机转速
                                    angle = x14

                                    self.sigID_ID10.emit(str(ID))  # 往GUI界面中传入数据,注意ID传入的参数为int型要与Listener属性定义处的sigID类型一致

                                    self.sigL2v_ID10.emit(float(L2v))

                                    self.sigR2v_ID10.emit(float(R2V))

                                    self.sigangle_ID10.emit(float(angle))

                                    self.sigLPWM_ID10.emit(LPWM)

                                    self.sigRPWM_ID10.emit(RPWM)

                                    Ay = 111
                                    Yaw = 111
                                    Tn = 111
                                    Vy = 111

                                    self.sigAy_ID10.emit(Ay)
                                    self.sigYaw_ID10.emit(Yaw)
                                    self.sigTn_ID10.emit(Tn)
                                    self.sigVy_ID10.emit(Vy)



                                    # ================写入数据库
                                    conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                           autocommit=True)

                                    # 使用cursor()方法获取操作游标
                                    cursor1 = conn.cursor()

                                    # SQL语句：向数据表中插入数据
                                    # sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                    #                                              VALUES (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)"""  # 修改这一行数据，可多次插入
                                    sql1 = """INSERT INTO State(Number_M, ID_M, State_M, UPWM_M, L2V_M, R2V_M, Angle_M, Ay_M, Yaw_M, Tn_M, Vy_M)
                                                                                values("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")"""  # 修改这一行数据，可多次插入
                                    data_state = (x6, x8, x11, x15, x12, x13, x14, Ay, Yaw, Tn, Vy)
                                    # 异常处理
                                    try:
                                        # 执行SQL语句
                                        cursor1.execute(sql1, data_state)
                                        # 提交事务到数据库执行
                                        conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                        print("状态数据写入数据库")
                                    except:
                                        # 如果发生错误则执行回滚操作
                                        conn.rollback()

                                    # 关闭数据库连接
                                    conn.close()
                                    ##############写入数据库

                                    # self.stateButton.setCheckable(False)
                                ##==============================更新车辆状态数据
                            ##================================更新车辆状态数据以及检测废数据

                            ##================================获取车辆上传的GPS定位数据
                            elif (x5 == 64):  # 如果上传的数据为64字节，则对应车辆目前GPS获取的经纬度数据
                                Start_LngLat = time.time()  # 开始读取经纬度的时间点
                                print("这是车辆所处的经纬度")
                                # 上传数据示例
                                # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                                # 数据块：N 的十六进制为4E; P的十六进制为50；L为4C；B为42；卫星个数：01；填充数据： 00 00
                                # 经度：（120.04208246406465）40 5E 02 B1 7A A5 B9 23  纬度：（30.231343807768763）40 3E 3B 39 59 08 7F BB
                                # 120.04862759640338  \x40\x5e\x03\x1c\xb6\xec\x0f\x14  30.237128736109234  \x40\x3e\x3c\xb4\x78\x06\x87\xee
                                # 120.0457642526888  \x40\x5e\x02\xed\xcd\x30\x27\xf4  30.23500645123769  \x40\x3e\x3c\x29\x61\xfe\x6a\x37
                                dataFromCar_jingwei_from_car = tcp_socket_ID10.recv(4)  # 接收GPS等
                                try:
                                    y11, y12, y13, y14 = struct.unpack('4B', dataFromCar_jingwei_from_car)
                                except:
                                    print("解析GPS/卫星数据出错")
                                GPS = y11  # GPS协议类型
                                Star = y12  # 卫星个数
                                print("GPS:", str(GPS))
                                print("卫星个数：", int(Star))

                                dataFromCar_jingwei_from_car = tcp_socket_ID10.recv(32)
                                try:
                                    y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31, y32 = struct.unpack(
                                        '2d16B',
                                        dataFromCar_jingwei_from_car)  # 4B4i2I4B2d16B 解包C的结构体数据,大端格式加！,h表示两个字节的short型数据（网络调试助手为大端格式，下位机上传为小端格式，需要改）
                                except:
                                    print("解析经纬度数据出错")

                                ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                                # print("接收数据转换成字符串为：", y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14,
                                #       y15, y16,
                                #       y17,
                                #       y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31,y32)

                                jingdu_Car = y15  # 小车所处经度
                                weidu_Car = y16  # 小车所处纬度
                                lng = y15
                                lat = y16
                                converted = []
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))


                                #================写入数据库
                                conn = pymysql.connect('47.102.36.187', 'root', 'Zjy_812240127', 'Car_Upload',
                                                       autocommit=True)

                                # 使用cursor()方法获取操作游标
                                cursor2 = conn.cursor()

                                # SQL语句：向数据表中插入数据
                                # sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)VALUES (x6, y11,y15,y16)"""  # 修改这一行数据，可多次插入
                                # VALUES 里的数据的类型一定要与定义表时的类型一致,该方法适合传入给定数据，如果是变量则要用（"%s",%d）等格式字符
                                sql2 = """INSERT INTO lng_lat(Number_M, GPS_M,Lng_M, Lat_M)values("%s","%s","%s","%s")"""  # 修改这一行数据，可多次插入
                                data_lnglat = (x8, y11, y15, y16)

                                # 异常处理
                                try:
                                    # 执行SQL语句
                                    cursor2.execute(sql2, data_lnglat)
                                    # 提交事务到数据库执行
                                    conn.commit()  # 事务是访问和更新数据库的一个程序执行单元
                                    print("经纬度数据写入数据库")
                                except:
                                    # 如果发生错误则执行回滚操作
                                    conn.rollback()

                                # 关闭数据库连接
                                conn.close()
                                ##############写入数据库


                                converted = wgs84_to_bd09_change.gcj02_to_bd09(y15,
                                                                               y16)  # 调用外部函数将谷歌地图GPS经纬度数据转换成百度地图格式

                                fun_time_ID10(converted[0], converted[1])

                                # ti = threading.Thread(target=fun_time, args=(converted[0], converted[1])) ##传入经纬度和车辆ID，将其写入对应的json文件
                                # ti.start()

                                self.siglng_ID10.emit(float(converted[0]))
                                self.siglat_ID10.emit(float(converted[1]))
                                # time.sleep(1)

                                End_Lnglat = time.time()
                                print("执行一次经纬度数据读取用时", End_Lnglat - Start_LngLat)

                                # print("GPS:", str(GPS))
                                # print("卫星个数：", int(Star))
                                # print("小车所处经度:", float(jingdu_Car))
                                # print("小车所处纬度:", float(weidu_Car))
                            ##================================获取车辆上传的GPS定位数据

                            elif (x9 == 3 ):  # 如果上传数据字节数过多，则为图像信息

                                print("上传的是图像数据")
                                # def ImageRead():
                                StartImage = time.time()  # 开始读取图片数据

                                data_image = tcp_socket_ID10.recv(1)
                                try:
                                    image_geshi = struct.unpack('B', data_image)
                                except:
                                    print("解析图像格式出错")
                                # print("图像格式为：", image_geshi)
                                data_image = tcp_socket_ID10.recv(4)
                                try:
                                    image_len = struct.unpack('1I', data_image)
                                except:
                                    print("解析图像字节数出错")
                                print("图像字节数：", image_len)

                                image_msg = b''
                                # print("帧中读取的图像数据块字节数，未转化成int型前：", image_len)
                                len1 = int(image_len[0])  # 图像数据的字节长度
                                # print("转化成int型后：", len1)
                                image_length = len1
                                readlength = 0  # 从缓冲区读取的字节数
                                while (len1 > 0):
                                    if len1 > 20000:  # 如果剩余图像字节数大于20000
                                        buffer = tcp_socket_ID10.recv(20000,
                                                                     socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                        # print("本次recv收到的字节是否为20000，", len(buffer))  # 检查每次recv是否收到完整的1024个字节
                                        image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                        len1 = len1 - 20000
                                        readlength += 20000
                                    else:
                                        buffer = tcp_socket_ID10.recv(len1, socket.MSG_WAITALL)
                                        # print("剩余不满20000的字节数为", len1, "读取的字节数为", len(buffer))  # 检查最后一次读取的字节数
                                        image_msg += buffer
                                        readlength += len1
                                        break

                                try:
                                    # 将读取到的字节流存储到图像文件中
                                    start = time.time()
                                    with open("image_file_ID10.jpg", "wb+") as img_file:
                                        img_file.write(image_msg)
                                    end = time.time()
                                    print("写入图片用时", end - start)
                                    imge = "image_file_ID10.jpg"
                                    self.sigImage.emit(imge)


                                except:
                                    print("图像数据出错")

                                # 继续检测包尾
                                left = tcp_socket_ID10.recv(1)
                                while 1:
                                    try:
                                        left_baowei = struct.unpack('B', left)
                                        # print("检测包尾读到的数据为", left_baowei)
                                    except:
                                        print("检测包尾第一个字节解析错误")

                                    # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                                    if (left_baowei == (204,)):  # 如果读到包尾则一次性读完包尾
                                        left = tcp_socket_ID10.recv(3)
                                        print("读完四个包尾")
                                        break
                                    else:
                                        left = tcp_socket_ID10.recv(1)

                                EndImage = time.time()  # 发送完图片时间
                                print("一次图片操作用时", EndImage - StartImage)

                            else:
                                    print("上传数据出错")
                            # 如果是ID为1的车发送的数据则进行接收


                while True:
                    # 创建一个线程去读取数据
                    read_thread = threading.Thread(target=read_thread_method)
                    # read_thread.setDaemon(True)  # 守护线程，read_thread作为一个守护线程，主线程结束，其立马也随之结束
                    read_thread.start()
                    # 要在线程执行完毕后在关闭套接字，不然会报错：在一个非套接字上尝试了一个操作
                    # read_thread.join()  # join 设置为主线程等待子线程结束后再继续执行主线程


                    #
                    #     askimage_thread = threading.Thread(target=askimage_method)
                    #     askimage_thread.start()
                    #     print("开启主动请求图像线程")

                    while True:

                        j = 0  # 请求状态数据时的计数
                        h = 0  # 请求图像数据时的计数

                        ###=======================上位机主动下发第一组经纬度数据
                        if (sendFlag_ID10 == 1):
                            print("下发第一组数据")
                            baotou_1 = 0xff  # char
                            baotou_2 = 0xff  # char
                            baotou_3 = 0xff  # char
                            baotou_4 = 0xff  # char
                            baochang_1 = 128  # int  包长  字节对齐会在double前面加上四个字节00000000
                            baoxuhao_1 = 1  # int  发送次数
                            shijianchuo_1 = 0  # int  上位机下发设为0
                            # zhongduanID_1 = 1  # int  终端ID
                            shujuyu_11 = 1  # int  类型1表示下发经纬度
                            shujuyu_21 = 84  # int  5个经纬度数组，一共80字节
                            dianshu_11 = 5  # I 下发5个点

                            ## 数据块之前的内容
                            data_11 = [baotou_1, baotou_2, baotou_3, baotou_4, baochang_1, baoxuhao_1, shijianchuo_1,

                                       shujuyu_11, shujuyu_21, dianshu_11]

                            #####################################--------------------------------------------数据域
                            file_path = "jingweidu.txt"  # 经纬度存储文件名

                            with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                                t_sum1 = len(f.readlines())  # 总共有的经纬度组数

                                if 6 < t_sum1:  # 保证文档里经纬度数据大于五个

                                    for n in range(1, 6):
                                        line_number_1 = n  # 文件行数从1开始
                                        fread_n = linecache.getline(file_path, line_number_1).strip()  # 读取对应行数的经纬度
                                        fread_n_num = fread_n.strip("()")  # 删去字符串中左右两边的括号
                                        fread_split = fread_n_num.split(",")
                                        fread_n_jingdu = fread_split[0]  # 每行的经度str
                                        fread_n_weidu = fread_split[1]  # 每行的纬度str

                                        jingdu_1 = float(fread_n_jingdu)
                                        weidu_1 = float(fread_n_weidu)
                                        data_11.append(jingdu_1)
                                        data_11.append(weidu_1)
                                else:
                                    print("已经发送完毕所有数据")
                            f.close()

                            yuliu_1 = 0x00
                            # 循环加入12个0x00表示预留位和CRC32位
                            for s in range(0, 12):
                                data_11.append(yuliu_1)

                            baowei_1 = 0xee
                            # 循环加入四个0xee表示包尾
                            for t in range(0, 4):
                                data_11.append(baowei_1)

                            ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                            # 为小端接收模式
                            dataTobytes_1 = struct.pack('4B6i10d16B', data_11[0], data_11[1], data_11[2], data_11[3],
                                                        data_11[4], data_11[5]
                                                        , data_11[6], data_11[7], data_11[8], data_11[9], data_11[10],
                                                        data_11[11]
                                                        , data_11[12], data_11[13], data_11[14], data_11[15],
                                                        data_11[16],
                                                        data_11[17], data_11[18], data_11[19]
                                                        , data_11[20], data_11[21], data_11[22], data_11[23],
                                                        data_11[24],
                                                        data_11[25], data_11[26], data_11[27]
                                                        , data_11[28], data_11[29], data_11[30], data_11[31],
                                                        data_11[32],
                                                        data_11[33], data_11[34], data_11[35]

                                                        )
                            # print(type(dataTobytes_1), len(dataTobytes_1))

                            tcp_socket_ID10.send(dataTobytes_1)
                            sendFlag_ID10 = 0
                            ###=======================上位机主动下发第一组经纬度数据


                        if (askstateFlag_ID10 == 1):  # 如果请求状态按钮被激活则 下发请求状态指令，小车发送任意指令上位机均可以下发请求指令
                            askstate_thread_ID10 = threading.Thread(target=askstate_method_ID10)
                            askstate_thread_ID10.start()
                            print("开启主动请求状态线程")
                            print("askstateFlag_ID10:", askstateFlag_ID10)

                        if (askstateFlag_ID10 == 2):
                            print("开始请求车辆状态的数据")

                            send_state_baotou = 0xff  # 包头
                            send_state_baochang = 44  # 包长度，请求时数据域为0字节
                            send_state_xuhao = j  # 包序号
                            send_state_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_state_ID = 1  # int 固定车辆ID号
                            send_state_shujuyu_1 = 2  # int 第二类终端状态请求
                            send_state_shujuyu_2 = 0  # int 请求状态时L为0
                            send_state_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_state_yuliu = 0x00  # 保留帧暂时填充
                            send_state_baowei = 0xee  # 结束帧暂时填充

                            send_state_dataTobytes = []
                            for state_i in range(0, 4):
                                send_state_dataTobytes.append(send_state_baotou)
                            send_state_dataTobytes.append(send_state_baochang)
                            send_state_dataTobytes.append(send_state_xuhao)
                            send_state_dataTobytes.append(send_state_timechuo)
                            # send_state_dataTobytes.append(send_state_ID)
                            send_state_dataTobytes.append(send_state_shujuyu_1)
                            send_state_dataTobytes.append(send_state_shujuyu_2)
                            for state_j in range(0, 8):
                                send_state_dataTobytes.append(send_state_yuliu)

                            for state_k in range(0, 4):
                                send_state_dataTobytes.append(send_state_CRC32)

                            for state_l in range(0, 4):
                                send_state_dataTobytes.append(send_state_baowei)

                            dataTobytes_state = struct.pack('4B3i2I16B', send_state_dataTobytes[0],
                                                            send_state_dataTobytes[1], send_state_dataTobytes[2],
                                                            send_state_dataTobytes[3]
                                                            , send_state_dataTobytes[4], send_state_dataTobytes[5],
                                                            send_state_dataTobytes[6], send_state_dataTobytes[7]
                                                            , send_state_dataTobytes[8], send_state_dataTobytes[9],
                                                            send_state_dataTobytes[10], send_state_dataTobytes[11]
                                                            , send_state_dataTobytes[12], send_state_dataTobytes[13],
                                                            send_state_dataTobytes[14], send_state_dataTobytes[15]
                                                            , send_state_dataTobytes[16], send_state_dataTobytes[17],
                                                            send_state_dataTobytes[18], send_state_dataTobytes[19]
                                                            , send_state_dataTobytes[20], send_state_dataTobytes[21],
                                                            send_state_dataTobytes[22], send_state_dataTobytes[23]
                                                            , send_state_dataTobytes[24])

                            tcp_socket_ID10.send(dataTobytes_state)
                            askstateFlag_ID10 = 0  # 发送完后重新把标志位置零
                            j += 1
                        ####======================上位机向下位机发送请求状态数据的请求

                        ##==========================上位机向下位机请求图像数据
                        if (askimageFlag_ID10 == 1):  # 请求图像按钮被按下时激活，向下发送请求图像指令，小车发送任意数据上位机均可以下发请求指令
                            askimage_thread_ID10 = threading.Thread(target=askimage_method_ID10)
                            askimage_thread_ID10.start()
                            print("开启主动请求图像线程")
                            print("askimageFlag_ID10:", askimageFlag_ID10)

                        if (askimageFlag_ID10 == 2):
                            print("开始请求图像的数据")
                            send_image_baotou = 0xff  # 包头
                            send_image_baochang = 44  # 包长度，请求时数据域为0字节
                            send_image_xuhao = h  # 包序号
                            send_image_timechuo = 0  # int 时间戳上位机 暂时设为零
                            # send_image_ID = 1  # int 固定车辆ID号
                            send_image_shujuyu_1 = 3  # int 第三类终端状态请求
                            send_image_shujuyu_2 = 0  # int 请求图像时L为0
                            send_image_CRC32 = 0x00  # CRC32四个字节暂时填充
                            send_image_yuliu = 0x00  # 保留帧暂时填充
                            send_image_baowei = 0xee  # 结束帧暂时填充

                            send_image_dataTobytes = []
                            for image_i in range(0, 4):
                                send_image_dataTobytes.append(send_image_baotou)
                            send_image_dataTobytes.append(send_image_baochang)
                            send_image_dataTobytes.append(send_image_xuhao)
                            send_image_dataTobytes.append(send_image_timechuo)
                            # send_image_dataTobytes.append(send_image_ID)
                            send_image_dataTobytes.append(send_image_shujuyu_1)
                            send_image_dataTobytes.append(send_image_shujuyu_2)
                            for image_j in range(0, 8):
                                send_image_dataTobytes.append(send_image_yuliu)

                            for state_k in range(0, 4):
                                send_image_dataTobytes.append(send_image_CRC32)

                            for state_l in range(0, 4):
                                send_image_dataTobytes.append(send_image_baowei)

                            dataTobytes_image = struct.pack('4B3i2I16B', send_image_dataTobytes[0],
                                                            send_image_dataTobytes[1], send_image_dataTobytes[2],
                                                            send_image_dataTobytes[3]
                                                            , send_image_dataTobytes[4], send_image_dataTobytes[5],
                                                            send_image_dataTobytes[6], send_image_dataTobytes[7]
                                                            , send_image_dataTobytes[8], send_image_dataTobytes[9],
                                                            send_image_dataTobytes[10], send_image_dataTobytes[11]
                                                            , send_image_dataTobytes[12], send_image_dataTobytes[13],
                                                            send_image_dataTobytes[14], send_image_dataTobytes[15]
                                                            , send_image_dataTobytes[16], send_image_dataTobytes[17],
                                                            send_image_dataTobytes[18], send_image_dataTobytes[19]
                                                            , send_image_dataTobytes[20], send_image_dataTobytes[21],
                                                            send_image_dataTobytes[22], send_image_dataTobytes[23]
                                                            , send_image_dataTobytes[24])

                            # client.send(dataTobytes_image)  # 发送请求的信号的数据格式
                            tcp_socket_ID10.send(dataTobytes_image)
                            askimageFlag_ID10 = 0  # 发送后标志位重新置零
                            h += 1
                        ##==========================上位机向下位机请求图像数据

                    # 清理socket，同样道理，这里需要锁定和解锁
                    # socket_lock.acquire()
                    # read_thread.join()
                    tcp_socket_ID10.close()
                    tcp_socket_ID10 = None
                    # socket_lock.release()
                    # break

    def upSend(self, flag):
        pass



#=========================窗口程序块
#第一辆车
class First_ID1(QWidget):


    serverSig = pyqtSignal()  # 申明无参数信号


    def __init__(self):  # 初始化
        self.myname = socket.getfqdn(socket.gethostname())  # gethostname() ： 返回本地主机的标准主机名。
        self.myaddr = socket.gethostbyname(self.myname)  # gethostbyname()：用域名或主机名获取IP地址
        super(First_ID1, self).__init__()  # 继承父类的属性和方法
        self.initUI()  # 调用自己的方法


    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)

        if int(i) == 2:  ## 传过来的是str型参数，转换成int型才可
            # self.hide()
            self.s2 = Second_ID2()
            self.s2.show()
            # self.s2.exec_()
            # self.setVisible(False)
            print("+++++++++++")




        elif int(i) == 3:
            # self.hide()
            self.t3 = Third_ID3()
            # return
            # print("++++++++++++++")
            self.t3.show()
            # self.t3.exec_()

        elif int(i) == 4:
            # self.hide()
            self.f4 = Forth_ID4()
            self.f4.show()
            # self.f4.exec_()

        elif int(i) == 5:
            # self.hide()
            self.f5 = Fifth_ID5()
            self.f5.show()
            # self.f5.exec_()

        elif int(i) == 6:
            # self.hide()
            self.s6 = Sixth_ID6()
            self.s6.show()
            # self.s6.exec_()

        elif int(i) == 7:
            # self.hide()
            self.s7 = Seventh_ID7()
            self.s7.show()
            # self.s7.exec_()

        elif int(i) == 8:
            # self.hide()
            self.e8 = Eighth_ID8()
            self.e8.show()

        elif int(i) == 9:
            # self.hide()
            self.n9 = Ninth_ID9()
            self.n9.show()

        elif int(i) == 10:
            # self.hide()
            self.t10 = Tenth_ID10()
            self.t10.show()

    def initUI(self):

        self.btn = QPushButton('jump to FirstUI', self)  # 用来返回到第一个界面
        self.btn.setGeometry(350, 50, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function_ID1)

        self.cb = QComboBox(self)
        self.cb.move(350, 10)
        self.cb.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容

        ##=======================================================第四层按钮组件
        # 退出按钮
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(QCoreApplication.instance().quit)  # 信号与槽，槽可以是QT内置的槽也可以是python内置方法
        self.quitButton.resize(self.quitButton.sizeHint())  # sizeHint()提供一个推荐大小
        self.quitButton.move(50, 360)  # 放置位子
        # 监听按钮
        self.listenButton = QPushButton('Listen', self)
        self.listenButton.setCheckable(True)  # 可以点击
        self.listenButton.clicked.connect(self.listenToClient)  # 链接到槽方法listenToClient,开始监听
        self.listenButton.resize(self.quitButton.sizeHint())  # 和quitButton按钮一样大
        self.listenButton.move(250, 360)  # 改变大小并移动

        #  开始按钮
        self.startButton = QPushButton('Start', self)
        self.startButton.setCheckable(True)
        self.startButton.clicked.connect(self.start)  # self.StartFlag = 1,表示开始向下位机发送数据
        self.startButton.resize(self.quitButton.sizeHint())
        self.startButton.move(50, 400)

        #  发送第一组数据按钮
        self.sendButton = QPushButton('Send', self)
        self.sendButton.setCheckable(True)
        self.sendButton.clicked.connect(self.send)  # 发送第一组经纬度
        self.sendButton.resize(self.quitButton.sizeHint())
        self.sendButton.move(250, 400)

        #  请求车辆的状态
        self.stateButton = QPushButton('AskState', self)
        self.stateButton.setCheckable(True)
        self.stateButton.clicked.connect(self.askstate)  # 发送停止信号 “ST”
        self.stateButton.resize(self.quitButton.sizeHint())
        self.stateButton.move(150, 360)

        #  请求车辆的图像
        self.imageButton = QPushButton('AskImage', self)
        self.imageButton.setCheckable(True)
        self.imageButton.clicked.connect(self.askimage)  # 发送停止信号 “ST”
        self.imageButton.resize(self.quitButton.sizeHint())
        self.imageButton.move(150, 400)

        #  请求百度地图
        # self.imageButton = QPushButton('BD_map', self)
        # self.imageButton.setCheckable(True)
        # self.imageButton.clicked.connect(self.mapshow)  # 发送显示地图指令
        # self.imageButton.resize(self.quitButton.sizeHint())
        # self.imageButton.move(150, 320)
        ##====================================================第四层按钮组件


        ##==============================================第一层按钮组件
        # 服务器角色 控件布局
        # 上位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(85, 10)
        self.carIPLabel.setText('上位机')
        # IP Label (20, 20) default size
        self.serverIPLabel = QLabel(self)
        self.serverIPLabel.move(20, 30)
        self.serverIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.serverIPLineEdit = QLineEdit(self)
        self.serverIPLineEdit.move(50, 38)
        self.serverIPLineEdit.resize(120, 15)
        self.serverIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverIPLineEdit.setText(self.myaddr)  # 本地主机的IP
        # IP Label (20, 40) default size
        self.serverPortLabel = QLabel(self)
        self.serverPortLabel.move(20, 50)
        self.serverPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.serverPortLineEdit = QLineEdit(self)
        self.serverPortLineEdit.move(50, 58)
        self.serverPortLineEdit.resize(120, 15)
        self.serverPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverPortLineEdit.setText('7890')  # 自己选取的端口号

        # 客户端角色 控件布局
        # 下位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(255, 10)
        self.carIPLabel.setText('阿里云')
        # IP Label (20, 20) default size
        self.clientIPLabel = QLabel(self)  # IP标签
        self.clientIPLabel.move(190, 30)
        self.clientIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.clientIPLineEdit = QLineEdit(self)  # IP显示文本框
        self.clientIPLineEdit.move(220, 38)
        self.clientIPLineEdit.resize(120, 15)
        self.clientIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        # self.clientIPLineEdit.setText(self.myaddr)
        ######################################################################################
        self.clientIPLineEdit.setText("47.102.36.187")  # 输入自定义IP
        # IP Label (20, 40) default size
        self.clientPortLabel = QLabel(self)  # port标签
        self.clientPortLabel.move(190, 50)
        self.clientPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.clientPortLineEdit = QLineEdit(self)
        self.clientPortLineEdit.move(220, 58)
        self.clientPortLineEdit.resize(120, 15)
        self.clientPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.clientPortLineEdit.setText('8082')
        ##==============================================第一层按钮组件

        ##=========================================================第二层按钮组件
        # 参数设置
        # 车辆长度 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(40, 85)
        self.lengthOfCarLabel.setText('车辆长度:')
        # 车辆长度 Edit  (50, 18) (120, 15)
        self.lengthOfCarLienEdit = QLineEdit(self)
        self.lengthOfCarLienEdit.move(95, 91)
        self.lengthOfCarLienEdit.resize(50, 15)
        self.lengthOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.lengthOfCarLienEdit.setText('1')
        # 车辆长度单位 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(150, 85)
        self.lengthOfCarLabel.setText('m')

        # 车辆重量 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(210, 85)
        self.weightOfCarLabel.setText('车辆重量:')
        # 车辆重量 Edit  (50, 18) (120, 15)
        self.weightOfCarLienEdit = QLineEdit(self)
        self.weightOfCarLienEdit.move(265, 91)
        self.weightOfCarLienEdit.resize(50, 15)
        self.weightOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.weightOfCarLienEdit.setText('1')
        # 车辆重量单位 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(320, 85)
        self.weightOfCarLabel.setText('kg')

        # 最大速度 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(40, 110)
        self.maxVelocityOfCarLabel.setText('最大速度:')
        # 最大速度 Edit  (50, 18) (120, 15)
        self.maxVelocityOfCarLienEdit = QLineEdit(self)
        self.maxVelocityOfCarLienEdit.move(95, 116)
        self.maxVelocityOfCarLienEdit.resize(50, 15)
        self.maxVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxVelocityOfCarLienEdit.setText('1')
        # 最大速度单位 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(150, 110)
        self.maxVelocityOfCarLabel.setText('m/s')

        # 最小速度 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(210, 110)
        self.minVelocityOfCarLabel.setText('最小速度:')
        # 最小速度 Edit  (50, 18) (120, 15)
        self.minVelocityOfCarLienEdit = QLineEdit(self)
        self.minVelocityOfCarLienEdit.move(265, 116)
        self.minVelocityOfCarLienEdit.resize(50, 15)
        self.minVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.minVelocityOfCarLienEdit.setText('1')
        # 最小速度单位 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(320, 110)
        self.minVelocityOfCarLabel.setText('m/s')

        # 最大加速度 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(30, 135)
        self.maxAccelationOfCarLabel.setText('最大加速度:')
        # 最大加速度 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 141)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 最大加速度单位 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 135)
        self.maxAccelationOfCarLabel.setText('m/s^2')

        # 最大减速度 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(200, 135)
        self.maxDecelerationOfCarLabel.setText('最大减速度:')
        # 最大减速度 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 141)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 最大减速度单位 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 135)
        self.maxDecelerationOfCarLabel.setText('m/s^2')

        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(40, 160)
        self.maxAccelationOfCarLabel.setText('转动惯量:')
        # 转动惯量 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 166)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 160)
        self.maxAccelationOfCarLabel.setText('kg·m^2')

        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(235, 160)
        self.maxDecelerationOfCarLabel.setText('轴距:')
        # 轴距 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 166)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 160)
        self.maxDecelerationOfCarLabel.setText('m')





        ##=========================================================第二层按钮组件


        ##======================================================第三层按钮组件
        # 数据显示部分
        # 车辆ID
        self.IDLabel = QLabel(self)
        self.IDLabel.move(65, 190)
        self.IDLabel.setText('车辆编号:')
        self.IDChangeLabel = QLabel(self)
        self.IDChangeLabel.move(120, 190)
        self.IDChangeLabel.setText('xx')

        # 左轮速度
        self.L2vLabel = QLabel(self)
        self.L2vLabel.move(65, 210)
        self.L2vLabel.setText('左轮电机速度:')
        self.L2vChangeLabel = QLabel(self)
        self.L2vChangeLabel.move(145, 210)
        self.L2vChangeLabel.setText('xxxx')
        self.L2vUnitLabel = QLabel(self)
        self.L2vUnitLabel.move(170, 210)
        self.L2vUnitLabel.setText('cm/s')

        # 右轮速度
        self.R2vLabel = QLabel(self)
        self.R2vLabel.move(210, 210)
        self.R2vLabel.setText('右轮电机速度:')
        self.R2vChangeLabel = QLabel(self)
        self.R2vChangeLabel.move(290, 210)
        self.R2vChangeLabel.setText('xxxxx')
        self.R2vUnitLabel = QLabel(self)
        self.R2vUnitLabel.move(320, 210)
        self.R2vUnitLabel.setText('cm/s')

        # 舵机转角
        self.angleLabel = QLabel(self)
        self.angleLabel.move(210, 230)
        self.angleLabel.setText('转向角度:')
        self.angleChangeLabel = QLabel(self)
        self.angleChangeLabel.move(265, 230)
        self.angleChangeLabel.setText('xxxx')
        self.angleUnitLabel = QLabel(self)
        self.angleUnitLabel.move(295, 230)
        self.angleUnitLabel.setText('°')

        # 车辆状态
        self.LPWMLabel = QLabel(self)
        self.LPWMLabel.move(210, 190)
        self.LPWMLabel.setText('车辆状态:')
        self.LPWMChangeLabel = QLabel(self)
        self.LPWMChangeLabel.move(265, 190)
        self.LPWMChangeLabel.setText('xxxx')

        # 电池电压
        self.RPWMLabel = QLabel(self)
        self.RPWMLabel.move(65, 230)
        self.RPWMLabel.setText('电池电压:')
        self.RPWMChangeLabel = QLabel(self)
        self.RPWMChangeLabel.move(120, 230)
        self.RPWMChangeLabel.setText('xxxx')
        self.RPWMUnitLabel = QLabel(self)
        self.RPWMUnitLabel.move(150, 230)
        self.RPWMUnitLabel.setText('v')

        # 横向加速度
        self.AyLabel = QLabel(self)
        self.AyLabel.move(65, 250)
        self.AyLabel.setText('横向加速度:')
        self.AyChangeLabel = QLabel(self)
        self.AyChangeLabel.move(135, 250)
        self.AyChangeLabel.setText('xxxx')
        self.AyUnitLabel = QLabel(self)
        self.AyUnitLabel.move(165, 250)
        self.AyUnitLabel.setText('m/s^2')

        # 横摆角速度
        self.YawLabel = QLabel(self)
        self.YawLabel.move(210, 250)
        self.YawLabel.setText('横摆角速度:')
        self.YawChangeLabel = QLabel(self)
        self.YawChangeLabel.move(280, 250)
        self.YawChangeLabel.setText('xxxx')
        self.YawUnitLabel = QLabel(self)
        self.YawUnitLabel.move(310, 250)
        self.YawUnitLabel.setText('°/s')

        # 电机转矩
        self.TnLabel = QLabel(self)
        self.TnLabel.move(210, 270)
        self.TnLabel.setText('电机转矩:')
        self.TnChangeLabel = QLabel(self)
        self.TnChangeLabel.move(265, 270)
        self.TnChangeLabel.setText('xxxx')
        self.TnUnitLabel = QLabel(self)
        self.TnUnitLabel.move(295, 270)
        self.TnUnitLabel.setText('N·m')

        # 横向速度
        self.VyLabel = QLabel(self)
        self.VyLabel.move(65, 270)
        self.VyLabel.setText('横向速度:')
        self.VyChangeLabel = QLabel(self)
        self.VyChangeLabel.move(125, 270)
        self.VyChangeLabel.setText('xxxx')
        self.VyUnitLabel = QLabel(self)
        self.VyUnitLabel.move(155, 270)
        self.VyUnitLabel.setText('m/s')

        # 当前经度
        self.lngLabel = QLabel(self)
        self.lngLabel.move(65, 300)
        self.lngLabel.setText('当前经度:')
        self.lngChangeLabel = QLabel(self)
        self.lngChangeLabel.move(120, 300)
        self.lngChangeLabel.setText('xxxx')
        self.lngUnitLabel = QLabel(self)
        self.lngUnitLabel.move(250, 300)
        self.lngUnitLabel.setText('°')

        # 当前纬度
        self.latLabel = QLabel(self)
        self.latLabel.move(65, 320)
        self.latLabel.setText('当前纬度:')
        self.latChangeLabel = QLabel(self)
        self.latChangeLabel.move(120, 320)
        self.latChangeLabel.setText('xxxx')
        # self.latChangeLabel.setGeometry(QRect(328, 240, 329, 27 * 4))
        # self.latChangeLabel.setWordWrap(True)
        # self.latChangeLabel.setAlignment(Qt.AlignTop)
        self.latUnitLabel = QLabel(self)
        self.latUnitLabel.move(250, 320)
        self.latUnitLabel.setText('°')



        ## 下位机上传的图像信息
        self.angleLabel = QLabel(self)
        self.angleLabel.move(400, 150)
        self.angleLabel.setText('图像:')

        pix = QPixmap('background.jpg')
        self.lb1 = QLabel(self)
        self.lb1.setGeometry(450, 5, 400, 200)  # x1 x2 x3 x4,从（x1,x2）开始显示一个x3长x4宽的矩形
        self.lb1.setPixmap(QPixmap('background.jpg'))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小

        self.lb1.setStyleSheet("border: 2px solid red")



        # 方法三
        self.angleLabel = QLabel(self)  # 标签
        self.angleLabel.move(390, 350)
        self.angleLabel.setText('导航图像:')
        # 调用Mapwindow函数，建立一个他的对象
        SettingBox_Map1 = QGroupBox("导航地图")
        Map1 = Map_load2()
        v_map1_layout = QVBoxLayout()
        v_map1_layout.addWidget(Map1)
        v_map1_layout.setContentsMargins(450, 200, 50, 50)  # 左上右下距离边框的长度
        self.setLayout(v_map1_layout)
        # QApplication.processEvents()  # 使得图像界面可以实时更新


        # 状态栏显示
        # self.setGeometry(100, 100, 370, 550)
        self.setGeometry(100, 100, 900, 450)
        self.setWindowTitle('First')
        self.show()

    def slot_btn_function_ID1(self):
        # self.hide()
        self.f1 = First_ID1()
        self.f1.show()

    ## 响应槽函数
    def mapshow(self, text):
        map = (Map().add(text, [list(z) for z in zip(Faker.provinces, Faker.values())], text)
               .set_global_opts(title_opts=opts.TitleOpts(title="map")))
        map.render('BD_map.html')  # 读取对应车辆的百度地图API程序
        # self.browser.load(QUrl(QFileInfo("file:///E:/pycharm_project/TCP%2010%2025/BD_map.html").absoluteFilePath()))
        self.browser.load(QUrl(QFileInfo("BD_map.html").absoluteFilePath()))
        print("更新BD地图============")
        if text in self.knowledge:
            self.knowledge_label.setText(self.knowledge[text])
        else:
            self.knowledge_label.setText('')

    def IDchange(self,ID):  # 更新车辆ID的槽函数
        self.IDChangeLabel.setText(ID)

    def Statechange(self,State):  # 更新车辆状态
        self.StatechangeLable.setText(str(State))


    def L2vchange(self, L2v):  # 更新左轮电机转速的槽函数
        self.L2vChangeLabel.setText(str(L2v))

    def R2vchange(self, R2v):  # 更新右轮电机转速的槽函数
        self.R2vChangeLabel.setText(str(R2v))
    def anglechange(self, angle):  # 更新转向角度的槽函数
        self.angleChangeLabel.setText(str(angle))

    def Uchange(self,U):
        self.UchangeLabel.setText(U)

    def LPWMchange(self, LPWM):
        self.LPWMChangeLabel.setText(str(LPWM))

    def RPWMchange(self,RPWM):
        self.RPWMChangeLabel.setText(str(RPWM))

    def Aychange(self,Ay):
        self.AyChangeLabel.setText(str(Ay))

    def Yawchange(self,Yaw):
        self.YawChangeLabel.setText(str(Yaw))

    def Tnchange(self,Tn):
        self.TnChangeLabel.setText(str(Tn))

    def Vychange(self,Vy):
        self.VyChangeLabel.setText(str(Vy))


    def lngChange(self,lng):
        self.lngChangeLabel.setText(str(lng))

    def latChange(self,lat):
        self.latChangeLabel.setText(str(lat))


    # 修改显示的图像
    def QPixmapchange(self,Image):
        self.lb1.setPixmap(QPixmap(str(Image)))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
    # 修改显示的图像


    def start(self):  # start按钮的槽函数
        global startFlag
        startFlag = 1



    def listenToClient(self):  # 点击Listen后的响应事件
        localIP = self.serverIPLineEdit.text()  # 定义Listener类中的属性值
        localPort = self.serverPortLineEdit.text()
        serverIP = self.clientIPLineEdit.text() 
        serverPort = self.clientPortLineEdit.text()
        length = self.lengthOfCarLienEdit.text()
        weight = self.weightOfCarLienEdit.text()
        maxV = self.maxVelocityOfCarLienEdit.text()
        minV = self.minVelocityOfCarLienEdit.text()
        maxA = self.maxAccelationOfCarLienEdit.text()
        maxD = self.maxDecelerationOfCarLienEdit.text()
        self._thread = Listener_ID1(localIP, int(localPort), serverIP, int(serverPort),
                                int(length), int(weight), int(maxV),
                                int(minV), int(maxA), int(maxD))  # 定义一个Listener的对象
        self._thread.sigID.connect(self.IDchange)  # 调用修改参数方法，实时传输显示下位机传输的数据
        self._thread.sigRPWM.connect(self.RPWMchange)
        self._thread.sigLPWM.connect(self.LPWMchange)
        self._thread.sigL2v.connect(self.L2vchange)
        self._thread.sigR2v.connect(self.R2vchange)
        self._thread.sigangle.connect(self.anglechange)
        self._thread.sigImage.connect(self.QPixmapchange)  # 更新显示的图片

        self._thread.sigAy.connect(self.Aychange)
        self._thread.sigYaw.connect(self.Yawchange)
        self._thread.sigTn.connect(self.Tnchange)
        self._thread.sigVy.connect(self.Vychange)

        self._thread.siglat.connect(self.latChange)
        self._thread.siglng.connect(self.lngChange)  # 更新当前经纬度数据


        self._thread.start()  # 执行Litener类中的run方法
        self.listenButton.setText('Listening')  # 开始执行监听后标识为“正在监听”




    def askstate(self):  # askstate按钮的槽函数
        global askstateFlag_ID1
        askstateFlag_ID1 = 1
        print('askstateFlag_ID1_change_to:', askstateFlag_ID1)

    def askimage(self):  # askimage按钮的槽函数
        global askimageFlag_ID1
        askimageFlag_ID1 = 1
        print('askimageFlag_ID1_change_to:', askimageFlag_ID1)

        # self._thread = Image_listen()
        # self._thread.start()

    def send(self):  # send按钮的槽函数
        global sendFlag_ID1
        sendFlag_ID1 = 1
        print('sendFlag_ID1_change_to:', sendFlag_ID1)




    def closeEvent(self, event):  # GUI窗口右上角关闭按钮的槽函数
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()  #第一辆车

# 第二辆车
class Second_ID2(QWidget):

    serverSig = pyqtSignal()  # 申明无参数信号

    def __init__(self):  # 初始化
        self.myname = socket.getfqdn(socket.gethostname())  # gethostname() ： 返回本地主机的标准主机名。
        self.myaddr = socket.gethostbyname(self.myname)  # gethostbyname()：用域名或主机名获取IP地址
        super(Second_ID2, self).__init__()  # 继承父类的属性和方法
        self.initUI()  # 调用自己的方法


    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)

        if int(i) == 1:  ## 传过来的是str型参数，转换成int型才可
            # self.hide()
            self.f1 = First_ID1()
            self.f1.show()

        elif int(i) == 3:
            # self.hide()
            self.t3 = Third_ID3()
            self.t3.show()

        elif int(i) == 4:
            # self.hide()
            self.f4 = Forth_ID4()
            self.f4.show()

        elif int(i) == 5:
            # self.hide()
            self.f5 = Fifth_ID5()
            self.f5.show()

        elif int(i) == 6:
            # self.hide()
            self.s6 = Sixth_ID6()
            self.s6.show()

        elif int(i) == 7:
            # self.hide()
            self.s7 = Seventh_ID7()
            self.s7.show()

        elif int(i) == 8:
            # self.hide()
            self.e8 = Eighth_ID8()
            self.e8.show()

        elif int(i) == 9:
            # self.hide()
            self.n9 = Ninth_ID9()
            self.n9.show()

        elif int(i) == 10:
            # self.hide()
            self.t10 = Tenth_ID10()
            self.t10.show()

    def initUI(self):



        self.btn = QPushButton('jump to FirstUI', self)  # 用来返回到第一个界面
        self.btn.setGeometry(350, 50, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function)

        self.cb = QComboBox(self)
        self.cb.move(350, 10)
        self.cb.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容

        ##=======================================================第四层按钮组件
        # 退出按钮
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(QCoreApplication.instance().quit)  # 信号与槽，槽可以是QT内置的槽也可以是python内置方法
        self.quitButton.resize(self.quitButton.sizeHint())  # sizeHint()提供一个推荐大小
        self.quitButton.move(50, 360)  # 放置位子
        # 监听按钮
        self.listenButton = QPushButton('Listen', self)
        self.listenButton.setCheckable(True)  # 可以点击
        self.listenButton.clicked.connect(self.listenToClient)  # 链接到槽方法listenToClient,开始监听
        self.listenButton.resize(self.quitButton.sizeHint())  # 和quitButton按钮一样大
        self.listenButton.move(250, 360)  # 改变大小并移动

        #  开始按钮
        self.startButton = QPushButton('Start', self)
        self.startButton.setCheckable(True)
        self.startButton.clicked.connect(self.start)  # self.StartFlag = 1,表示开始向下位机发送数据
        self.startButton.resize(self.quitButton.sizeHint())
        self.startButton.move(50, 400)

        #  发送第一组数据按钮
        self.sendButton = QPushButton('Send', self)
        self.sendButton.setCheckable(True)
        self.sendButton.clicked.connect(self.send)  # 发送第一组经纬度
        self.sendButton.resize(self.quitButton.sizeHint())
        self.sendButton.move(250, 400)

        #  请求车辆的状态
        self.stateButton = QPushButton('AskState', self)
        self.stateButton.setCheckable(True)
        self.stateButton.clicked.connect(self.askstate)  # 发送停止信号 “ST”
        self.stateButton.resize(self.quitButton.sizeHint())
        self.stateButton.move(150, 360)

        #  请求车辆的图像
        self.imageButton = QPushButton('AskImage', self)
        self.imageButton.setCheckable(True)
        self.imageButton.clicked.connect(self.askimage)  # 发送停止信号 “ST”
        self.imageButton.resize(self.quitButton.sizeHint())
        self.imageButton.move(150, 400)

        #  请求百度地图
        # self.imageButton = QPushButton('BD_map', self)
        # self.imageButton.setCheckable(True)
        # self.imageButton.clicked.connect(self.mapshow)  # 发送显示地图指令
        # self.imageButton.resize(self.quitButton.sizeHint())
        # self.imageButton.move(150, 320)
        ##====================================================第四层按钮组件


        ##==============================================第一层按钮组件
        # 服务器角色 控件布局
        # 上位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(85, 10)
        self.carIPLabel.setText('上位机')
        # IP Label (20, 20) default size
        self.serverIPLabel = QLabel(self)
        self.serverIPLabel.move(20, 30)
        self.serverIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.serverIPLineEdit = QLineEdit(self)
        self.serverIPLineEdit.move(50, 38)
        self.serverIPLineEdit.resize(120, 15)
        self.serverIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverIPLineEdit.setText(self.myaddr)  # 本地主机的IP
        # IP Label (20, 40) default size
        self.serverPortLabel = QLabel(self)
        self.serverPortLabel.move(20, 50)
        self.serverPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.serverPortLineEdit = QLineEdit(self)
        self.serverPortLineEdit.move(50, 58)
        self.serverPortLineEdit.resize(120, 15)
        self.serverPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverPortLineEdit.setText('7890')  # 自己选取的端口号

        # 客户端角色 控件布局
        # 下位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(255, 10)
        self.carIPLabel.setText('阿里云')
        # IP Label (20, 20) default size
        self.clientIPLabel = QLabel(self)  # IP标签
        self.clientIPLabel.move(190, 30)
        self.clientIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.clientIPLineEdit = QLineEdit(self)  # IP显示文本框
        self.clientIPLineEdit.move(220, 38)
        self.clientIPLineEdit.resize(120, 15)
        self.clientIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        # self.clientIPLineEdit.setText(self.myaddr)
        ######################################################################################
        self.clientIPLineEdit.setText("47.102.36.187")  # 输入自定义IP
        # IP Label (20, 40) default size
        self.clientPortLabel = QLabel(self)  # port标签
        self.clientPortLabel.move(190, 50)
        self.clientPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.clientPortLineEdit = QLineEdit(self)
        self.clientPortLineEdit.move(220, 58)
        self.clientPortLineEdit.resize(120, 15)
        self.clientPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.clientPortLineEdit.setText('8084')
        ##==============================================第一层按钮组件

        ##=========================================================第二层按钮组件
        # 参数设置
        # 车辆长度 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(40, 85)
        self.lengthOfCarLabel.setText('车辆长度:')
        # 车辆长度 Edit  (50, 18) (120, 15)
        self.lengthOfCarLienEdit = QLineEdit(self)
        self.lengthOfCarLienEdit.move(95, 91)
        self.lengthOfCarLienEdit.resize(50, 15)
        self.lengthOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.lengthOfCarLienEdit.setText('1')
        # 车辆长度单位 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(150, 85)
        self.lengthOfCarLabel.setText('m')

        # 车辆重量 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(210, 85)
        self.weightOfCarLabel.setText('车辆重量:')
        # 车辆重量 Edit  (50, 18) (120, 15)
        self.weightOfCarLienEdit = QLineEdit(self)
        self.weightOfCarLienEdit.move(265, 91)
        self.weightOfCarLienEdit.resize(50, 15)
        self.weightOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.weightOfCarLienEdit.setText('1')
        # 车辆重量单位 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(320, 85)
        self.weightOfCarLabel.setText('kg')

        # 最大速度 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(40, 110)
        self.maxVelocityOfCarLabel.setText('最大速度:')
        # 最大速度 Edit  (50, 18) (120, 15)
        self.maxVelocityOfCarLienEdit = QLineEdit(self)
        self.maxVelocityOfCarLienEdit.move(95, 116)
        self.maxVelocityOfCarLienEdit.resize(50, 15)
        self.maxVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxVelocityOfCarLienEdit.setText('1')
        # 最大速度单位 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(150, 110)
        self.maxVelocityOfCarLabel.setText('m/s')

        # 最小速度 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(210, 110)
        self.minVelocityOfCarLabel.setText('最小速度:')
        # 最小速度 Edit  (50, 18) (120, 15)
        self.minVelocityOfCarLienEdit = QLineEdit(self)
        self.minVelocityOfCarLienEdit.move(265, 116)
        self.minVelocityOfCarLienEdit.resize(50, 15)
        self.minVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.minVelocityOfCarLienEdit.setText('1')
        # 最小速度单位 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(320, 110)
        self.minVelocityOfCarLabel.setText('m/s')

        # 最大加速度 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(30, 135)
        self.maxAccelationOfCarLabel.setText('最大加速度:')
        # 最大加速度 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 141)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 最大加速度单位 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 135)
        self.maxAccelationOfCarLabel.setText('m/s^2')

        # 最大减速度 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(200, 135)
        self.maxDecelerationOfCarLabel.setText('最大减速度:')
        # 最大减速度 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 141)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 最大减速度单位 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 135)
        self.maxDecelerationOfCarLabel.setText('m/s^2')

        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(40, 160)
        self.maxAccelationOfCarLabel.setText('转动惯量:')
        # 转动惯量 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 166)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 160)
        self.maxAccelationOfCarLabel.setText('kg·m^2')

        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(235, 160)
        self.maxDecelerationOfCarLabel.setText('轴距:')
        # 轴距 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 166)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 160)
        self.maxDecelerationOfCarLabel.setText('m')





        ##=========================================================第二层按钮组件


        ##======================================================第三层按钮组件
        # 数据显示部分
        # 车辆ID
        self.IDLabel = QLabel(self)
        self.IDLabel.move(65, 190)
        self.IDLabel.setText('车辆编号:')
        self.IDChangeLabel = QLabel(self)
        self.IDChangeLabel.move(120, 190)
        self.IDChangeLabel.setText('xx')

        # 左轮速度
        self.L2vLabel = QLabel(self)
        self.L2vLabel.move(65, 210)
        self.L2vLabel.setText('左轮电机速度:')
        self.L2vChangeLabel = QLabel(self)
        self.L2vChangeLabel.move(145, 210)
        self.L2vChangeLabel.setText('xxxx')
        self.L2vUnitLabel = QLabel(self)
        self.L2vUnitLabel.move(170, 210)
        self.L2vUnitLabel.setText('cm/s')

        # 右轮速度
        self.R2vLabel = QLabel(self)
        self.R2vLabel.move(210, 210)
        self.R2vLabel.setText('右轮电机速度:')
        self.R2vChangeLabel = QLabel(self)
        self.R2vChangeLabel.move(290, 210)
        self.R2vChangeLabel.setText('xxxxx')
        self.R2vUnitLabel = QLabel(self)
        self.R2vUnitLabel.move(320, 210)
        self.R2vUnitLabel.setText('cm/s')

        # 舵机转角
        self.angleLabel = QLabel(self)
        self.angleLabel.move(210, 230)
        self.angleLabel.setText('转向角度:')
        self.angleChangeLabel = QLabel(self)
        self.angleChangeLabel.move(265, 230)
        self.angleChangeLabel.setText('xxxx')
        self.angleUnitLabel = QLabel(self)
        self.angleUnitLabel.move(295, 230)
        self.angleUnitLabel.setText('°')

        # 车辆状态
        self.LPWMLabel = QLabel(self)
        self.LPWMLabel.move(210, 190)
        self.LPWMLabel.setText('车辆状态:')
        self.LPWMChangeLabel = QLabel(self)
        self.LPWMChangeLabel.move(265, 190)
        self.LPWMChangeLabel.setText('xxxx')

        # 电池电压
        self.RPWMLabel = QLabel(self)
        self.RPWMLabel.move(65, 230)
        self.RPWMLabel.setText('电池电压:')
        self.RPWMChangeLabel = QLabel(self)
        self.RPWMChangeLabel.move(120, 230)
        self.RPWMChangeLabel.setText('xxxx')
        self.RPWMUnitLabel = QLabel(self)
        self.RPWMUnitLabel.move(150, 230)
        self.RPWMUnitLabel.setText('v')

        # 横向加速度
        self.AyLabel = QLabel(self)
        self.AyLabel.move(65, 250)
        self.AyLabel.setText('横向加速度:')
        self.AyChangeLabel = QLabel(self)
        self.AyChangeLabel.move(135, 250)
        self.AyChangeLabel.setText('xxxx')
        self.AyUnitLabel = QLabel(self)
        self.AyUnitLabel.move(165, 250)
        self.AyUnitLabel.setText('m/s^2')

        # 横摆角速度
        self.YawLabel = QLabel(self)
        self.YawLabel.move(210, 250)
        self.YawLabel.setText('横摆角速度:')
        self.YawChangeLabel = QLabel(self)
        self.YawChangeLabel.move(280, 250)
        self.YawChangeLabel.setText('xxxx')
        self.YawUnitLabel = QLabel(self)
        self.YawUnitLabel.move(310, 250)
        self.YawUnitLabel.setText('°/s')

        # 电机转矩
        self.TnLabel = QLabel(self)
        self.TnLabel.move(210, 270)
        self.TnLabel.setText('电机转矩:')
        self.TnChangeLabel = QLabel(self)
        self.TnChangeLabel.move(265, 270)
        self.TnChangeLabel.setText('xxxx')
        self.TnUnitLabel = QLabel(self)
        self.TnUnitLabel.move(295, 270)
        self.TnUnitLabel.setText('N·m')

        # 横向速度
        self.VyLabel = QLabel(self)
        self.VyLabel.move(65, 270)
        self.VyLabel.setText('横向速度:')
        self.VyChangeLabel = QLabel(self)
        self.VyChangeLabel.move(125, 270)
        self.VyChangeLabel.setText('xxxx')
        self.VyUnitLabel = QLabel(self)
        self.VyUnitLabel.move(155, 270)
        self.VyUnitLabel.setText('m/s')

        # 当前经度
        self.lngLabel = QLabel(self)
        self.lngLabel.move(65, 300)
        self.lngLabel.setText('当前经度:')
        self.lngChangeLabel = QLabel(self)
        self.lngChangeLabel.move(120, 300)
        self.lngChangeLabel.setText('xxxx')
        self.lngUnitLabel = QLabel(self)
        self.lngUnitLabel.move(250, 300)
        self.lngUnitLabel.setText('°')

        # 当前纬度
        self.latLabel = QLabel(self)
        self.latLabel.move(65, 320)
        self.latLabel.setText('当前纬度:')
        self.latChangeLabel = QLabel(self)
        self.latChangeLabel.move(120, 320)
        self.latChangeLabel.setText('xxxx')
        # self.latChangeLabel.setGeometry(QRect(328, 240, 329, 27 * 4))
        # self.latChangeLabel.setWordWrap(True)
        # self.latChangeLabel.setAlignment(Qt.AlignTop)
        self.latUnitLabel = QLabel(self)
        self.latUnitLabel.move(250, 320)
        self.latUnitLabel.setText('°')



        ## 下位机上传的图像信息
        self.angleLabel = QLabel(self)
        self.angleLabel.move(400, 150)
        self.angleLabel.setText('图像:')

        pix = QPixmap('background.jpg')
        self.lb1 = QLabel(self)
        self.lb1.setGeometry(450, 5, 400, 200)  # x1 x2 x3 x4,从（x1,x2）开始显示一个x3长x4宽的矩形
        self.lb1.setPixmap(QPixmap('background.jpg'))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
        self.lb1.setStyleSheet("border: 2px solid red")


        # 方法三
        self.angleLabel = QLabel(self)  # 标签
        self.angleLabel.move(390, 350)
        self.angleLabel.setText('导航图像:')
        # 调用Mapwindow函数，建立一个他的对象
        SettingBox_Map1 = QGroupBox("导航地图")
        Map1 = Map_load2()
        v_map1_layout = QVBoxLayout()
        v_map1_layout.addWidget(Map1)
        v_map1_layout.setContentsMargins(450, 200, 50, 50)  # 左上右下距离边框的长度
        self.setLayout(v_map1_layout)
        # QApplication.processEvents()  # 使得图像界面可以实时更新


        # 状态栏显示
        # self.setGeometry(100, 100, 370, 550)
        self.setGeometry(100, 100, 900, 450)
        self.setWindowTitle('Second')
        self.show()

    def slot_btn_function(self):
        # self.hide()
        self.f1 = First_ID1()
        self.f1.show()



    ## 响应槽函数
    def mapshow(self, text):
        map = (Map().add(text, [list(z) for z in zip(Faker.provinces, Faker.values())], text)
               .set_global_opts(title_opts=opts.TitleOpts(title="map")))
        map.render('BD_map2.html')  # 读取对应车辆的百度地图API程序
        # self.browser.load(QUrl(QFileInfo("file:///E:/pycharm_project/TCP%2010%2025/BD_map.html").absoluteFilePath()))
        self.browser.load(QUrl(QFileInfo("BD_map2.html").absoluteFilePath()))
        print("更新BD地图============")
        if text in self.knowledge:
            self.knowledge_label.setText(self.knowledge[text])
        else:
            self.knowledge_label.setText('')

    def IDchange(self,ID):  # 更新车辆ID的槽函数
        self.IDChangeLabel.setText(ID)

    def Statechange(self,State):  # 更新车辆状态
        self.StatechangeLable.setText(str(State))


    def L2vchange(self, L2v):  # 更新左轮电机转速的槽函数
        self.L2vChangeLabel.setText(str(L2v))

    def R2vchange(self, R2v):  # 更新右轮电机转速的槽函数
        self.R2vChangeLabel.setText(str(R2v))
    def anglechange(self, angle):  # 更新转向角度的槽函数
        self.angleChangeLabel.setText(str(angle))

    def Uchange(self,U):
        self.UchangeLabel.setText(U)

    def LPWMchange(self, LPWM):
        self.LPWMChangeLabel.setText(str(LPWM))

    def RPWMchange(self,RPWM):
        self.RPWMChangeLabel.setText(str(RPWM))

    def Aychange(self,Ay):
        self.AyChangeLabel.setText(str(Ay))

    def Yawchange(self,Yaw):
        self.YawChangeLabel.setText(str(Yaw))

    def Tnchange(self,Tn):
        self.TnChangeLabel.setText(str(Tn))

    def Vychange(self,Vy):
        self.VyChangeLabel.setText(str(Vy))


    def lngChange(self,lng):
        self.lngChangeLabel.setText(str(lng))

    def latChange(self,lat):
        self.latChangeLabel.setText(str(lat))


    # 修改显示的图像
    def QPixmapchange(self,Image):
        self.lb1.setPixmap(QPixmap(str(Image)))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
    # 修改显示的图像


    def start(self):  # start按钮的槽函数
        global startFlag
        startFlag = 1



    def listenToClient(self):  # 点击Listen后的响应事件
        localIP = self.serverIPLineEdit.text()  # 定义Listener类中的属性值
        localPort = self.serverPortLineEdit.text()
        serverIP = self.clientIPLineEdit.text()
        serverPort = self.clientPortLineEdit.text()
        length = self.lengthOfCarLienEdit.text()
        weight = self.weightOfCarLienEdit.text()
        maxV = self.maxVelocityOfCarLienEdit.text()
        minV = self.minVelocityOfCarLienEdit.text()
        maxA = self.maxAccelationOfCarLienEdit.text()
        maxD = self.maxDecelerationOfCarLienEdit.text()
        self._thread = Listener_ID2(localIP, int(localPort), serverIP, int(serverPort),
                                int(length), int(weight), int(maxV),
                                int(minV), int(maxA), int(maxD))  # 定义一个Listener的对象
        self._thread.sigID_ID2.connect(self.IDchange)  # 调用修改参数方法，实时传输显示下位机传输的数据
        self._thread.sigRPWM_ID2.connect(self.RPWMchange)
        self._thread.sigLPWM_ID2.connect(self.LPWMchange)
        self._thread.sigL2v_ID2.connect(self.L2vchange)
        self._thread.sigR2v_ID2.connect(self.R2vchange)
        self._thread.sigangle_ID2.connect(self.anglechange)
        self._thread.sigImage_ID2.connect(self.QPixmapchange)  # 更新显示的图片

        self._thread.sigAy_ID2.connect(self.Aychange)
        self._thread.sigYaw_ID2.connect(self.Yawchange)
        self._thread.sigTn_ID2.connect(self.Tnchange)
        self._thread.sigVy_ID2.connect(self.Vychange)

        self._thread.siglat_ID2.connect(self.latChange)
        self._thread.siglng_ID2.connect(self.lngChange)  # 更新当前经纬度数据


        self._thread.start()  # 执行Litener类中的run方法
        self.listenButton.setText('Listening')  # 开始执行监听后标识为“正在监听”




    def askstate(self):  # askstate按钮的槽函数
        global askstateFlag_ID2
        askstateFlag_ID2 = 1
        print('askstateFlag_ID2_change_to:', askstateFlag_ID2)

    def askimage(self):  # askimage按钮的槽函数
        global askimageFlag_ID2
        askimageFlag_ID2 = 1
        print('askimageFlag_ID2_change_to:', askimageFlag_ID2)

        # self._thread = Image_listen()
        # self._thread.start()

    def send(self):  # send按钮的槽函数
        global sendFlag_ID2
        sendFlag_ID2 = 1
        print('sendFlag_ID2_change_to:', sendFlag_ID2)




    def closeEvent(self, event):  # GUI窗口右上角关闭按钮的槽函数
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# 第三辆车
class Third_ID3(QWidget):

    serverSig = pyqtSignal()  # 申明无参数信号

    def __init__(self):  # 初始化
        self.myname = socket.getfqdn(socket.gethostname())  # gethostname() ： 返回本地主机的标准主机名。
        self.myaddr = socket.gethostbyname(self.myname)  # gethostbyname()：用域名或主机名获取IP地址
        super(Third_ID3, self).__init__()  # 继承父类的属性和方法
        self.initUI()  # 调用自己的方法

    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)

        if int(i) == 1:  ## 传过来的是str型参数，转换成int型才可
            # self.hide()
            self.f1 = First_ID1()
            self.f1.show()

        elif int(i) == 2:
            # self.hide()
            self.s2 = Second_ID2()
            self.s2.show()

        elif int(i) == 4:
            # self.hide()
            self.f4 = Forth_ID4()
            self.f4.show()

        elif int(i) == 5:
            # self.hide()
            self.f5 = Fifth_ID5()
            self.f5.show()

        elif int(i) == 6:
            # self.hide()
            self.s6 = Sixth_ID6()
            self.s6.show()

        elif int(i) == 7:
            # self.hide()
            self.s7 = Seventh_ID7()
            self.s7.show()

        elif int(i) == 8:
            # self.hide()
            self.e8 = Eighth_ID8()
            self.e8.show()

        elif int(i) == 9:
            # self.hide()
            self.n9 = Ninth_ID9()
            self.n9.show()

        elif int(i) == 10:
            # self.hide()
            self.t10 = Tenth_ID10()
            self.t10.show()

    def initUI(self):

        self.btn = QPushButton('jump to FirstUI', self)  # 用来返回到第一个界面
        self.btn.setGeometry(350, 50, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function)

        self.cb = QComboBox(self)
        self.cb.move(350, 10)
        self.cb.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容

        ##=======================================================第四层按钮组件
        # 退出按钮
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(QCoreApplication.instance().quit)  # 信号与槽，槽可以是QT内置的槽也可以是python内置方法
        self.quitButton.resize(self.quitButton.sizeHint())  # sizeHint()提供一个推荐大小
        self.quitButton.move(50, 360)  # 放置位子
        # 监听按钮
        self.listenButton = QPushButton('Listen', self)
        self.listenButton.setCheckable(True)  # 可以点击
        self.listenButton.clicked.connect(self.listenToClient)  # 链接到槽方法listenToClient,开始监听
        self.listenButton.resize(self.quitButton.sizeHint())  # 和quitButton按钮一样大
        self.listenButton.move(250, 360)  # 改变大小并移动

        #  开始按钮
        self.startButton = QPushButton('Start', self)
        self.startButton.setCheckable(True)
        self.startButton.clicked.connect(self.start)  # self.StartFlag = 1,表示开始向下位机发送数据
        self.startButton.resize(self.quitButton.sizeHint())
        self.startButton.move(50, 400)

        #  发送第一组数据按钮
        self.sendButton = QPushButton('Send', self)
        self.sendButton.setCheckable(True)
        self.sendButton.clicked.connect(self.send)  # 发送第一组经纬度
        self.sendButton.resize(self.quitButton.sizeHint())
        self.sendButton.move(250, 400)

        #  请求车辆的状态
        self.stateButton = QPushButton('AskState', self)
        self.stateButton.setCheckable(True)
        self.stateButton.clicked.connect(self.askstate)  # 发送停止信号 “ST”
        self.stateButton.resize(self.quitButton.sizeHint())
        self.stateButton.move(150, 360)

        #  请求车辆的图像
        self.imageButton = QPushButton('AskImage', self)
        self.imageButton.setCheckable(True)
        self.imageButton.clicked.connect(self.askimage)  # 发送停止信号 “ST”
        self.imageButton.resize(self.quitButton.sizeHint())
        self.imageButton.move(150, 400)

        #  请求百度地图
        # self.imageButton = QPushButton('BD_map', self)
        # self.imageButton.setCheckable(True)
        # self.imageButton.clicked.connect(self.mapshow)  # 发送显示地图指令
        # self.imageButton.resize(self.quitButton.sizeHint())
        # self.imageButton.move(150, 320)
        ##====================================================第四层按钮组件


        ##==============================================第一层按钮组件
        # 服务器角色 控件布局
        # 上位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(85, 10)
        self.carIPLabel.setText('上位机')
        # IP Label (20, 20) default size
        self.serverIPLabel = QLabel(self)
        self.serverIPLabel.move(20, 30)
        self.serverIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.serverIPLineEdit = QLineEdit(self)
        self.serverIPLineEdit.move(50, 38)
        self.serverIPLineEdit.resize(120, 15)
        self.serverIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverIPLineEdit.setText(self.myaddr)  # 本地主机的IP
        # IP Label (20, 40) default size
        self.serverPortLabel = QLabel(self)
        self.serverPortLabel.move(20, 50)
        self.serverPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.serverPortLineEdit = QLineEdit(self)
        self.serverPortLineEdit.move(50, 58)
        self.serverPortLineEdit.resize(120, 15)
        self.serverPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverPortLineEdit.setText('7890')  # 自己选取的端口号

        # 客户端角色 控件布局
        # 下位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(255, 10)
        self.carIPLabel.setText('阿里云')
        # IP Label (20, 20) default size
        self.clientIPLabel = QLabel(self)  # IP标签
        self.clientIPLabel.move(190, 30)
        self.clientIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.clientIPLineEdit = QLineEdit(self)  # IP显示文本框
        self.clientIPLineEdit.move(220, 38)
        self.clientIPLineEdit.resize(120, 15)
        self.clientIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        # self.clientIPLineEdit.setText(self.myaddr)
        ######################################################################################
        self.clientIPLineEdit.setText("47.102.36.187")  # 输入自定义IP
        # IP Label (20, 40) default size
        self.clientPortLabel = QLabel(self)  # port标签
        self.clientPortLabel.move(190, 50)
        self.clientPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.clientPortLineEdit = QLineEdit(self)
        self.clientPortLineEdit.move(220, 58)
        self.clientPortLineEdit.resize(120, 15)
        self.clientPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.clientPortLineEdit.setText('8086')
        ##==============================================第一层按钮组件

        ##=========================================================第二层按钮组件
        # 参数设置
        # 车辆长度 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(40, 85)
        self.lengthOfCarLabel.setText('车辆长度:')
        # 车辆长度 Edit  (50, 18) (120, 15)
        self.lengthOfCarLienEdit = QLineEdit(self)
        self.lengthOfCarLienEdit.move(95, 91)
        self.lengthOfCarLienEdit.resize(50, 15)
        self.lengthOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.lengthOfCarLienEdit.setText('1')
        # 车辆长度单位 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(150, 85)
        self.lengthOfCarLabel.setText('m')

        # 车辆重量 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(210, 85)
        self.weightOfCarLabel.setText('车辆重量:')
        # 车辆重量 Edit  (50, 18) (120, 15)
        self.weightOfCarLienEdit = QLineEdit(self)
        self.weightOfCarLienEdit.move(265, 91)
        self.weightOfCarLienEdit.resize(50, 15)
        self.weightOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.weightOfCarLienEdit.setText('1')
        # 车辆重量单位 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(320, 85)
        self.weightOfCarLabel.setText('kg')

        # 最大速度 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(40, 110)
        self.maxVelocityOfCarLabel.setText('最大速度:')
        # 最大速度 Edit  (50, 18) (120, 15)
        self.maxVelocityOfCarLienEdit = QLineEdit(self)
        self.maxVelocityOfCarLienEdit.move(95, 116)
        self.maxVelocityOfCarLienEdit.resize(50, 15)
        self.maxVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxVelocityOfCarLienEdit.setText('1')
        # 最大速度单位 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(150, 110)
        self.maxVelocityOfCarLabel.setText('m/s')

        # 最小速度 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(210, 110)
        self.minVelocityOfCarLabel.setText('最小速度:')
        # 最小速度 Edit  (50, 18) (120, 15)
        self.minVelocityOfCarLienEdit = QLineEdit(self)
        self.minVelocityOfCarLienEdit.move(265, 116)
        self.minVelocityOfCarLienEdit.resize(50, 15)
        self.minVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.minVelocityOfCarLienEdit.setText('1')
        # 最小速度单位 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(320, 110)
        self.minVelocityOfCarLabel.setText('m/s')

        # 最大加速度 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(30, 135)
        self.maxAccelationOfCarLabel.setText('最大加速度:')
        # 最大加速度 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 141)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 最大加速度单位 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 135)
        self.maxAccelationOfCarLabel.setText('m/s^2')

        # 最大减速度 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(200, 135)
        self.maxDecelerationOfCarLabel.setText('最大减速度:')
        # 最大减速度 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 141)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 最大减速度单位 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 135)
        self.maxDecelerationOfCarLabel.setText('m/s^2')

        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(40, 160)
        self.maxAccelationOfCarLabel.setText('转动惯量:')
        # 转动惯量 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 166)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 160)
        self.maxAccelationOfCarLabel.setText('kg·m^2')

        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(235, 160)
        self.maxDecelerationOfCarLabel.setText('轴距:')
        # 轴距 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 166)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 160)
        self.maxDecelerationOfCarLabel.setText('m')





        ##=========================================================第二层按钮组件


        ##======================================================第三层按钮组件
        # 数据显示部分
        # 车辆ID
        self.IDLabel = QLabel(self)
        self.IDLabel.move(65, 190)
        self.IDLabel.setText('车辆编号:')
        self.IDChangeLabel = QLabel(self)
        self.IDChangeLabel.move(120, 190)
        self.IDChangeLabel.setText('xx')

        # 左轮速度
        self.L2vLabel = QLabel(self)
        self.L2vLabel.move(65, 210)
        self.L2vLabel.setText('左轮电机速度:')
        self.L2vChangeLabel = QLabel(self)
        self.L2vChangeLabel.move(145, 210)
        self.L2vChangeLabel.setText('xxxx')
        self.L2vUnitLabel = QLabel(self)
        self.L2vUnitLabel.move(170, 210)
        self.L2vUnitLabel.setText('cm/s')

        # 右轮速度
        self.R2vLabel = QLabel(self)
        self.R2vLabel.move(210, 210)
        self.R2vLabel.setText('右轮电机速度:')
        self.R2vChangeLabel = QLabel(self)
        self.R2vChangeLabel.move(290, 210)
        self.R2vChangeLabel.setText('xxxxx')
        self.R2vUnitLabel = QLabel(self)
        self.R2vUnitLabel.move(320, 210)
        self.R2vUnitLabel.setText('cm/s')

        # 舵机转角
        self.angleLabel = QLabel(self)
        self.angleLabel.move(210, 230)
        self.angleLabel.setText('转向角度:')
        self.angleChangeLabel = QLabel(self)
        self.angleChangeLabel.move(265, 230)
        self.angleChangeLabel.setText('xxxx')
        self.angleUnitLabel = QLabel(self)
        self.angleUnitLabel.move(295, 230)
        self.angleUnitLabel.setText('°')

        # 车辆状态
        self.LPWMLabel = QLabel(self)
        self.LPWMLabel.move(210, 190)
        self.LPWMLabel.setText('车辆状态:')
        self.LPWMChangeLabel = QLabel(self)
        self.LPWMChangeLabel.move(265, 190)
        self.LPWMChangeLabel.setText('xxxx')

        # 电池电压
        self.RPWMLabel = QLabel(self)
        self.RPWMLabel.move(65, 230)
        self.RPWMLabel.setText('电池电压:')
        self.RPWMChangeLabel = QLabel(self)
        self.RPWMChangeLabel.move(120, 230)
        self.RPWMChangeLabel.setText('xxxx')
        self.RPWMUnitLabel = QLabel(self)
        self.RPWMUnitLabel.move(150, 230)
        self.RPWMUnitLabel.setText('v')

        # 横向加速度
        self.AyLabel = QLabel(self)
        self.AyLabel.move(65, 250)
        self.AyLabel.setText('横向加速度:')
        self.AyChangeLabel = QLabel(self)
        self.AyChangeLabel.move(135, 250)
        self.AyChangeLabel.setText('xxxx')
        self.AyUnitLabel = QLabel(self)
        self.AyUnitLabel.move(165, 250)
        self.AyUnitLabel.setText('m/s^2')

        # 横摆角速度
        self.YawLabel = QLabel(self)
        self.YawLabel.move(210, 250)
        self.YawLabel.setText('横摆角速度:')
        self.YawChangeLabel = QLabel(self)
        self.YawChangeLabel.move(280, 250)
        self.YawChangeLabel.setText('xxxx')
        self.YawUnitLabel = QLabel(self)
        self.YawUnitLabel.move(310, 250)
        self.YawUnitLabel.setText('°/s')

        # 电机转矩
        self.TnLabel = QLabel(self)
        self.TnLabel.move(210, 270)
        self.TnLabel.setText('电机转矩:')
        self.TnChangeLabel = QLabel(self)
        self.TnChangeLabel.move(265, 270)
        self.TnChangeLabel.setText('xxxx')
        self.TnUnitLabel = QLabel(self)
        self.TnUnitLabel.move(295, 270)
        self.TnUnitLabel.setText('N·m')

        # 横向速度
        self.VyLabel = QLabel(self)
        self.VyLabel.move(65, 270)
        self.VyLabel.setText('横向速度:')
        self.VyChangeLabel = QLabel(self)
        self.VyChangeLabel.move(125, 270)
        self.VyChangeLabel.setText('xxxx')
        self.VyUnitLabel = QLabel(self)
        self.VyUnitLabel.move(155, 270)
        self.VyUnitLabel.setText('m/s')

        # 当前经度
        self.lngLabel = QLabel(self)
        self.lngLabel.move(65, 300)
        self.lngLabel.setText('当前经度:')
        self.lngChangeLabel = QLabel(self)
        self.lngChangeLabel.move(120, 300)
        self.lngChangeLabel.setText('xxxx')
        self.lngUnitLabel = QLabel(self)
        self.lngUnitLabel.move(250, 300)
        self.lngUnitLabel.setText('°')

        # 当前纬度
        self.latLabel = QLabel(self)
        self.latLabel.move(65, 320)
        self.latLabel.setText('当前纬度:')
        self.latChangeLabel = QLabel(self)
        self.latChangeLabel.move(120, 320)
        self.latChangeLabel.setText('xxxx')
        # self.latChangeLabel.setGeometry(QRect(328, 240, 329, 27 * 4))
        # self.latChangeLabel.setWordWrap(True)
        # self.latChangeLabel.setAlignment(Qt.AlignTop)
        self.latUnitLabel = QLabel(self)
        self.latUnitLabel.move(250, 320)
        self.latUnitLabel.setText('°')



        ## 下位机上传的图像信息
        self.angleLabel = QLabel(self)
        self.angleLabel.move(400, 150)
        self.angleLabel.setText('图像:')

        pix = QPixmap('background.jpg')
        self.lb1 = QLabel(self)
        self.lb1.setGeometry(450, 5, 400, 200)  # x1 x2 x3 x4,从（x1,x2）开始显示一个x3长x4宽的矩形
        self.lb1.setPixmap(QPixmap('background.jpg'))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
        self.lb1.setStyleSheet("border: 2px solid red")


        # 方法三
        self.angleLabel = QLabel(self)  # 标签
        self.angleLabel.move(390, 350)
        self.angleLabel.setText('导航图像:')
        # 调用Mapwindow函数，建立一个他的对象
        SettingBox_Map1 = QGroupBox("导航地图")
        Map1 = Map_load2()
        v_map1_layout = QVBoxLayout()
        v_map1_layout.addWidget(Map1)
        v_map1_layout.setContentsMargins(450, 200, 50, 50)  # 左上右下距离边框的长度
        self.setLayout(v_map1_layout)
        # QApplication.processEvents()  # 使得图像界面可以实时更新


        # 状态栏显示
        # self.setGeometry(100, 100, 370, 550)
        self.setGeometry(100, 100, 900, 450)
        self.setWindowTitle('Third')
        self.show()

    def slot_btn_function(self):
        # self.hide()
        self.f1 = First_ID1()
        self.f1.show()



    ## 响应槽函数
    def mapshow(self, text):
        map = (Map().add(text, [list(z) for z in zip(Faker.provinces, Faker.values())], text)
               .set_global_opts(title_opts=opts.TitleOpts(title="map")))
        map.render('BD_map3.html')  # 读取对应车辆的百度地图API程序
        # self.browser.load(QUrl(QFileInfo("file:///E:/pycharm_project/TCP%2010%2025/BD_map.html").absoluteFilePath()))
        self.browser.load(QUrl(QFileInfo("BD_map3.html").absoluteFilePath()))
        print("更新BD地图============")
        if text in self.knowledge:
            self.knowledge_label.setText(self.knowledge[text])
        else:
            self.knowledge_label.setText('')

    def IDchange(self,ID):  # 更新车辆ID的槽函数
        self.IDChangeLabel.setText(ID)

    def Statechange(self,State):  # 更新车辆状态
        self.StatechangeLable.setText(str(State))


    def L2vchange(self, L2v):  # 更新左轮电机转速的槽函数
        self.L2vChangeLabel.setText(str(L2v))

    def R2vchange(self, R2v):  # 更新右轮电机转速的槽函数
        self.R2vChangeLabel.setText(str(R2v))
    def anglechange(self, angle):  # 更新转向角度的槽函数
        self.angleChangeLabel.setText(str(angle))

    def Uchange(self,U):
        self.UchangeLabel.setText(U)

    def LPWMchange(self, LPWM):
        self.LPWMChangeLabel.setText(str(LPWM))

    def RPWMchange(self,RPWM):
        self.RPWMChangeLabel.setText(str(RPWM))

    def Aychange(self,Ay):
        self.AyChangeLabel.setText(str(Ay))

    def Yawchange(self,Yaw):
        self.YawChangeLabel.setText(str(Yaw))

    def Tnchange(self,Tn):
        self.TnChangeLabel.setText(str(Tn))

    def Vychange(self,Vy):
        self.VyChangeLabel.setText(str(Vy))


    def lngChange(self,lng):
        self.lngChangeLabel.setText(str(lng))

    def latChange(self,lat):
        self.latChangeLabel.setText(str(lat))


    # 修改显示的图像
    def QPixmapchange(self,Image):
        self.lb1.setPixmap(QPixmap(str(Image)))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
    # 修改显示的图像


    def start(self):  # start按钮的槽函数
        global startFlag
        startFlag = 1



    def listenToClient(self):  # 点击Listen后的响应事件
        localIP = self.serverIPLineEdit.text()  # 定义Listener类中的属性值
        localPort = self.serverPortLineEdit.text()
        serverIP = self.clientIPLineEdit.text()
        serverPort = self.clientPortLineEdit.text()
        length = self.lengthOfCarLienEdit.text()
        weight = self.weightOfCarLienEdit.text()
        maxV = self.maxVelocityOfCarLienEdit.text()
        minV = self.minVelocityOfCarLienEdit.text()
        maxA = self.maxAccelationOfCarLienEdit.text()
        maxD = self.maxDecelerationOfCarLienEdit.text()
        self._thread = Listener_ID3(localIP, int(localPort), serverIP, int(serverPort),
                                int(length), int(weight), int(maxV),
                                int(minV), int(maxA), int(maxD))  # 定义一个Listener的对象
        self._thread.sigID_ID3.connect(self.IDchange)  # 调用修改参数方法，实时传输显示下位机传输的数据
        self._thread.sigRPWM_ID3.connect(self.RPWMchange)
        self._thread.sigLPWM_ID3.connect(self.LPWMchange)
        self._thread.sigL2v_ID3.connect(self.L2vchange)
        self._thread.sigR2v_ID3.connect(self.R2vchange)
        self._thread.sigangle_ID3.connect(self.anglechange)
        self._thread.sigImage_ID3.connect(self.QPixmapchange)  # 更新显示的图片

        self._thread.sigAy_ID3.connect(self.Aychange)
        self._thread.sigYaw_ID3.connect(self.Yawchange)
        self._thread.sigTn_ID3.connect(self.Tnchange)
        self._thread.sigVy_ID3.connect(self.Vychange)

        self._thread.siglat_ID3.connect(self.latChange)
        self._thread.siglng_ID3.connect(self.lngChange)  # 更新当前经纬度数据


        self._thread.start()  # 执行Litener类中的run方法
        self.listenButton.setText('Listening')  # 开始执行监听后标识为“正在监听”




    def askstate(self):  # askstate按钮的槽函数
        global askstateFlag_ID3
        askstateFlag_ID3 = 1
        print('askstateFlag_ID3_change_to:', askstateFlag_ID3)

    def askimage(self):  # askimage按钮的槽函数
        global askimageFlag_ID3
        askimageFlag_ID3 = 1
        print('askimageFlag_ID3_change_to:', askimageFlag_ID3)

        # self._thread = Image_listen()
        # self._thread.start()

    def send(self):  # send按钮的槽函数
        global sendFlag_ID3
        sendFlag_ID3 = 1
        print('sendFlag_ID3_change_to:', sendFlag_ID3)




    def closeEvent(self, event):  # GUI窗口右上角关闭按钮的槽函数
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# 第四辆车
class Forth_ID4(QWidget):

    serverSig = pyqtSignal()  # 申明无参数信号

    def __init__(self):  # 初始化
        self.myname = socket.getfqdn(socket.gethostname())  # gethostname() ： 返回本地主机的标准主机名。
        self.myaddr = socket.gethostbyname(self.myname)  # gethostbyname()：用域名或主机名获取IP地址
        super(Forth_ID4, self).__init__()  # 继承父类的属性和方法
        self.initUI()  # 调用自己的方法

    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)

        if int(i) == 1:  ## 传过来的是str型参数，转换成int型才可
            # self.hide()
            self.f1 = First_ID1()
            self.f1.show()

        elif int(i) == 2:
            # self.hide()
            self.s2 = Second_ID2()
            self.s2.show()

        elif int(i) == 3:
            # self.hide()
            self.t3 = Third_ID3()
            self.t3.show()

        elif int(i) == 5:
            # self.hide()
            self.f5 = Fifth_ID5()
            self.f5.show()

        elif int(i) == 6:
            # self.hide()
            self.s6 = Sixth_ID6()
            self.s6.show()

        elif int(i) == 7:
            # self.hide()
            self.s7 = Seventh_ID7()
            self.s7.show()

        elif int(i) == 8:
            # self.hide()
            self.e8 = Eighth_ID8()
            self.e8.show()

        elif int(i) == 9:
            # self.hide()
            self.n9 = Ninth_ID9()
            self.n9.show()

        elif int(i) == 10:
            # self.hide()
            self.t10 = Tenth_ID10()
            self.t10.show()

    def initUI(self):

        self.btn = QPushButton('jump to FirstUI', self)  # 用来返回到第一个界面
        self.btn.setGeometry(350, 50, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function)

        self.cb = QComboBox(self)
        self.cb.move(350, 10)
        self.cb.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容

        ##=======================================================第四层按钮组件
        # 退出按钮
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(QCoreApplication.instance().quit)  # 信号与槽，槽可以是QT内置的槽也可以是python内置方法
        self.quitButton.resize(self.quitButton.sizeHint())  # sizeHint()提供一个推荐大小
        self.quitButton.move(50, 360)  # 放置位子
        # 监听按钮
        self.listenButton = QPushButton('Listen', self)
        self.listenButton.setCheckable(True)  # 可以点击
        self.listenButton.clicked.connect(self.listenToClient)  # 链接到槽方法listenToClient,开始监听
        self.listenButton.resize(self.quitButton.sizeHint())  # 和quitButton按钮一样大
        self.listenButton.move(250, 360)  # 改变大小并移动

        #  开始按钮
        self.startButton = QPushButton('Start', self)
        self.startButton.setCheckable(True)
        self.startButton.clicked.connect(self.start)  # self.StartFlag = 1,表示开始向下位机发送数据
        self.startButton.resize(self.quitButton.sizeHint())
        self.startButton.move(50, 400)

        #  发送第一组数据按钮
        self.sendButton = QPushButton('Send', self)
        self.sendButton.setCheckable(True)
        self.sendButton.clicked.connect(self.send)  # 发送第一组经纬度
        self.sendButton.resize(self.quitButton.sizeHint())
        self.sendButton.move(250, 400)

        #  请求车辆的状态
        self.stateButton = QPushButton('AskState', self)
        self.stateButton.setCheckable(True)
        self.stateButton.clicked.connect(self.askstate)  # 发送停止信号 “ST”
        self.stateButton.resize(self.quitButton.sizeHint())
        self.stateButton.move(150, 360)

        #  请求车辆的图像
        self.imageButton = QPushButton('AskImage', self)
        self.imageButton.setCheckable(True)
        self.imageButton.clicked.connect(self.askimage)  # 发送停止信号 “ST”
        self.imageButton.resize(self.quitButton.sizeHint())
        self.imageButton.move(150, 400)

        #  请求百度地图
        # self.imageButton = QPushButton('BD_map', self)
        # self.imageButton.setCheckable(True)
        # self.imageButton.clicked.connect(self.mapshow)  # 发送显示地图指令
        # self.imageButton.resize(self.quitButton.sizeHint())
        # self.imageButton.move(150, 320)
        ##====================================================第四层按钮组件


        ##==============================================第一层按钮组件
        # 服务器角色 控件布局
        # 上位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(85, 10)
        self.carIPLabel.setText('上位机')
        # IP Label (20, 20) default size
        self.serverIPLabel = QLabel(self)
        self.serverIPLabel.move(20, 30)
        self.serverIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.serverIPLineEdit = QLineEdit(self)
        self.serverIPLineEdit.move(50, 38)
        self.serverIPLineEdit.resize(120, 15)
        self.serverIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverIPLineEdit.setText(self.myaddr)  # 本地主机的IP
        # IP Label (20, 40) default size
        self.serverPortLabel = QLabel(self)
        self.serverPortLabel.move(20, 50)
        self.serverPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.serverPortLineEdit = QLineEdit(self)
        self.serverPortLineEdit.move(50, 58)
        self.serverPortLineEdit.resize(120, 15)
        self.serverPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverPortLineEdit.setText('7890')  # 自己选取的端口号

        # 客户端角色 控件布局
        # 下位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(255, 10)
        self.carIPLabel.setText('阿里云')
        # IP Label (20, 20) default size
        self.clientIPLabel = QLabel(self)  # IP标签
        self.clientIPLabel.move(190, 30)
        self.clientIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.clientIPLineEdit = QLineEdit(self)  # IP显示文本框
        self.clientIPLineEdit.move(220, 38)
        self.clientIPLineEdit.resize(120, 15)
        self.clientIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        # self.clientIPLineEdit.setText(self.myaddr)
        ######################################################################################
        self.clientIPLineEdit.setText("47.102.36.187")  # 输入自定义IP
        # IP Label (20, 40) default size
        self.clientPortLabel = QLabel(self)  # port标签
        self.clientPortLabel.move(190, 50)
        self.clientPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.clientPortLineEdit = QLineEdit(self)
        self.clientPortLineEdit.move(220, 58)
        self.clientPortLineEdit.resize(120, 15)
        self.clientPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.clientPortLineEdit.setText('8088')
        ##==============================================第一层按钮组件

        ##=========================================================第二层按钮组件
        # 参数设置
        # 车辆长度 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(40, 85)
        self.lengthOfCarLabel.setText('车辆长度:')
        # 车辆长度 Edit  (50, 18) (120, 15)
        self.lengthOfCarLienEdit = QLineEdit(self)
        self.lengthOfCarLienEdit.move(95, 91)
        self.lengthOfCarLienEdit.resize(50, 15)
        self.lengthOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.lengthOfCarLienEdit.setText('1')
        # 车辆长度单位 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(150, 85)
        self.lengthOfCarLabel.setText('m')

        # 车辆重量 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(210, 85)
        self.weightOfCarLabel.setText('车辆重量:')
        # 车辆重量 Edit  (50, 18) (120, 15)
        self.weightOfCarLienEdit = QLineEdit(self)
        self.weightOfCarLienEdit.move(265, 91)
        self.weightOfCarLienEdit.resize(50, 15)
        self.weightOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.weightOfCarLienEdit.setText('1')
        # 车辆重量单位 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(320, 85)
        self.weightOfCarLabel.setText('kg')

        # 最大速度 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(40, 110)
        self.maxVelocityOfCarLabel.setText('最大速度:')
        # 最大速度 Edit  (50, 18) (120, 15)
        self.maxVelocityOfCarLienEdit = QLineEdit(self)
        self.maxVelocityOfCarLienEdit.move(95, 116)
        self.maxVelocityOfCarLienEdit.resize(50, 15)
        self.maxVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxVelocityOfCarLienEdit.setText('1')
        # 最大速度单位 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(150, 110)
        self.maxVelocityOfCarLabel.setText('m/s')

        # 最小速度 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(210, 110)
        self.minVelocityOfCarLabel.setText('最小速度:')
        # 最小速度 Edit  (50, 18) (120, 15)
        self.minVelocityOfCarLienEdit = QLineEdit(self)
        self.minVelocityOfCarLienEdit.move(265, 116)
        self.minVelocityOfCarLienEdit.resize(50, 15)
        self.minVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.minVelocityOfCarLienEdit.setText('1')
        # 最小速度单位 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(320, 110)
        self.minVelocityOfCarLabel.setText('m/s')

        # 最大加速度 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(30, 135)
        self.maxAccelationOfCarLabel.setText('最大加速度:')
        # 最大加速度 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 141)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 最大加速度单位 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 135)
        self.maxAccelationOfCarLabel.setText('m/s^2')

        # 最大减速度 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(200, 135)
        self.maxDecelerationOfCarLabel.setText('最大减速度:')
        # 最大减速度 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 141)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 最大减速度单位 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 135)
        self.maxDecelerationOfCarLabel.setText('m/s^2')

        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(40, 160)
        self.maxAccelationOfCarLabel.setText('转动惯量:')
        # 转动惯量 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 166)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 160)
        self.maxAccelationOfCarLabel.setText('kg·m^2')

        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(235, 160)
        self.maxDecelerationOfCarLabel.setText('轴距:')
        # 轴距 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 166)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 160)
        self.maxDecelerationOfCarLabel.setText('m')





        ##=========================================================第二层按钮组件


        ##======================================================第三层按钮组件
        # 数据显示部分
        # 车辆ID
        self.IDLabel = QLabel(self)
        self.IDLabel.move(65, 190)
        self.IDLabel.setText('车辆编号:')
        self.IDChangeLabel = QLabel(self)
        self.IDChangeLabel.move(120, 190)
        self.IDChangeLabel.setText('xx')

        # 左轮速度
        self.L2vLabel = QLabel(self)
        self.L2vLabel.move(65, 210)
        self.L2vLabel.setText('左轮电机速度:')
        self.L2vChangeLabel = QLabel(self)
        self.L2vChangeLabel.move(145, 210)
        self.L2vChangeLabel.setText('xxxx')
        self.L2vUnitLabel = QLabel(self)
        self.L2vUnitLabel.move(170, 210)
        self.L2vUnitLabel.setText('cm/s')

        # 右轮速度
        self.R2vLabel = QLabel(self)
        self.R2vLabel.move(210, 210)
        self.R2vLabel.setText('右轮电机速度:')
        self.R2vChangeLabel = QLabel(self)
        self.R2vChangeLabel.move(290, 210)
        self.R2vChangeLabel.setText('xxxxx')
        self.R2vUnitLabel = QLabel(self)
        self.R2vUnitLabel.move(320, 210)
        self.R2vUnitLabel.setText('cm/s')

        # 舵机转角
        self.angleLabel = QLabel(self)
        self.angleLabel.move(210, 230)
        self.angleLabel.setText('转向角度:')
        self.angleChangeLabel = QLabel(self)
        self.angleChangeLabel.move(265, 230)
        self.angleChangeLabel.setText('xxxx')
        self.angleUnitLabel = QLabel(self)
        self.angleUnitLabel.move(295, 230)
        self.angleUnitLabel.setText('°')

        # 车辆状态
        self.LPWMLabel = QLabel(self)
        self.LPWMLabel.move(210, 190)
        self.LPWMLabel.setText('车辆状态:')
        self.LPWMChangeLabel = QLabel(self)
        self.LPWMChangeLabel.move(265, 190)
        self.LPWMChangeLabel.setText('xxxx')

        # 电池电压
        self.RPWMLabel = QLabel(self)
        self.RPWMLabel.move(65, 230)
        self.RPWMLabel.setText('电池电压:')
        self.RPWMChangeLabel = QLabel(self)
        self.RPWMChangeLabel.move(120, 230)
        self.RPWMChangeLabel.setText('xxxx')
        self.RPWMUnitLabel = QLabel(self)
        self.RPWMUnitLabel.move(150, 230)
        self.RPWMUnitLabel.setText('v')

        # 横向加速度
        self.AyLabel = QLabel(self)
        self.AyLabel.move(65, 250)
        self.AyLabel.setText('横向加速度:')
        self.AyChangeLabel = QLabel(self)
        self.AyChangeLabel.move(135, 250)
        self.AyChangeLabel.setText('xxxx')
        self.AyUnitLabel = QLabel(self)
        self.AyUnitLabel.move(165, 250)
        self.AyUnitLabel.setText('m/s^2')

        # 横摆角速度
        self.YawLabel = QLabel(self)
        self.YawLabel.move(210, 250)
        self.YawLabel.setText('横摆角速度:')
        self.YawChangeLabel = QLabel(self)
        self.YawChangeLabel.move(280, 250)
        self.YawChangeLabel.setText('xxxx')
        self.YawUnitLabel = QLabel(self)
        self.YawUnitLabel.move(310, 250)
        self.YawUnitLabel.setText('°/s')

        # 电机转矩
        self.TnLabel = QLabel(self)
        self.TnLabel.move(210, 270)
        self.TnLabel.setText('电机转矩:')
        self.TnChangeLabel = QLabel(self)
        self.TnChangeLabel.move(265, 270)
        self.TnChangeLabel.setText('xxxx')
        self.TnUnitLabel = QLabel(self)
        self.TnUnitLabel.move(295, 270)
        self.TnUnitLabel.setText('N·m')

        # 横向速度
        self.VyLabel = QLabel(self)
        self.VyLabel.move(65, 270)
        self.VyLabel.setText('横向速度:')
        self.VyChangeLabel = QLabel(self)
        self.VyChangeLabel.move(125, 270)
        self.VyChangeLabel.setText('xxxx')
        self.VyUnitLabel = QLabel(self)
        self.VyUnitLabel.move(155, 270)
        self.VyUnitLabel.setText('m/s')

        # 当前经度
        self.lngLabel = QLabel(self)
        self.lngLabel.move(65, 300)
        self.lngLabel.setText('当前经度:')
        self.lngChangeLabel = QLabel(self)
        self.lngChangeLabel.move(120, 300)
        self.lngChangeLabel.setText('xxxx')
        self.lngUnitLabel = QLabel(self)
        self.lngUnitLabel.move(250, 300)
        self.lngUnitLabel.setText('°')

        # 当前纬度
        self.latLabel = QLabel(self)
        self.latLabel.move(65, 320)
        self.latLabel.setText('当前纬度:')
        self.latChangeLabel = QLabel(self)
        self.latChangeLabel.move(120, 320)
        self.latChangeLabel.setText('xxxx')
        # self.latChangeLabel.setGeometry(QRect(328, 240, 329, 27 * 4))
        # self.latChangeLabel.setWordWrap(True)
        # self.latChangeLabel.setAlignment(Qt.AlignTop)
        self.latUnitLabel = QLabel(self)
        self.latUnitLabel.move(250, 320)
        self.latUnitLabel.setText('°')



        ## 下位机上传的图像信息
        self.angleLabel = QLabel(self)
        self.angleLabel.move(400, 150)
        self.angleLabel.setText('图像:')

        pix = QPixmap('background.jpg')
        self.lb1 = QLabel(self)
        self.lb1.setGeometry(450, 5, 400, 200)  # x1 x2 x3 x4,从（x1,x2）开始显示一个x3长x4宽的矩形
        self.lb1.setPixmap(QPixmap('background.jpg'))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
        self.lb1.setStyleSheet("border: 2px solid red")


        # 方法三
        self.angleLabel = QLabel(self)  # 标签
        self.angleLabel.move(390, 350)
        self.angleLabel.setText('导航图像:')
        # 调用Mapwindow函数，建立一个他的对象
        SettingBox_Map1 = QGroupBox("导航地图")
        Map1 = Map_load2()
        v_map1_layout = QVBoxLayout()
        v_map1_layout.addWidget(Map1)
        v_map1_layout.setContentsMargins(450, 200, 50, 50)  # 左上右下距离边框的长度
        self.setLayout(v_map1_layout)
        # QApplication.processEvents()  # 使得图像界面可以实时更新


        # 状态栏显示
        # self.setGeometry(100, 100, 370, 550)
        self.setGeometry(100, 100, 900, 450)
        self.setWindowTitle('Forth')
        self.show()

    def slot_btn_function(self):
        # self.hide()
        self.f1 = First_ID1()
        self.f1.show()



    ## 响应槽函数
    def mapshow(self, text):
        map = (Map().add(text, [list(z) for z in zip(Faker.provinces, Faker.values())], text)
               .set_global_opts(title_opts=opts.TitleOpts(title="map")))
        map.render('BD_map4.html')  # 读取对应车辆的百度地图API程序
        # self.browser.load(QUrl(QFileInfo("file:///E:/pycharm_project/TCP%2010%2025/BD_map.html").absoluteFilePath()))
        self.browser.load(QUrl(QFileInfo("BD_map4.html").absoluteFilePath()))
        print("更新BD地图============")
        if text in self.knowledge:
            self.knowledge_label.setText(self.knowledge[text])
        else:
            self.knowledge_label.setText('')

    def IDchange(self,ID):  # 更新车辆ID的槽函数
        self.IDChangeLabel.setText(ID)

    def Statechange(self,State):  # 更新车辆状态
        self.StatechangeLable.setText(str(State))


    def L2vchange(self, L2v):  # 更新左轮电机转速的槽函数
        self.L2vChangeLabel.setText(str(L2v))

    def R2vchange(self, R2v):  # 更新右轮电机转速的槽函数
        self.R2vChangeLabel.setText(str(R2v))
    def anglechange(self, angle):  # 更新转向角度的槽函数
        self.angleChangeLabel.setText(str(angle))

    def Uchange(self,U):
        self.UchangeLabel.setText(U)

    def LPWMchange(self, LPWM):
        self.LPWMChangeLabel.setText(str(LPWM))

    def RPWMchange(self,RPWM):
        self.RPWMChangeLabel.setText(str(RPWM))

    def Aychange(self,Ay):
        self.AyChangeLabel.setText(str(Ay))

    def Yawchange(self,Yaw):
        self.YawChangeLabel.setText(str(Yaw))

    def Tnchange(self,Tn):
        self.TnChangeLabel.setText(str(Tn))

    def Vychange(self,Vy):
        self.VyChangeLabel.setText(str(Vy))


    def lngChange(self,lng):
        self.lngChangeLabel.setText(str(lng))

    def latChange(self,lat):
        self.latChangeLabel.setText(str(lat))


    # 修改显示的图像
    def QPixmapchange(self,Image):
        self.lb1.setPixmap(QPixmap(str(Image)))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
    # 修改显示的图像


    def start(self):  # start按钮的槽函数
        global startFlag
        startFlag = 1



    def listenToClient(self):  # 点击Listen后的响应事件
        localIP = self.serverIPLineEdit.text()  # 定义Listener类中的属性值
        localPort = self.serverPortLineEdit.text()
        serverIP = self.clientIPLineEdit.text()
        serverPort = self.clientPortLineEdit.text()
        length = self.lengthOfCarLienEdit.text()
        weight = self.weightOfCarLienEdit.text()
        maxV = self.maxVelocityOfCarLienEdit.text()
        minV = self.minVelocityOfCarLienEdit.text()
        maxA = self.maxAccelationOfCarLienEdit.text()
        maxD = self.maxDecelerationOfCarLienEdit.text()
        self._thread = Listener_ID4(localIP, int(localPort), serverIP, int(serverPort),
                                int(length), int(weight), int(maxV),
                                int(minV), int(maxA), int(maxD))  # 定义一个Listener的对象
        self._thread.sigID_ID4.connect(self.IDchange)  # 调用修改参数方法，实时传输显示下位机传输的数据
        self._thread.sigRPWM_ID4.connect(self.RPWMchange)
        self._thread.sigLPWM_ID4.connect(self.LPWMchange)
        self._thread.sigL2v_ID4.connect(self.L2vchange)
        self._thread.sigR2v_ID4.connect(self.R2vchange)
        self._thread.sigangle_ID4.connect(self.anglechange)
        self._thread.sigImage_ID4.connect(self.QPixmapchange)  # 更新显示的图片

        self._thread.sigAy_ID4.connect(self.Aychange)
        self._thread.sigYaw_ID4.connect(self.Yawchange)
        self._thread.sigTn_ID4.connect(self.Tnchange)
        self._thread.sigVy_ID4.connect(self.Vychange)

        self._thread.siglat_ID4.connect(self.latChange)
        self._thread.siglng_ID4.connect(self.lngChange)  # 更新当前经纬度数据


        self._thread.start()  # 执行Litener类中的run方法
        self.listenButton.setText('Listening')  # 开始执行监听后标识为“正在监听”




    def askstate(self):  # askstate按钮的槽函数
        global askstateFlag_ID4
        askstateFlag_ID4 = 1
        print('askstateFlag_ID4_change_to:', askstateFlag_ID4)

    def askimage(self):  # askimage按钮的槽函数
        global askimageFlag_ID4
        askimageFlag_ID4 = 1
        print('askimageFlag_ID4_change_to:', askimageFlag_ID4)

        # self._thread = Image_listen()
        # self._thread.start()

    def send(self):  # send按钮的槽函数
        global sendFlag_ID4
        sendFlag_ID4 = 1
        print('sendFlag_ID4_change_to:', sendFlag_ID4)




    def closeEvent(self, event):  # GUI窗口右上角关闭按钮的槽函数
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# 第五辆车
class Fifth_ID5(QWidget):

    serverSig = pyqtSignal()  # 申明无参数信号

    def __init__(self):  # 初始化
        self.myname = socket.getfqdn(socket.gethostname())  # gethostname() ： 返回本地主机的标准主机名。
        self.myaddr = socket.gethostbyname(self.myname)  # gethostbyname()：用域名或主机名获取IP地址
        super(Fifth_ID5, self).__init__()  # 继承父类的属性和方法
        self.initUI()  # 调用自己的方法

    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)

        if int(i) == 1:  ## 传过来的是str型参数，转换成int型才可
            # self.hide()
            self.f1 = First_ID1()
            self.f1.show()

        elif int(i) == 2:
            # self.hide()
            self.s2 = Second_ID2()
            self.s2.show()

        elif int(i) == 3:
            # self.hide()
            self.t3 = Third_ID3()
            self.t3.show()

        elif int(i) == 4:
            # self.hide()
            self.f4 = Forth_ID4()
            self.f4.show()

        elif int(i) == 6:
            # self.hide()
            self.s6 = Sixth_ID6()
            self.s6.show()

        elif int(i) == 7:
            # self.hide()
            self.s7 = Seventh_ID7()
            self.s7.show()

        elif int(i) == 8:
            # self.hide()
            self.e8 = Eighth_ID8()
            self.e8.show()

        elif int(i) == 9:
            # self.hide()
            self.n9 = Ninth_ID9()
            self.n9.show()

        elif int(i) == 10:
            # self.hide()
            self.t10 = Tenth_ID10()
            self.t10.show()

    def initUI(self):

        self.btn = QPushButton('jump to FirstUI', self)  # 用来返回到第一个界面
        self.btn.setGeometry(350, 50, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function)

        self.cb = QComboBox(self)
        self.cb.move(350, 10)
        self.cb.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容

        ##=======================================================第四层按钮组件
        # 退出按钮
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(QCoreApplication.instance().quit)  # 信号与槽，槽可以是QT内置的槽也可以是python内置方法
        self.quitButton.resize(self.quitButton.sizeHint())  # sizeHint()提供一个推荐大小
        self.quitButton.move(50, 360)  # 放置位子
        # 监听按钮
        self.listenButton = QPushButton('Listen', self)
        self.listenButton.setCheckable(True)  # 可以点击
        self.listenButton.clicked.connect(self.listenToClient)  # 链接到槽方法listenToClient,开始监听
        self.listenButton.resize(self.quitButton.sizeHint())  # 和quitButton按钮一样大
        self.listenButton.move(250, 360)  # 改变大小并移动

        #  开始按钮
        self.startButton = QPushButton('Start', self)
        self.startButton.setCheckable(True)
        self.startButton.clicked.connect(self.start)  # self.StartFlag = 1,表示开始向下位机发送数据
        self.startButton.resize(self.quitButton.sizeHint())
        self.startButton.move(50, 400)

        #  发送第一组数据按钮
        self.sendButton = QPushButton('Send', self)
        self.sendButton.setCheckable(True)
        self.sendButton.clicked.connect(self.send)  # 发送第一组经纬度
        self.sendButton.resize(self.quitButton.sizeHint())
        self.sendButton.move(250, 400)

        #  请求车辆的状态
        self.stateButton = QPushButton('AskState', self)
        self.stateButton.setCheckable(True)
        self.stateButton.clicked.connect(self.askstate)  # 发送停止信号 “ST”
        self.stateButton.resize(self.quitButton.sizeHint())
        self.stateButton.move(150, 360)

        #  请求车辆的图像
        self.imageButton = QPushButton('AskImage', self)
        self.imageButton.setCheckable(True)
        self.imageButton.clicked.connect(self.askimage)  # 发送停止信号 “ST”
        self.imageButton.resize(self.quitButton.sizeHint())
        self.imageButton.move(150, 400)

        #  请求百度地图
        # self.imageButton = QPushButton('BD_map', self)
        # self.imageButton.setCheckable(True)
        # self.imageButton.clicked.connect(self.mapshow)  # 发送显示地图指令
        # self.imageButton.resize(self.quitButton.sizeHint())
        # self.imageButton.move(150, 320)
        ##====================================================第四层按钮组件


        ##==============================================第一层按钮组件
        # 服务器角色 控件布局
        # 上位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(85, 10)
        self.carIPLabel.setText('上位机')
        # IP Label (20, 20) default size
        self.serverIPLabel = QLabel(self)
        self.serverIPLabel.move(20, 30)
        self.serverIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.serverIPLineEdit = QLineEdit(self)
        self.serverIPLineEdit.move(50, 38)
        self.serverIPLineEdit.resize(120, 15)
        self.serverIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverIPLineEdit.setText(self.myaddr)  # 本地主机的IP
        # IP Label (20, 40) default size
        self.serverPortLabel = QLabel(self)
        self.serverPortLabel.move(20, 50)
        self.serverPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.serverPortLineEdit = QLineEdit(self)
        self.serverPortLineEdit.move(50, 58)
        self.serverPortLineEdit.resize(120, 15)
        self.serverPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverPortLineEdit.setText('7890')  # 自己选取的端口号

        # 客户端角色 控件布局
        # 下位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(255, 10)
        self.carIPLabel.setText('阿里云')
        # IP Label (20, 20) default size
        self.clientIPLabel = QLabel(self)  # IP标签
        self.clientIPLabel.move(190, 30)
        self.clientIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.clientIPLineEdit = QLineEdit(self)  # IP显示文本框
        self.clientIPLineEdit.move(220, 38)
        self.clientIPLineEdit.resize(120, 15)
        self.clientIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        # self.clientIPLineEdit.setText(self.myaddr)
        ######################################################################################
        self.clientIPLineEdit.setText("47.102.36.187")  # 输入自定义IP
        # IP Label (20, 40) default size
        self.clientPortLabel = QLabel(self)  # port标签
        self.clientPortLabel.move(190, 50)
        self.clientPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.clientPortLineEdit = QLineEdit(self)
        self.clientPortLineEdit.move(220, 58)
        self.clientPortLineEdit.resize(120, 15)
        self.clientPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.clientPortLineEdit.setText('8090')
        ##==============================================第一层按钮组件

        ##=========================================================第二层按钮组件
        # 参数设置
        # 车辆长度 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(40, 85)
        self.lengthOfCarLabel.setText('车辆长度:')
        # 车辆长度 Edit  (50, 18) (120, 15)
        self.lengthOfCarLienEdit = QLineEdit(self)
        self.lengthOfCarLienEdit.move(95, 91)
        self.lengthOfCarLienEdit.resize(50, 15)
        self.lengthOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.lengthOfCarLienEdit.setText('1')
        # 车辆长度单位 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(150, 85)
        self.lengthOfCarLabel.setText('m')

        # 车辆重量 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(210, 85)
        self.weightOfCarLabel.setText('车辆重量:')
        # 车辆重量 Edit  (50, 18) (120, 15)
        self.weightOfCarLienEdit = QLineEdit(self)
        self.weightOfCarLienEdit.move(265, 91)
        self.weightOfCarLienEdit.resize(50, 15)
        self.weightOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.weightOfCarLienEdit.setText('1')
        # 车辆重量单位 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(320, 85)
        self.weightOfCarLabel.setText('kg')

        # 最大速度 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(40, 110)
        self.maxVelocityOfCarLabel.setText('最大速度:')
        # 最大速度 Edit  (50, 18) (120, 15)
        self.maxVelocityOfCarLienEdit = QLineEdit(self)
        self.maxVelocityOfCarLienEdit.move(95, 116)
        self.maxVelocityOfCarLienEdit.resize(50, 15)
        self.maxVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxVelocityOfCarLienEdit.setText('1')
        # 最大速度单位 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(150, 110)
        self.maxVelocityOfCarLabel.setText('m/s')

        # 最小速度 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(210, 110)
        self.minVelocityOfCarLabel.setText('最小速度:')
        # 最小速度 Edit  (50, 18) (120, 15)
        self.minVelocityOfCarLienEdit = QLineEdit(self)
        self.minVelocityOfCarLienEdit.move(265, 116)
        self.minVelocityOfCarLienEdit.resize(50, 15)
        self.minVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.minVelocityOfCarLienEdit.setText('1')
        # 最小速度单位 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(320, 110)
        self.minVelocityOfCarLabel.setText('m/s')

        # 最大加速度 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(30, 135)
        self.maxAccelationOfCarLabel.setText('最大加速度:')
        # 最大加速度 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 141)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 最大加速度单位 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 135)
        self.maxAccelationOfCarLabel.setText('m/s^2')

        # 最大减速度 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(200, 135)
        self.maxDecelerationOfCarLabel.setText('最大减速度:')
        # 最大减速度 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 141)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 最大减速度单位 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 135)
        self.maxDecelerationOfCarLabel.setText('m/s^2')

        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(40, 160)
        self.maxAccelationOfCarLabel.setText('转动惯量:')
        # 转动惯量 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 166)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 160)
        self.maxAccelationOfCarLabel.setText('kg·m^2')

        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(235, 160)
        self.maxDecelerationOfCarLabel.setText('轴距:')
        # 轴距 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 166)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 160)
        self.maxDecelerationOfCarLabel.setText('m')





        ##=========================================================第二层按钮组件


        ##======================================================第三层按钮组件
        # 数据显示部分
        # 车辆ID
        self.IDLabel = QLabel(self)
        self.IDLabel.move(65, 190)
        self.IDLabel.setText('车辆编号:')
        self.IDChangeLabel = QLabel(self)
        self.IDChangeLabel.move(120, 190)
        self.IDChangeLabel.setText('xx')

        # 左轮速度
        self.L2vLabel = QLabel(self)
        self.L2vLabel.move(65, 210)
        self.L2vLabel.setText('左轮电机速度:')
        self.L2vChangeLabel = QLabel(self)
        self.L2vChangeLabel.move(145, 210)
        self.L2vChangeLabel.setText('xxxx')
        self.L2vUnitLabel = QLabel(self)
        self.L2vUnitLabel.move(170, 210)
        self.L2vUnitLabel.setText('cm/s')

        # 右轮速度
        self.R2vLabel = QLabel(self)
        self.R2vLabel.move(210, 210)
        self.R2vLabel.setText('右轮电机速度:')
        self.R2vChangeLabel = QLabel(self)
        self.R2vChangeLabel.move(290, 210)
        self.R2vChangeLabel.setText('xxxxx')
        self.R2vUnitLabel = QLabel(self)
        self.R2vUnitLabel.move(320, 210)
        self.R2vUnitLabel.setText('cm/s')

        # 舵机转角
        self.angleLabel = QLabel(self)
        self.angleLabel.move(210, 230)
        self.angleLabel.setText('转向角度:')
        self.angleChangeLabel = QLabel(self)
        self.angleChangeLabel.move(265, 230)
        self.angleChangeLabel.setText('xxxx')
        self.angleUnitLabel = QLabel(self)
        self.angleUnitLabel.move(295, 230)
        self.angleUnitLabel.setText('°')

        # 车辆状态
        self.LPWMLabel = QLabel(self)
        self.LPWMLabel.move(210, 190)
        self.LPWMLabel.setText('车辆状态:')
        self.LPWMChangeLabel = QLabel(self)
        self.LPWMChangeLabel.move(265, 190)
        self.LPWMChangeLabel.setText('xxxx')

        # 电池电压
        self.RPWMLabel = QLabel(self)
        self.RPWMLabel.move(65, 230)
        self.RPWMLabel.setText('电池电压:')
        self.RPWMChangeLabel = QLabel(self)
        self.RPWMChangeLabel.move(120, 230)
        self.RPWMChangeLabel.setText('xxxx')
        self.RPWMUnitLabel = QLabel(self)
        self.RPWMUnitLabel.move(150, 230)
        self.RPWMUnitLabel.setText('v')

        # 横向加速度
        self.AyLabel = QLabel(self)
        self.AyLabel.move(65, 250)
        self.AyLabel.setText('横向加速度:')
        self.AyChangeLabel = QLabel(self)
        self.AyChangeLabel.move(135, 250)
        self.AyChangeLabel.setText('xxxx')
        self.AyUnitLabel = QLabel(self)
        self.AyUnitLabel.move(165, 250)
        self.AyUnitLabel.setText('m/s^2')

        # 横摆角速度
        self.YawLabel = QLabel(self)
        self.YawLabel.move(210, 250)
        self.YawLabel.setText('横摆角速度:')
        self.YawChangeLabel = QLabel(self)
        self.YawChangeLabel.move(280, 250)
        self.YawChangeLabel.setText('xxxx')
        self.YawUnitLabel = QLabel(self)
        self.YawUnitLabel.move(310, 250)
        self.YawUnitLabel.setText('°/s')

        # 电机转矩
        self.TnLabel = QLabel(self)
        self.TnLabel.move(210, 270)
        self.TnLabel.setText('电机转矩:')
        self.TnChangeLabel = QLabel(self)
        self.TnChangeLabel.move(265, 270)
        self.TnChangeLabel.setText('xxxx')
        self.TnUnitLabel = QLabel(self)
        self.TnUnitLabel.move(295, 270)
        self.TnUnitLabel.setText('N·m')

        # 横向速度
        self.VyLabel = QLabel(self)
        self.VyLabel.move(65, 270)
        self.VyLabel.setText('横向速度:')
        self.VyChangeLabel = QLabel(self)
        self.VyChangeLabel.move(125, 270)
        self.VyChangeLabel.setText('xxxx')
        self.VyUnitLabel = QLabel(self)
        self.VyUnitLabel.move(155, 270)
        self.VyUnitLabel.setText('m/s')

        # 当前经度
        self.lngLabel = QLabel(self)
        self.lngLabel.move(65, 300)
        self.lngLabel.setText('当前经度:')
        self.lngChangeLabel = QLabel(self)
        self.lngChangeLabel.move(120, 300)
        self.lngChangeLabel.setText('xxxx')
        self.lngUnitLabel = QLabel(self)
        self.lngUnitLabel.move(250, 300)
        self.lngUnitLabel.setText('°')

        # 当前纬度
        self.latLabel = QLabel(self)
        self.latLabel.move(65, 320)
        self.latLabel.setText('当前纬度:')
        self.latChangeLabel = QLabel(self)
        self.latChangeLabel.move(120, 320)
        self.latChangeLabel.setText('xxxx')
        # self.latChangeLabel.setGeometry(QRect(328, 240, 329, 27 * 4))
        # self.latChangeLabel.setWordWrap(True)
        # self.latChangeLabel.setAlignment(Qt.AlignTop)
        self.latUnitLabel = QLabel(self)
        self.latUnitLabel.move(250, 320)
        self.latUnitLabel.setText('°')



        ## 下位机上传的图像信息
        self.angleLabel = QLabel(self)
        self.angleLabel.move(400, 150)
        self.angleLabel.setText('图像:')

        pix = QPixmap('background.jpg')
        self.lb1 = QLabel(self)
        self.lb1.setGeometry(450, 5, 400, 200)  # x1 x2 x3 x4,从（x1,x2）开始显示一个x3长x4宽的矩形
        self.lb1.setPixmap(QPixmap('background.jpg'))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
        self.lb1.setStyleSheet("border: 2px solid red")


        # 方法三
        self.angleLabel = QLabel(self)  # 标签
        self.angleLabel.move(390, 350)
        self.angleLabel.setText('导航图像:')
        # 调用Mapwindow函数，建立一个他的对象
        SettingBox_Map1 = QGroupBox("导航地图")
        Map1 = Map_load2()
        v_map1_layout = QVBoxLayout()
        v_map1_layout.addWidget(Map1)
        v_map1_layout.setContentsMargins(450, 200, 50, 50)  # 左上右下距离边框的长度
        self.setLayout(v_map1_layout)
        # QApplication.processEvents()  # 使得图像界面可以实时更新


        # 状态栏显示
        # self.setGeometry(100, 100, 370, 550)
        self.setGeometry(100, 100, 900, 450)
        self.setWindowTitle('Fifth')
        self.show()

    def slot_btn_function(self):
        # self.hide()
        self.f1 = First_ID1()
        self.f1.show()



    ## 响应槽函数
    def mapshow(self, text):
        map = (Map().add(text, [list(z) for z in zip(Faker.provinces, Faker.values())], text)
               .set_global_opts(title_opts=opts.TitleOpts(title="map")))
        map.render('BD_map5.html')  # 读取对应车辆的百度地图API程序
        # self.browser.load(QUrl(QFileInfo("file:///E:/pycharm_project/TCP%2010%2025/BD_map.html").absoluteFilePath()))
        self.browser.load(QUrl(QFileInfo("BD_map5.html").absoluteFilePath()))
        print("更新BD地图============")
        if text in self.knowledge:
            self.knowledge_label.setText(self.knowledge[text])
        else:
            self.knowledge_label.setText('')

    def IDchange(self,ID):  # 更新车辆ID的槽函数
        self.IDChangeLabel.setText(ID)

    def Statechange(self,State):  # 更新车辆状态
        self.StatechangeLable.setText(str(State))


    def L2vchange(self, L2v):  # 更新左轮电机转速的槽函数
        self.L2vChangeLabel.setText(str(L2v))

    def R2vchange(self, R2v):  # 更新右轮电机转速的槽函数
        self.R2vChangeLabel.setText(str(R2v))
    def anglechange(self, angle):  # 更新转向角度的槽函数
        self.angleChangeLabel.setText(str(angle))

    def Uchange(self,U):
        self.UchangeLabel.setText(U)

    def LPWMchange(self, LPWM):
        self.LPWMChangeLabel.setText(str(LPWM))

    def RPWMchange(self,RPWM):
        self.RPWMChangeLabel.setText(str(RPWM))

    def Aychange(self,Ay):
        self.AyChangeLabel.setText(str(Ay))

    def Yawchange(self,Yaw):
        self.YawChangeLabel.setText(str(Yaw))

    def Tnchange(self,Tn):
        self.TnChangeLabel.setText(str(Tn))

    def Vychange(self,Vy):
        self.VyChangeLabel.setText(str(Vy))


    def lngChange(self,lng):
        self.lngChangeLabel.setText(str(lng))

    def latChange(self,lat):
        self.latChangeLabel.setText(str(lat))


    # 修改显示的图像
    def QPixmapchange(self,Image):
        self.lb1.setPixmap(QPixmap(str(Image)))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
    # 修改显示的图像


    def start(self):  # start按钮的槽函数
        global startFlag
        startFlag = 1



    def listenToClient(self):  # 点击Listen后的响应事件
        localIP = self.serverIPLineEdit.text()  # 定义Listener类中的属性值
        localPort = self.serverPortLineEdit.text()
        serverIP = self.clientIPLineEdit.text()
        serverPort = self.clientPortLineEdit.text()
        length = self.lengthOfCarLienEdit.text()
        weight = self.weightOfCarLienEdit.text()
        maxV = self.maxVelocityOfCarLienEdit.text()
        minV = self.minVelocityOfCarLienEdit.text()
        maxA = self.maxAccelationOfCarLienEdit.text()
        maxD = self.maxDecelerationOfCarLienEdit.text()
        self._thread = Listener_ID5(localIP, int(localPort), serverIP, int(serverPort),
                                int(length), int(weight), int(maxV),
                                int(minV), int(maxA), int(maxD))  # 定义一个Listener的对象
        self._thread.sigID_ID5.connect(self.IDchange)  # 调用修改参数方法，实时传输显示下位机传输的数据
        self._thread.sigRPWM_ID5.connect(self.RPWMchange)
        self._thread.sigLPWM_ID5.connect(self.LPWMchange)
        self._thread.sigL2v_ID5.connect(self.L2vchange)
        self._thread.sigR2v_ID5.connect(self.R2vchange)
        self._thread.sigangle_ID5.connect(self.anglechange)
        self._thread.sigImage_ID5.connect(self.QPixmapchange)  # 更新显示的图片

        self._thread.sigAy_ID5.connect(self.Aychange)
        self._thread.sigYaw_ID5.connect(self.Yawchange)
        self._thread.sigTn_ID5.connect(self.Tnchange)
        self._thread.sigVy_ID5.connect(self.Vychange)

        self._thread.siglat_ID5.connect(self.latChange)
        self._thread.siglng_ID5.connect(self.lngChange)  # 更新当前经纬度数据


        self._thread.start()  # 执行Litener类中的run方法
        self.listenButton.setText('Listening')  # 开始执行监听后标识为“正在监听”




    def askstate(self):  # askstate按钮的槽函数
        global askstateFlag_ID5
        askstateFlag_ID5 = 1
        print('askstateFlag_ID5_change_to:', askstateFlag_ID5)

    def askimage(self):  # askimage按钮的槽函数
        global askimageFlag_ID5
        askimageFlag_ID5 = 1
        print('askimageFlag_ID5_change_to:', askimageFlag_ID5)

        # self._thread = Image_listen()
        # self._thread.start()

    def send(self):  # send按钮的槽函数
        global sendFlag_ID5
        sendFlag_ID5 = 1
        print('sendFlag_ID5_change_to:', sendFlag_ID5)




    def closeEvent(self, event):  # GUI窗口右上角关闭按钮的槽函数
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# 第六辆车
class Sixth_ID6(QWidget):

    serverSig = pyqtSignal()  # 申明无参数信号

    def __init__(self):  # 初始化
        self.myname = socket.getfqdn(socket.gethostname())  # gethostname() ： 返回本地主机的标准主机名。
        self.myaddr = socket.gethostbyname(self.myname)  # gethostbyname()：用域名或主机名获取IP地址
        super(Sixth_ID6, self).__init__()  # 继承父类的属性和方法
        self.initUI()  # 调用自己的方法

    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)

        if int(i) == 1:  ## 传过来的是str型参数，转换成int型才可
            # self.hide()
            self.f1 = First_ID1()
            self.f1.show()

        elif int(i) == 2:
            # self.hide()
            self.s2 = Second_ID2()
            self.s2.show()

        elif int(i) == 3:
            # self.hide()
            self.t3 = Third_ID3()
            self.t3.show()

        elif int(i) == 4:
            # self.hide()
            self.f4 = Forth_ID4()
            self.f4.show()

        elif int(i) == 5:
            # self.hide()
            self.f5 = Fifth_ID5()
            self.f5.show()

        elif int(i) == 7:
            # self.hide()
            self.s7 = Seventh_ID7()
            self.s7.show()

        elif int(i) == 8:
            # self.hide()
            self.e8 = Eighth_ID8()
            self.e8.show()

        elif int(i) == 9:
            # self.hide()
            self.n9 = Ninth_ID9()
            self.n9.show()

        elif int(i) == 10:
            # self.hide()
            self.t10 = Tenth_ID10()
            self.t10.show()

    def initUI(self):

        self.btn = QPushButton('jump to FirstUI', self)  # 用来返回到第一个界面
        self.btn.setGeometry(350, 50, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function)

        self.cb = QComboBox(self)
        self.cb.move(350, 10)
        self.cb.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容

        ##=======================================================第四层按钮组件
        # 退出按钮
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(QCoreApplication.instance().quit)  # 信号与槽，槽可以是QT内置的槽也可以是python内置方法
        self.quitButton.resize(self.quitButton.sizeHint())  # sizeHint()提供一个推荐大小
        self.quitButton.move(50, 360)  # 放置位子
        # 监听按钮
        self.listenButton = QPushButton('Listen', self)
        self.listenButton.setCheckable(True)  # 可以点击
        self.listenButton.clicked.connect(self.listenToClient)  # 链接到槽方法listenToClient,开始监听
        self.listenButton.resize(self.quitButton.sizeHint())  # 和quitButton按钮一样大
        self.listenButton.move(250, 360)  # 改变大小并移动

        #  开始按钮
        self.startButton = QPushButton('Start', self)
        self.startButton.setCheckable(True)
        self.startButton.clicked.connect(self.start)  # self.StartFlag = 1,表示开始向下位机发送数据
        self.startButton.resize(self.quitButton.sizeHint())
        self.startButton.move(50, 400)

        #  发送第一组数据按钮
        self.sendButton = QPushButton('Send', self)
        self.sendButton.setCheckable(True)
        self.sendButton.clicked.connect(self.send)  # 发送第一组经纬度
        self.sendButton.resize(self.quitButton.sizeHint())
        self.sendButton.move(250, 400)

        #  请求车辆的状态
        self.stateButton = QPushButton('AskState', self)
        self.stateButton.setCheckable(True)
        self.stateButton.clicked.connect(self.askstate)  # 发送停止信号 “ST”
        self.stateButton.resize(self.quitButton.sizeHint())
        self.stateButton.move(150, 360)

        #  请求车辆的图像
        self.imageButton = QPushButton('AskImage', self)
        self.imageButton.setCheckable(True)
        self.imageButton.clicked.connect(self.askimage)  # 发送停止信号 “ST”
        self.imageButton.resize(self.quitButton.sizeHint())
        self.imageButton.move(150, 400)

        #  请求百度地图
        # self.imageButton = QPushButton('BD_map', self)
        # self.imageButton.setCheckable(True)
        # self.imageButton.clicked.connect(self.mapshow)  # 发送显示地图指令
        # self.imageButton.resize(self.quitButton.sizeHint())
        # self.imageButton.move(150, 320)
        ##====================================================第四层按钮组件


        ##==============================================第一层按钮组件
        # 服务器角色 控件布局
        # 上位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(85, 10)
        self.carIPLabel.setText('上位机')
        # IP Label (20, 20) default size
        self.serverIPLabel = QLabel(self)
        self.serverIPLabel.move(20, 30)
        self.serverIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.serverIPLineEdit = QLineEdit(self)
        self.serverIPLineEdit.move(50, 38)
        self.serverIPLineEdit.resize(120, 15)
        self.serverIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverIPLineEdit.setText(self.myaddr)  # 本地主机的IP
        # IP Label (20, 40) default size
        self.serverPortLabel = QLabel(self)
        self.serverPortLabel.move(20, 50)
        self.serverPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.serverPortLineEdit = QLineEdit(self)
        self.serverPortLineEdit.move(50, 58)
        self.serverPortLineEdit.resize(120, 15)
        self.serverPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverPortLineEdit.setText('7890')  # 自己选取的端口号

        # 客户端角色 控件布局
        # 下位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(255, 10)
        self.carIPLabel.setText('阿里云')
        # IP Label (20, 20) default size
        self.clientIPLabel = QLabel(self)  # IP标签
        self.clientIPLabel.move(190, 30)
        self.clientIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.clientIPLineEdit = QLineEdit(self)  # IP显示文本框
        self.clientIPLineEdit.move(220, 38)
        self.clientIPLineEdit.resize(120, 15)
        self.clientIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        # self.clientIPLineEdit.setText(self.myaddr)
        ######################################################################################
        self.clientIPLineEdit.setText("47.102.36.187")  # 输入自定义IP
        # IP Label (20, 40) default size
        self.clientPortLabel = QLabel(self)  # port标签
        self.clientPortLabel.move(190, 50)
        self.clientPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.clientPortLineEdit = QLineEdit(self)
        self.clientPortLineEdit.move(220, 58)
        self.clientPortLineEdit.resize(120, 15)
        self.clientPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.clientPortLineEdit.setText('8092')
        ##==============================================第一层按钮组件

        ##=========================================================第二层按钮组件
        # 参数设置
        # 车辆长度 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(40, 85)
        self.lengthOfCarLabel.setText('车辆长度:')
        # 车辆长度 Edit  (50, 18) (120, 15)
        self.lengthOfCarLienEdit = QLineEdit(self)
        self.lengthOfCarLienEdit.move(95, 91)
        self.lengthOfCarLienEdit.resize(50, 15)
        self.lengthOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.lengthOfCarLienEdit.setText('1')
        # 车辆长度单位 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(150, 85)
        self.lengthOfCarLabel.setText('m')

        # 车辆重量 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(210, 85)
        self.weightOfCarLabel.setText('车辆重量:')
        # 车辆重量 Edit  (50, 18) (120, 15)
        self.weightOfCarLienEdit = QLineEdit(self)
        self.weightOfCarLienEdit.move(265, 91)
        self.weightOfCarLienEdit.resize(50, 15)
        self.weightOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.weightOfCarLienEdit.setText('1')
        # 车辆重量单位 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(320, 85)
        self.weightOfCarLabel.setText('kg')

        # 最大速度 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(40, 110)
        self.maxVelocityOfCarLabel.setText('最大速度:')
        # 最大速度 Edit  (50, 18) (120, 15)
        self.maxVelocityOfCarLienEdit = QLineEdit(self)
        self.maxVelocityOfCarLienEdit.move(95, 116)
        self.maxVelocityOfCarLienEdit.resize(50, 15)
        self.maxVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxVelocityOfCarLienEdit.setText('1')
        # 最大速度单位 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(150, 110)
        self.maxVelocityOfCarLabel.setText('m/s')

        # 最小速度 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(210, 110)
        self.minVelocityOfCarLabel.setText('最小速度:')
        # 最小速度 Edit  (50, 18) (120, 15)
        self.minVelocityOfCarLienEdit = QLineEdit(self)
        self.minVelocityOfCarLienEdit.move(265, 116)
        self.minVelocityOfCarLienEdit.resize(50, 15)
        self.minVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.minVelocityOfCarLienEdit.setText('1')
        # 最小速度单位 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(320, 110)
        self.minVelocityOfCarLabel.setText('m/s')

        # 最大加速度 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(30, 135)
        self.maxAccelationOfCarLabel.setText('最大加速度:')
        # 最大加速度 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 141)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 最大加速度单位 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 135)
        self.maxAccelationOfCarLabel.setText('m/s^2')

        # 最大减速度 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(200, 135)
        self.maxDecelerationOfCarLabel.setText('最大减速度:')
        # 最大减速度 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 141)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 最大减速度单位 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 135)
        self.maxDecelerationOfCarLabel.setText('m/s^2')

        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(40, 160)
        self.maxAccelationOfCarLabel.setText('转动惯量:')
        # 转动惯量 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 166)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 160)
        self.maxAccelationOfCarLabel.setText('kg·m^2')

        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(235, 160)
        self.maxDecelerationOfCarLabel.setText('轴距:')
        # 轴距 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 166)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 160)
        self.maxDecelerationOfCarLabel.setText('m')





        ##=========================================================第二层按钮组件


        ##======================================================第三层按钮组件
        # 数据显示部分
        # 车辆ID
        self.IDLabel = QLabel(self)
        self.IDLabel.move(65, 190)
        self.IDLabel.setText('车辆编号:')
        self.IDChangeLabel = QLabel(self)
        self.IDChangeLabel.move(120, 190)
        self.IDChangeLabel.setText('xx')

        # 左轮速度
        self.L2vLabel = QLabel(self)
        self.L2vLabel.move(65, 210)
        self.L2vLabel.setText('左轮电机速度:')
        self.L2vChangeLabel = QLabel(self)
        self.L2vChangeLabel.move(145, 210)
        self.L2vChangeLabel.setText('xxxx')
        self.L2vUnitLabel = QLabel(self)
        self.L2vUnitLabel.move(170, 210)
        self.L2vUnitLabel.setText('cm/s')

        # 右轮速度
        self.R2vLabel = QLabel(self)
        self.R2vLabel.move(210, 210)
        self.R2vLabel.setText('右轮电机速度:')
        self.R2vChangeLabel = QLabel(self)
        self.R2vChangeLabel.move(290, 210)
        self.R2vChangeLabel.setText('xxxxx')
        self.R2vUnitLabel = QLabel(self)
        self.R2vUnitLabel.move(320, 210)
        self.R2vUnitLabel.setText('cm/s')

        # 舵机转角
        self.angleLabel = QLabel(self)
        self.angleLabel.move(210, 230)
        self.angleLabel.setText('转向角度:')
        self.angleChangeLabel = QLabel(self)
        self.angleChangeLabel.move(265, 230)
        self.angleChangeLabel.setText('xxxx')
        self.angleUnitLabel = QLabel(self)
        self.angleUnitLabel.move(295, 230)
        self.angleUnitLabel.setText('°')

        # 车辆状态
        self.LPWMLabel = QLabel(self)
        self.LPWMLabel.move(210, 190)
        self.LPWMLabel.setText('车辆状态:')
        self.LPWMChangeLabel = QLabel(self)
        self.LPWMChangeLabel.move(265, 190)
        self.LPWMChangeLabel.setText('xxxx')

        # 电池电压
        self.RPWMLabel = QLabel(self)
        self.RPWMLabel.move(65, 230)
        self.RPWMLabel.setText('电池电压:')
        self.RPWMChangeLabel = QLabel(self)
        self.RPWMChangeLabel.move(120, 230)
        self.RPWMChangeLabel.setText('xxxx')
        self.RPWMUnitLabel = QLabel(self)
        self.RPWMUnitLabel.move(150, 230)
        self.RPWMUnitLabel.setText('v')

        # 横向加速度
        self.AyLabel = QLabel(self)
        self.AyLabel.move(65, 250)
        self.AyLabel.setText('横向加速度:')
        self.AyChangeLabel = QLabel(self)
        self.AyChangeLabel.move(135, 250)
        self.AyChangeLabel.setText('xxxx')
        self.AyUnitLabel = QLabel(self)
        self.AyUnitLabel.move(165, 250)
        self.AyUnitLabel.setText('m/s^2')

        # 横摆角速度
        self.YawLabel = QLabel(self)
        self.YawLabel.move(210, 250)
        self.YawLabel.setText('横摆角速度:')
        self.YawChangeLabel = QLabel(self)
        self.YawChangeLabel.move(280, 250)
        self.YawChangeLabel.setText('xxxx')
        self.YawUnitLabel = QLabel(self)
        self.YawUnitLabel.move(310, 250)
        self.YawUnitLabel.setText('°/s')

        # 电机转矩
        self.TnLabel = QLabel(self)
        self.TnLabel.move(210, 270)
        self.TnLabel.setText('电机转矩:')
        self.TnChangeLabel = QLabel(self)
        self.TnChangeLabel.move(265, 270)
        self.TnChangeLabel.setText('xxxx')
        self.TnUnitLabel = QLabel(self)
        self.TnUnitLabel.move(295, 270)
        self.TnUnitLabel.setText('N·m')

        # 横向速度
        self.VyLabel = QLabel(self)
        self.VyLabel.move(65, 270)
        self.VyLabel.setText('横向速度:')
        self.VyChangeLabel = QLabel(self)
        self.VyChangeLabel.move(125, 270)
        self.VyChangeLabel.setText('xxxx')
        self.VyUnitLabel = QLabel(self)
        self.VyUnitLabel.move(155, 270)
        self.VyUnitLabel.setText('m/s')

        # 当前经度
        self.lngLabel = QLabel(self)
        self.lngLabel.move(65, 300)
        self.lngLabel.setText('当前经度:')
        self.lngChangeLabel = QLabel(self)
        self.lngChangeLabel.move(120, 300)
        self.lngChangeLabel.setText('xxxx')
        self.lngUnitLabel = QLabel(self)
        self.lngUnitLabel.move(250, 300)
        self.lngUnitLabel.setText('°')

        # 当前纬度
        self.latLabel = QLabel(self)
        self.latLabel.move(65, 320)
        self.latLabel.setText('当前纬度:')
        self.latChangeLabel = QLabel(self)
        self.latChangeLabel.move(120, 320)
        self.latChangeLabel.setText('xxxx')
        # self.latChangeLabel.setGeometry(QRect(328, 240, 329, 27 * 4))
        # self.latChangeLabel.setWordWrap(True)
        # self.latChangeLabel.setAlignment(Qt.AlignTop)
        self.latUnitLabel = QLabel(self)
        self.latUnitLabel.move(250, 320)
        self.latUnitLabel.setText('°')



        ## 下位机上传的图像信息
        self.angleLabel = QLabel(self)
        self.angleLabel.move(400, 150)
        self.angleLabel.setText('图像:')

        pix = QPixmap('background.jpg')
        self.lb1 = QLabel(self)
        self.lb1.setGeometry(450, 5, 400, 200)  # x1 x2 x3 x4,从（x1,x2）开始显示一个x3长x4宽的矩形
        self.lb1.setPixmap(QPixmap('background.jpg'))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
        self.lb1.setStyleSheet("border: 2px solid red")


        # 方法三
        self.angleLabel = QLabel(self)  # 标签
        self.angleLabel.move(390, 350)
        self.angleLabel.setText('导航图像:')
        # 调用Mapwindow函数，建立一个他的对象
        SettingBox_Map1 = QGroupBox("导航地图")
        Map1 = Map_load2()
        v_map1_layout = QVBoxLayout()
        v_map1_layout.addWidget(Map1)
        v_map1_layout.setContentsMargins(450, 200, 50, 50)  # 左上右下距离边框的长度
        self.setLayout(v_map1_layout)
        # QApplication.processEvents()  # 使得图像界面可以实时更新


        # 状态栏显示
        # self.setGeometry(100, 100, 370, 550)
        self.setGeometry(100, 100, 900, 450)
        self.setWindowTitle('Sixth')
        self.show()

    def slot_btn_function(self):
        # self.hide()
        self.f1 = First_ID1()
        self.f1.show()



    ## 响应槽函数
    def mapshow(self, text):
        map = (Map().add(text, [list(z) for z in zip(Faker.provinces, Faker.values())], text)
               .set_global_opts(title_opts=opts.TitleOpts(title="map")))
        map.render('BD_map6.html')  # 读取对应车辆的百度地图API程序
        # self.browser.load(QUrl(QFileInfo("file:///E:/pycharm_project/TCP%2010%2025/BD_map.html").absoluteFilePath()))
        self.browser.load(QUrl(QFileInfo("BD_map6.html").absoluteFilePath()))
        print("更新BD地图============")
        if text in self.knowledge:
            self.knowledge_label.setText(self.knowledge[text])
        else:
            self.knowledge_label.setText('')

    def IDchange(self,ID):  # 更新车辆ID的槽函数
        self.IDChangeLabel.setText(ID)

    def Statechange(self,State):  # 更新车辆状态
        self.StatechangeLable.setText(str(State))


    def L2vchange(self, L2v):  # 更新左轮电机转速的槽函数
        self.L2vChangeLabel.setText(str(L2v))

    def R2vchange(self, R2v):  # 更新右轮电机转速的槽函数
        self.R2vChangeLabel.setText(str(R2v))
    def anglechange(self, angle):  # 更新转向角度的槽函数
        self.angleChangeLabel.setText(str(angle))

    def Uchange(self,U):
        self.UchangeLabel.setText(U)

    def LPWMchange(self, LPWM):
        self.LPWMChangeLabel.setText(str(LPWM))

    def RPWMchange(self,RPWM):
        self.RPWMChangeLabel.setText(str(RPWM))

    def Aychange(self,Ay):
        self.AyChangeLabel.setText(str(Ay))

    def Yawchange(self,Yaw):
        self.YawChangeLabel.setText(str(Yaw))

    def Tnchange(self,Tn):
        self.TnChangeLabel.setText(str(Tn))

    def Vychange(self,Vy):
        self.VyChangeLabel.setText(str(Vy))


    def lngChange(self,lng):
        self.lngChangeLabel.setText(str(lng))

    def latChange(self,lat):
        self.latChangeLabel.setText(str(lat))


    # 修改显示的图像
    def QPixmapchange(self,Image):
        self.lb1.setPixmap(QPixmap(str(Image)))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
    # 修改显示的图像


    def start(self):  # start按钮的槽函数
        global startFlag
        startFlag = 1



    def listenToClient(self):  # 点击Listen后的响应事件
        localIP = self.serverIPLineEdit.text()  # 定义Listener类中的属性值
        localPort = self.serverPortLineEdit.text()
        serverIP = self.clientIPLineEdit.text()
        serverPort = self.clientPortLineEdit.text()
        length = self.lengthOfCarLienEdit.text()
        weight = self.weightOfCarLienEdit.text()
        maxV = self.maxVelocityOfCarLienEdit.text()
        minV = self.minVelocityOfCarLienEdit.text()
        maxA = self.maxAccelationOfCarLienEdit.text()
        maxD = self.maxDecelerationOfCarLienEdit.text()
        self._thread = Listener_ID6(localIP, int(localPort), serverIP, int(serverPort),
                                int(length), int(weight), int(maxV),
                                int(minV), int(maxA), int(maxD))  # 定义一个Listener的对象
        self._thread.sigID_ID6.connect(self.IDchange)  # 调用修改参数方法，实时传输显示下位机传输的数据
        self._thread.sigRPWM_ID6.connect(self.RPWMchange)
        self._thread.sigLPWM_ID6.connect(self.LPWMchange)
        self._thread.sigL2v_ID6.connect(self.L2vchange)
        self._thread.sigR2v_ID6.connect(self.R2vchange)
        self._thread.sigangle_ID6.connect(self.anglechange)
        self._thread.sigImage_ID6.connect(self.QPixmapchange)  # 更新显示的图片

        self._thread.sigAy_ID6.connect(self.Aychange)
        self._thread.sigYaw_ID6.connect(self.Yawchange)
        self._thread.sigTn_ID6.connect(self.Tnchange)
        self._thread.sigVy_ID6.connect(self.Vychange)

        self._thread.siglat_ID6.connect(self.latChange)
        self._thread.siglng_ID6.connect(self.lngChange)  # 更新当前经纬度数据


        self._thread.start()  # 执行Litener类中的run方法
        self.listenButton.setText('Listening')  # 开始执行监听后标识为“正在监听”




    def askstate(self):  # askstate按钮的槽函数
        global askstateFlag_ID6
        askstateFlag_ID6 = 1
        print('askstateFlag_ID6_change_to:', askstateFlag_ID6)

    def askimage(self):  # askimage按钮的槽函数
        global askimageFlag_ID6
        askimageFlag_ID6 = 1
        print('askimageFlag_ID6_change_to:', askimageFlag_ID6)

        # self._thread = Image_listen()
        # self._thread.start()

    def send(self):  # send按钮的槽函数
        global sendFlag_ID6
        sendFlag_ID6 = 1
        print('sendFlag_ID6_change_to:', sendFlag_ID6)




    def closeEvent(self, event):  # GUI窗口右上角关闭按钮的槽函数
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# 第七辆车
class Seventh_ID7(QWidget):

    serverSig = pyqtSignal()  # 申明无参数信号

    def __init__(self):  # 初始化
        self.myname = socket.getfqdn(socket.gethostname())  # gethostname() ： 返回本地主机的标准主机名。
        self.myaddr = socket.gethostbyname(self.myname)  # gethostbyname()：用域名或主机名获取IP地址
        super(Seventh_ID7, self).__init__()  # 继承父类的属性和方法
        self.initUI()  # 调用自己的方法

    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)

        if int(i) == 1:  ## 传过来的是str型参数，转换成int型才可
            # self.hide()
            self.f1 = First_ID1()
            self.f1.show()

        elif int(i) == 2:
            # self.hide()
            self.s2 = Second_ID2()
            self.s2.show()

        elif int(i) == 3:
            # self.hide()
            self.t3 = Third_ID3()
            self.t3.show()

        elif int(i) == 4:
            # self.hide()
            self.f4 = Forth_ID4()
            self.f4.show()

        elif int(i) == 5:
            # self.hide()
            self.f5 = Fifth_ID5()
            self.f5.show()

        elif int(i) == 6:
            # self.hide()
            self.s6 = Sixth_ID6()
            self.s6.show()

        elif int(i) == 8:
            # self.hide()
            self.e8 = Eighth_ID8()
            self.e8.show()

        elif int(i) == 9:
            # self.hide()
            self.n9 = Ninth_ID9()
            self.n9.show()

        elif int(i) == 10:
            # self.hide()
            self.t10 = Tenth_ID10()
            self.t10.show()

    def initUI(self):

        self.btn = QPushButton('jump to FirstUI', self)  # 用来返回到第一个界面
        self.btn.setGeometry(350, 50, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function)

        self.cb = QComboBox(self)
        self.cb.move(350, 10)
        self.cb.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容

        ##=======================================================第四层按钮组件
        # 退出按钮
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(QCoreApplication.instance().quit)  # 信号与槽，槽可以是QT内置的槽也可以是python内置方法
        self.quitButton.resize(self.quitButton.sizeHint())  # sizeHint()提供一个推荐大小
        self.quitButton.move(50, 360)  # 放置位子
        # 监听按钮
        self.listenButton = QPushButton('Listen', self)
        self.listenButton.setCheckable(True)  # 可以点击
        self.listenButton.clicked.connect(self.listenToClient)  # 链接到槽方法listenToClient,开始监听
        self.listenButton.resize(self.quitButton.sizeHint())  # 和quitButton按钮一样大
        self.listenButton.move(250, 360)  # 改变大小并移动

        #  开始按钮
        self.startButton = QPushButton('Start', self)
        self.startButton.setCheckable(True)
        self.startButton.clicked.connect(self.start)  # self.StartFlag = 1,表示开始向下位机发送数据
        self.startButton.resize(self.quitButton.sizeHint())
        self.startButton.move(50, 400)

        #  发送第一组数据按钮
        self.sendButton = QPushButton('Send', self)
        self.sendButton.setCheckable(True)
        self.sendButton.clicked.connect(self.send)  # 发送第一组经纬度
        self.sendButton.resize(self.quitButton.sizeHint())
        self.sendButton.move(250, 400)

        #  请求车辆的状态
        self.stateButton = QPushButton('AskState', self)
        self.stateButton.setCheckable(True)
        self.stateButton.clicked.connect(self.askstate)  # 发送停止信号 “ST”
        self.stateButton.resize(self.quitButton.sizeHint())
        self.stateButton.move(150, 360)

        #  请求车辆的图像
        self.imageButton = QPushButton('AskImage', self)
        self.imageButton.setCheckable(True)
        self.imageButton.clicked.connect(self.askimage)  # 发送停止信号 “ST”
        self.imageButton.resize(self.quitButton.sizeHint())
        self.imageButton.move(150, 400)

        #  请求百度地图
        # self.imageButton = QPushButton('BD_map', self)
        # self.imageButton.setCheckable(True)
        # self.imageButton.clicked.connect(self.mapshow)  # 发送显示地图指令
        # self.imageButton.resize(self.quitButton.sizeHint())
        # self.imageButton.move(150, 320)
        ##====================================================第四层按钮组件


        ##==============================================第一层按钮组件
        # 服务器角色 控件布局
        # 上位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(85, 10)
        self.carIPLabel.setText('上位机')
        # IP Label (20, 20) default size
        self.serverIPLabel = QLabel(self)
        self.serverIPLabel.move(20, 30)
        self.serverIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.serverIPLineEdit = QLineEdit(self)
        self.serverIPLineEdit.move(50, 38)
        self.serverIPLineEdit.resize(120, 15)
        self.serverIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverIPLineEdit.setText(self.myaddr)  # 本地主机的IP
        # IP Label (20, 40) default size
        self.serverPortLabel = QLabel(self)
        self.serverPortLabel.move(20, 50)
        self.serverPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.serverPortLineEdit = QLineEdit(self)
        self.serverPortLineEdit.move(50, 58)
        self.serverPortLineEdit.resize(120, 15)
        self.serverPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverPortLineEdit.setText('7890')  # 自己选取的端口号

        # 客户端角色 控件布局
        # 下位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(255, 10)
        self.carIPLabel.setText('阿里云')
        # IP Label (20, 20) default size
        self.clientIPLabel = QLabel(self)  # IP标签
        self.clientIPLabel.move(190, 30)
        self.clientIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.clientIPLineEdit = QLineEdit(self)  # IP显示文本框
        self.clientIPLineEdit.move(220, 38)
        self.clientIPLineEdit.resize(120, 15)
        self.clientIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        # self.clientIPLineEdit.setText(self.myaddr)
        ######################################################################################
        self.clientIPLineEdit.setText("47.102.36.187")  # 输入自定义IP
        # IP Label (20, 40) default size
        self.clientPortLabel = QLabel(self)  # port标签
        self.clientPortLabel.move(190, 50)
        self.clientPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.clientPortLineEdit = QLineEdit(self)
        self.clientPortLineEdit.move(220, 58)
        self.clientPortLineEdit.resize(120, 15)
        self.clientPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.clientPortLineEdit.setText('8094')
        ##==============================================第一层按钮组件

        ##=========================================================第二层按钮组件
        # 参数设置
        # 车辆长度 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(40, 85)
        self.lengthOfCarLabel.setText('车辆长度:')
        # 车辆长度 Edit  (50, 18) (120, 15)
        self.lengthOfCarLienEdit = QLineEdit(self)
        self.lengthOfCarLienEdit.move(95, 91)
        self.lengthOfCarLienEdit.resize(50, 15)
        self.lengthOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.lengthOfCarLienEdit.setText('1')
        # 车辆长度单位 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(150, 85)
        self.lengthOfCarLabel.setText('m')

        # 车辆重量 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(210, 85)
        self.weightOfCarLabel.setText('车辆重量:')
        # 车辆重量 Edit  (50, 18) (120, 15)
        self.weightOfCarLienEdit = QLineEdit(self)
        self.weightOfCarLienEdit.move(265, 91)
        self.weightOfCarLienEdit.resize(50, 15)
        self.weightOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.weightOfCarLienEdit.setText('1')
        # 车辆重量单位 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(320, 85)
        self.weightOfCarLabel.setText('kg')

        # 最大速度 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(40, 110)
        self.maxVelocityOfCarLabel.setText('最大速度:')
        # 最大速度 Edit  (50, 18) (120, 15)
        self.maxVelocityOfCarLienEdit = QLineEdit(self)
        self.maxVelocityOfCarLienEdit.move(95, 116)
        self.maxVelocityOfCarLienEdit.resize(50, 15)
        self.maxVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxVelocityOfCarLienEdit.setText('1')
        # 最大速度单位 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(150, 110)
        self.maxVelocityOfCarLabel.setText('m/s')

        # 最小速度 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(210, 110)
        self.minVelocityOfCarLabel.setText('最小速度:')
        # 最小速度 Edit  (50, 18) (120, 15)
        self.minVelocityOfCarLienEdit = QLineEdit(self)
        self.minVelocityOfCarLienEdit.move(265, 116)
        self.minVelocityOfCarLienEdit.resize(50, 15)
        self.minVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.minVelocityOfCarLienEdit.setText('1')
        # 最小速度单位 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(320, 110)
        self.minVelocityOfCarLabel.setText('m/s')

        # 最大加速度 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(30, 135)
        self.maxAccelationOfCarLabel.setText('最大加速度:')
        # 最大加速度 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 141)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 最大加速度单位 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 135)
        self.maxAccelationOfCarLabel.setText('m/s^2')

        # 最大减速度 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(200, 135)
        self.maxDecelerationOfCarLabel.setText('最大减速度:')
        # 最大减速度 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 141)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 最大减速度单位 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 135)
        self.maxDecelerationOfCarLabel.setText('m/s^2')

        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(40, 160)
        self.maxAccelationOfCarLabel.setText('转动惯量:')
        # 转动惯量 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 166)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 160)
        self.maxAccelationOfCarLabel.setText('kg·m^2')

        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(235, 160)
        self.maxDecelerationOfCarLabel.setText('轴距:')
        # 轴距 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 166)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 160)
        self.maxDecelerationOfCarLabel.setText('m')





        ##=========================================================第二层按钮组件


        ##======================================================第三层按钮组件
        # 数据显示部分
        # 车辆ID
        self.IDLabel = QLabel(self)
        self.IDLabel.move(65, 190)
        self.IDLabel.setText('车辆编号:')
        self.IDChangeLabel = QLabel(self)
        self.IDChangeLabel.move(120, 190)
        self.IDChangeLabel.setText('xx')

        # 左轮速度
        self.L2vLabel = QLabel(self)
        self.L2vLabel.move(65, 210)
        self.L2vLabel.setText('左轮电机速度:')
        self.L2vChangeLabel = QLabel(self)
        self.L2vChangeLabel.move(145, 210)
        self.L2vChangeLabel.setText('xxxx')
        self.L2vUnitLabel = QLabel(self)
        self.L2vUnitLabel.move(170, 210)
        self.L2vUnitLabel.setText('cm/s')

        # 右轮速度
        self.R2vLabel = QLabel(self)
        self.R2vLabel.move(210, 210)
        self.R2vLabel.setText('右轮电机速度:')
        self.R2vChangeLabel = QLabel(self)
        self.R2vChangeLabel.move(290, 210)
        self.R2vChangeLabel.setText('xxxxx')
        self.R2vUnitLabel = QLabel(self)
        self.R2vUnitLabel.move(320, 210)
        self.R2vUnitLabel.setText('cm/s')

        # 舵机转角
        self.angleLabel = QLabel(self)
        self.angleLabel.move(210, 230)
        self.angleLabel.setText('转向角度:')
        self.angleChangeLabel = QLabel(self)
        self.angleChangeLabel.move(265, 230)
        self.angleChangeLabel.setText('xxxx')
        self.angleUnitLabel = QLabel(self)
        self.angleUnitLabel.move(295, 230)
        self.angleUnitLabel.setText('°')

        # 车辆状态
        self.LPWMLabel = QLabel(self)
        self.LPWMLabel.move(210, 190)
        self.LPWMLabel.setText('车辆状态:')
        self.LPWMChangeLabel = QLabel(self)
        self.LPWMChangeLabel.move(265, 190)
        self.LPWMChangeLabel.setText('xxxx')

        # 电池电压
        self.RPWMLabel = QLabel(self)
        self.RPWMLabel.move(65, 230)
        self.RPWMLabel.setText('电池电压:')
        self.RPWMChangeLabel = QLabel(self)
        self.RPWMChangeLabel.move(120, 230)
        self.RPWMChangeLabel.setText('xxxx')
        self.RPWMUnitLabel = QLabel(self)
        self.RPWMUnitLabel.move(150, 230)
        self.RPWMUnitLabel.setText('v')

        # 横向加速度
        self.AyLabel = QLabel(self)
        self.AyLabel.move(65, 250)
        self.AyLabel.setText('横向加速度:')
        self.AyChangeLabel = QLabel(self)
        self.AyChangeLabel.move(135, 250)
        self.AyChangeLabel.setText('xxxx')
        self.AyUnitLabel = QLabel(self)
        self.AyUnitLabel.move(165, 250)
        self.AyUnitLabel.setText('m/s^2')

        # 横摆角速度
        self.YawLabel = QLabel(self)
        self.YawLabel.move(210, 250)
        self.YawLabel.setText('横摆角速度:')
        self.YawChangeLabel = QLabel(self)
        self.YawChangeLabel.move(280, 250)
        self.YawChangeLabel.setText('xxxx')
        self.YawUnitLabel = QLabel(self)
        self.YawUnitLabel.move(310, 250)
        self.YawUnitLabel.setText('°/s')

        # 电机转矩
        self.TnLabel = QLabel(self)
        self.TnLabel.move(210, 270)
        self.TnLabel.setText('电机转矩:')
        self.TnChangeLabel = QLabel(self)
        self.TnChangeLabel.move(265, 270)
        self.TnChangeLabel.setText('xxxx')
        self.TnUnitLabel = QLabel(self)
        self.TnUnitLabel.move(295, 270)
        self.TnUnitLabel.setText('N·m')

        # 横向速度
        self.VyLabel = QLabel(self)
        self.VyLabel.move(65, 270)
        self.VyLabel.setText('横向速度:')
        self.VyChangeLabel = QLabel(self)
        self.VyChangeLabel.move(125, 270)
        self.VyChangeLabel.setText('xxxx')
        self.VyUnitLabel = QLabel(self)
        self.VyUnitLabel.move(155, 270)
        self.VyUnitLabel.setText('m/s')

        # 当前经度
        self.lngLabel = QLabel(self)
        self.lngLabel.move(65, 300)
        self.lngLabel.setText('当前经度:')
        self.lngChangeLabel = QLabel(self)
        self.lngChangeLabel.move(120, 300)
        self.lngChangeLabel.setText('xxxx')
        self.lngUnitLabel = QLabel(self)
        self.lngUnitLabel.move(250, 300)
        self.lngUnitLabel.setText('°')

        # 当前纬度
        self.latLabel = QLabel(self)
        self.latLabel.move(65, 320)
        self.latLabel.setText('当前纬度:')
        self.latChangeLabel = QLabel(self)
        self.latChangeLabel.move(120, 320)
        self.latChangeLabel.setText('xxxx')
        # self.latChangeLabel.setGeometry(QRect(328, 240, 329, 27 * 4))
        # self.latChangeLabel.setWordWrap(True)
        # self.latChangeLabel.setAlignment(Qt.AlignTop)
        self.latUnitLabel = QLabel(self)
        self.latUnitLabel.move(250, 320)
        self.latUnitLabel.setText('°')



        ## 下位机上传的图像信息
        self.angleLabel = QLabel(self)
        self.angleLabel.move(400, 150)
        self.angleLabel.setText('图像:')

        pix = QPixmap('background.jpg')
        self.lb1 = QLabel(self)
        self.lb1.setGeometry(450, 5, 400, 200)  # x1 x2 x3 x4,从（x1,x2）开始显示一个x3长x4宽的矩形
        self.lb1.setPixmap(QPixmap('background.jpg'))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
        self.lb1.setStyleSheet("border: 2px solid red")


        # 方法三
        self.angleLabel = QLabel(self)  # 标签
        self.angleLabel.move(390, 350)
        self.angleLabel.setText('导航图像:')
        # 调用Mapwindow函数，建立一个他的对象
        SettingBox_Map1 = QGroupBox("导航地图")
        Map1 = Map_load2()
        v_map1_layout = QVBoxLayout()
        v_map1_layout.addWidget(Map1)
        v_map1_layout.setContentsMargins(450, 200, 50, 50)  # 左上右下距离边框的长度
        self.setLayout(v_map1_layout)
        # QApplication.processEvents()  # 使得图像界面可以实时更新


        # 状态栏显示
        # self.setGeometry(100, 100, 370, 550)
        self.setGeometry(100, 100, 900, 450)
        self.setWindowTitle('Seventh')
        self.show()

    def slot_btn_function(self):
        # self.hide()
        self.f1 = First_ID1()
        self.f1.show()



    ## 响应槽函数
    def mapshow(self, text):
        map = (Map().add(text, [list(z) for z in zip(Faker.provinces, Faker.values())], text)
               .set_global_opts(title_opts=opts.TitleOpts(title="map")))
        map.render('BD_map7.html')  # 读取对应车辆的百度地图API程序
        # self.browser.load(QUrl(QFileInfo("file:///E:/pycharm_project/TCP%2010%2025/BD_map.html").absoluteFilePath()))
        self.browser.load(QUrl(QFileInfo("BD_map7.html").absoluteFilePath()))
        print("更新BD地图============")
        if text in self.knowledge:
            self.knowledge_label.setText(self.knowledge[text])
        else:
            self.knowledge_label.setText('')

    def IDchange(self,ID):  # 更新车辆ID的槽函数
        self.IDChangeLabel.setText(ID)

    def Statechange(self,State):  # 更新车辆状态
        self.StatechangeLable.setText(str(State))


    def L2vchange(self, L2v):  # 更新左轮电机转速的槽函数
        self.L2vChangeLabel.setText(str(L2v))

    def R2vchange(self, R2v):  # 更新右轮电机转速的槽函数
        self.R2vChangeLabel.setText(str(R2v))
    def anglechange(self, angle):  # 更新转向角度的槽函数
        self.angleChangeLabel.setText(str(angle))

    def Uchange(self,U):
        self.UchangeLabel.setText(U)

    def LPWMchange(self, LPWM):
        self.LPWMChangeLabel.setText(str(LPWM))

    def RPWMchange(self,RPWM):
        self.RPWMChangeLabel.setText(str(RPWM))

    def Aychange(self,Ay):
        self.AyChangeLabel.setText(str(Ay))

    def Yawchange(self,Yaw):
        self.YawChangeLabel.setText(str(Yaw))

    def Tnchange(self,Tn):
        self.TnChangeLabel.setText(str(Tn))

    def Vychange(self,Vy):
        self.VyChangeLabel.setText(str(Vy))


    def lngChange(self,lng):
        self.lngChangeLabel.setText(str(lng))

    def latChange(self,lat):
        self.latChangeLabel.setText(str(lat))


    # 修改显示的图像
    def QPixmapchange(self,Image):
        self.lb1.setPixmap(QPixmap(str(Image)))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
    # 修改显示的图像


    def start(self):  # start按钮的槽函数
        global startFlag
        startFlag = 1



    def listenToClient(self):  # 点击Listen后的响应事件
        localIP = self.serverIPLineEdit.text()  # 定义Listener类中的属性值
        localPort = self.serverPortLineEdit.text()
        serverIP = self.clientIPLineEdit.text()
        serverPort = self.clientPortLineEdit.text()
        length = self.lengthOfCarLienEdit.text()
        weight = self.weightOfCarLienEdit.text()
        maxV = self.maxVelocityOfCarLienEdit.text()
        minV = self.minVelocityOfCarLienEdit.text()
        maxA = self.maxAccelationOfCarLienEdit.text()
        maxD = self.maxDecelerationOfCarLienEdit.text()
        self._thread = Listener_ID7(localIP, int(localPort), serverIP, int(serverPort),
                                int(length), int(weight), int(maxV),
                                int(minV), int(maxA), int(maxD))  # 定义一个Listener的对象
        self._thread.sigID_ID7.connect(self.IDchange)  # 调用修改参数方法，实时传输显示下位机传输的数据
        self._thread.sigRPWM_ID7.connect(self.RPWMchange)
        self._thread.sigLPWM_ID7.connect(self.LPWMchange)
        self._thread.sigL2v_ID7.connect(self.L2vchange)
        self._thread.sigR2v_ID7.connect(self.R2vchange)
        self._thread.sigangle_ID7.connect(self.anglechange)
        self._thread.sigImage_ID7.connect(self.QPixmapchange)  # 更新显示的图片

        self._thread.sigAy_ID7.connect(self.Aychange)
        self._thread.sigYaw_ID7.connect(self.Yawchange)
        self._thread.sigTn_ID7.connect(self.Tnchange)
        self._thread.sigVy_ID7.connect(self.Vychange)

        self._thread.siglat_ID7.connect(self.latChange)
        self._thread.siglng_ID7.connect(self.lngChange)  # 更新当前经纬度数据


        self._thread.start()  # 执行Litener类中的run方法
        self.listenButton.setText('Listening')  # 开始执行监听后标识为“正在监听”




    def askstate(self):  # askstate按钮的槽函数
        global askstateFlag_ID7
        askstateFlag_ID7 = 1
        print('askstateFlag_ID7_change_to:', askstateFlag_ID7)

    def askimage(self):  # askimage按钮的槽函数
        global askimageFlag_ID7
        askimageFlag_ID7 = 1
        print('askimageFlag_ID7_change_to:', askimageFlag_ID7)

        # self._thread = Image_listen()
        # self._thread.start()

    def send(self):  # send按钮的槽函数
        global sendFlag_ID7
        sendFlag_ID7 = 1
        print('sendFlag_ID7_change_to:', sendFlag_ID7)




    def closeEvent(self, event):  # GUI窗口右上角关闭按钮的槽函数
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# 第八辆车
class Eighth_ID8(QWidget):

    serverSig = pyqtSignal()  # 申明无参数信号

    def __init__(self):  # 初始化
        self.myname = socket.getfqdn(socket.gethostname())  # gethostname() ： 返回本地主机的标准主机名。
        self.myaddr = socket.gethostbyname(self.myname)  # gethostbyname()：用域名或主机名获取IP地址
        super(Eighth_ID8, self).__init__()  # 继承父类的属性和方法
        self.initUI()  # 调用自己的方法

    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)

        if int(i) == 1:  ## 传过来的是str型参数，转换成int型才可
            # self.hide()
            self.f1 = First_ID1()
            self.f1.show()

        elif int(i) == 2:
            # self.hide()
            self.s2 = Second_ID2()
            self.s2.show()

        elif int(i) == 3:
            # self.hide()
            self.t3 = Third_ID3()
            self.t3.show()

        elif int(i) == 4:
            # self.hide()
            self.f4 = Forth_ID4()
            self.f4.show()

        elif int(i) == 5:
            # self.hide()
            self.f5 = Fifth_ID5()
            self.f5.show()

        elif int(i) == 6:
            # self.hide()
            self.s6 = Sixth_ID6()
            self.s6.show()

        elif int(i) == 7:
            # self.hide()
            self.s7 = Seventh_ID7()
            self.s7.show()

        elif int(i) == 9:
            # self.hide()
            self.n9 = Ninth_ID9()
            self.n9.show()

        elif int(i) == 10:
            # self.hide()
            self.t10 = Tenth_ID10()
            self.t10.show()

    def initUI(self):

        self.btn = QPushButton('jump to FirstUI', self)  # 用来返回到第一个界面
        self.btn.setGeometry(350, 50, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function)

        self.cb = QComboBox(self)
        self.cb.move(350, 10)
        self.cb.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容

        ##=======================================================第四层按钮组件
        # 退出按钮
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(QCoreApplication.instance().quit)  # 信号与槽，槽可以是QT内置的槽也可以是python内置方法
        self.quitButton.resize(self.quitButton.sizeHint())  # sizeHint()提供一个推荐大小
        self.quitButton.move(50, 360)  # 放置位子
        # 监听按钮
        self.listenButton = QPushButton('Listen', self)
        self.listenButton.setCheckable(True)  # 可以点击
        self.listenButton.clicked.connect(self.listenToClient)  # 链接到槽方法listenToClient,开始监听
        self.listenButton.resize(self.quitButton.sizeHint())  # 和quitButton按钮一样大
        self.listenButton.move(250, 360)  # 改变大小并移动

        #  开始按钮
        self.startButton = QPushButton('Start', self)
        self.startButton.setCheckable(True)
        self.startButton.clicked.connect(self.start)  # self.StartFlag = 1,表示开始向下位机发送数据
        self.startButton.resize(self.quitButton.sizeHint())
        self.startButton.move(50, 400)

        #  发送第一组数据按钮
        self.sendButton = QPushButton('Send', self)
        self.sendButton.setCheckable(True)
        self.sendButton.clicked.connect(self.send)  # 发送第一组经纬度
        self.sendButton.resize(self.quitButton.sizeHint())
        self.sendButton.move(250, 400)

        #  请求车辆的状态
        self.stateButton = QPushButton('AskState', self)
        self.stateButton.setCheckable(True)
        self.stateButton.clicked.connect(self.askstate)  # 发送停止信号 “ST”
        self.stateButton.resize(self.quitButton.sizeHint())
        self.stateButton.move(150, 360)

        #  请求车辆的图像
        self.imageButton = QPushButton('AskImage', self)
        self.imageButton.setCheckable(True)
        self.imageButton.clicked.connect(self.askimage)  # 发送停止信号 “ST”
        self.imageButton.resize(self.quitButton.sizeHint())
        self.imageButton.move(150, 400)

        #  请求百度地图
        # self.imageButton = QPushButton('BD_map', self)
        # self.imageButton.setCheckable(True)
        # self.imageButton.clicked.connect(self.mapshow)  # 发送显示地图指令
        # self.imageButton.resize(self.quitButton.sizeHint())
        # self.imageButton.move(150, 320)
        ##====================================================第四层按钮组件


        ##==============================================第一层按钮组件
        # 服务器角色 控件布局
        # 上位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(85, 10)
        self.carIPLabel.setText('上位机')
        # IP Label (20, 20) default size
        self.serverIPLabel = QLabel(self)
        self.serverIPLabel.move(20, 30)
        self.serverIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.serverIPLineEdit = QLineEdit(self)
        self.serverIPLineEdit.move(50, 38)
        self.serverIPLineEdit.resize(120, 15)
        self.serverIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverIPLineEdit.setText(self.myaddr)  # 本地主机的IP
        # IP Label (20, 40) default size
        self.serverPortLabel = QLabel(self)
        self.serverPortLabel.move(20, 50)
        self.serverPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.serverPortLineEdit = QLineEdit(self)
        self.serverPortLineEdit.move(50, 58)
        self.serverPortLineEdit.resize(120, 15)
        self.serverPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverPortLineEdit.setText('7890')  # 自己选取的端口号

        # 客户端角色 控件布局
        # 下位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(255, 10)
        self.carIPLabel.setText('阿里云')
        # IP Label (20, 20) default size
        self.clientIPLabel = QLabel(self)  # IP标签
        self.clientIPLabel.move(190, 30)
        self.clientIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.clientIPLineEdit = QLineEdit(self)  # IP显示文本框
        self.clientIPLineEdit.move(220, 38)
        self.clientIPLineEdit.resize(120, 15)
        self.clientIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        # self.clientIPLineEdit.setText(self.myaddr)
        ######################################################################################
        self.clientIPLineEdit.setText("47.102.36.187")  # 输入自定义IP
        # IP Label (20, 40) default size
        self.clientPortLabel = QLabel(self)  # port标签
        self.clientPortLabel.move(190, 50)
        self.clientPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.clientPortLineEdit = QLineEdit(self)
        self.clientPortLineEdit.move(220, 58)
        self.clientPortLineEdit.resize(120, 15)
        self.clientPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.clientPortLineEdit.setText('8096')
        ##==============================================第一层按钮组件

        ##=========================================================第二层按钮组件
        # 参数设置
        # 车辆长度 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(40, 85)
        self.lengthOfCarLabel.setText('车辆长度:')
        # 车辆长度 Edit  (50, 18) (120, 15)
        self.lengthOfCarLienEdit = QLineEdit(self)
        self.lengthOfCarLienEdit.move(95, 91)
        self.lengthOfCarLienEdit.resize(50, 15)
        self.lengthOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.lengthOfCarLienEdit.setText('1')
        # 车辆长度单位 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(150, 85)
        self.lengthOfCarLabel.setText('m')

        # 车辆重量 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(210, 85)
        self.weightOfCarLabel.setText('车辆重量:')
        # 车辆重量 Edit  (50, 18) (120, 15)
        self.weightOfCarLienEdit = QLineEdit(self)
        self.weightOfCarLienEdit.move(265, 91)
        self.weightOfCarLienEdit.resize(50, 15)
        self.weightOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.weightOfCarLienEdit.setText('1')
        # 车辆重量单位 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(320, 85)
        self.weightOfCarLabel.setText('kg')

        # 最大速度 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(40, 110)
        self.maxVelocityOfCarLabel.setText('最大速度:')
        # 最大速度 Edit  (50, 18) (120, 15)
        self.maxVelocityOfCarLienEdit = QLineEdit(self)
        self.maxVelocityOfCarLienEdit.move(95, 116)
        self.maxVelocityOfCarLienEdit.resize(50, 15)
        self.maxVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxVelocityOfCarLienEdit.setText('1')
        # 最大速度单位 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(150, 110)
        self.maxVelocityOfCarLabel.setText('m/s')

        # 最小速度 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(210, 110)
        self.minVelocityOfCarLabel.setText('最小速度:')
        # 最小速度 Edit  (50, 18) (120, 15)
        self.minVelocityOfCarLienEdit = QLineEdit(self)
        self.minVelocityOfCarLienEdit.move(265, 116)
        self.minVelocityOfCarLienEdit.resize(50, 15)
        self.minVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.minVelocityOfCarLienEdit.setText('1')
        # 最小速度单位 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(320, 110)
        self.minVelocityOfCarLabel.setText('m/s')

        # 最大加速度 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(30, 135)
        self.maxAccelationOfCarLabel.setText('最大加速度:')
        # 最大加速度 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 141)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 最大加速度单位 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 135)
        self.maxAccelationOfCarLabel.setText('m/s^2')

        # 最大减速度 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(200, 135)
        self.maxDecelerationOfCarLabel.setText('最大减速度:')
        # 最大减速度 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 141)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 最大减速度单位 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 135)
        self.maxDecelerationOfCarLabel.setText('m/s^2')

        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(40, 160)
        self.maxAccelationOfCarLabel.setText('转动惯量:')
        # 转动惯量 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 166)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 160)
        self.maxAccelationOfCarLabel.setText('kg·m^2')

        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(235, 160)
        self.maxDecelerationOfCarLabel.setText('轴距:')
        # 轴距 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 166)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 160)
        self.maxDecelerationOfCarLabel.setText('m')





        ##=========================================================第二层按钮组件


        ##======================================================第三层按钮组件
        # 数据显示部分
        # 车辆ID
        self.IDLabel = QLabel(self)
        self.IDLabel.move(65, 190)
        self.IDLabel.setText('车辆编号:')
        self.IDChangeLabel = QLabel(self)
        self.IDChangeLabel.move(120, 190)
        self.IDChangeLabel.setText('xx')

        # 左轮速度
        self.L2vLabel = QLabel(self)
        self.L2vLabel.move(65, 210)
        self.L2vLabel.setText('左轮电机速度:')
        self.L2vChangeLabel = QLabel(self)
        self.L2vChangeLabel.move(145, 210)
        self.L2vChangeLabel.setText('xxxx')
        self.L2vUnitLabel = QLabel(self)
        self.L2vUnitLabel.move(170, 210)
        self.L2vUnitLabel.setText('cm/s')

        # 右轮速度
        self.R2vLabel = QLabel(self)
        self.R2vLabel.move(210, 210)
        self.R2vLabel.setText('右轮电机速度:')
        self.R2vChangeLabel = QLabel(self)
        self.R2vChangeLabel.move(290, 210)
        self.R2vChangeLabel.setText('xxxxx')
        self.R2vUnitLabel = QLabel(self)
        self.R2vUnitLabel.move(320, 210)
        self.R2vUnitLabel.setText('cm/s')

        # 舵机转角
        self.angleLabel = QLabel(self)
        self.angleLabel.move(210, 230)
        self.angleLabel.setText('转向角度:')
        self.angleChangeLabel = QLabel(self)
        self.angleChangeLabel.move(265, 230)
        self.angleChangeLabel.setText('xxxx')
        self.angleUnitLabel = QLabel(self)
        self.angleUnitLabel.move(295, 230)
        self.angleUnitLabel.setText('°')

        # 车辆状态
        self.LPWMLabel = QLabel(self)
        self.LPWMLabel.move(210, 190)
        self.LPWMLabel.setText('车辆状态:')
        self.LPWMChangeLabel = QLabel(self)
        self.LPWMChangeLabel.move(265, 190)
        self.LPWMChangeLabel.setText('xxxx')

        # 电池电压
        self.RPWMLabel = QLabel(self)
        self.RPWMLabel.move(65, 230)
        self.RPWMLabel.setText('电池电压:')
        self.RPWMChangeLabel = QLabel(self)
        self.RPWMChangeLabel.move(120, 230)
        self.RPWMChangeLabel.setText('xxxx')
        self.RPWMUnitLabel = QLabel(self)
        self.RPWMUnitLabel.move(150, 230)
        self.RPWMUnitLabel.setText('v')

        # 横向加速度
        self.AyLabel = QLabel(self)
        self.AyLabel.move(65, 250)
        self.AyLabel.setText('横向加速度:')
        self.AyChangeLabel = QLabel(self)
        self.AyChangeLabel.move(135, 250)
        self.AyChangeLabel.setText('xxxx')
        self.AyUnitLabel = QLabel(self)
        self.AyUnitLabel.move(165, 250)
        self.AyUnitLabel.setText('m/s^2')

        # 横摆角速度
        self.YawLabel = QLabel(self)
        self.YawLabel.move(210, 250)
        self.YawLabel.setText('横摆角速度:')
        self.YawChangeLabel = QLabel(self)
        self.YawChangeLabel.move(280, 250)
        self.YawChangeLabel.setText('xxxx')
        self.YawUnitLabel = QLabel(self)
        self.YawUnitLabel.move(310, 250)
        self.YawUnitLabel.setText('°/s')

        # 电机转矩
        self.TnLabel = QLabel(self)
        self.TnLabel.move(210, 270)
        self.TnLabel.setText('电机转矩:')
        self.TnChangeLabel = QLabel(self)
        self.TnChangeLabel.move(265, 270)
        self.TnChangeLabel.setText('xxxx')
        self.TnUnitLabel = QLabel(self)
        self.TnUnitLabel.move(295, 270)
        self.TnUnitLabel.setText('N·m')

        # 横向速度
        self.VyLabel = QLabel(self)
        self.VyLabel.move(65, 270)
        self.VyLabel.setText('横向速度:')
        self.VyChangeLabel = QLabel(self)
        self.VyChangeLabel.move(125, 270)
        self.VyChangeLabel.setText('xxxx')
        self.VyUnitLabel = QLabel(self)
        self.VyUnitLabel.move(155, 270)
        self.VyUnitLabel.setText('m/s')

        # 当前经度
        self.lngLabel = QLabel(self)
        self.lngLabel.move(65, 300)
        self.lngLabel.setText('当前经度:')
        self.lngChangeLabel = QLabel(self)
        self.lngChangeLabel.move(120, 300)
        self.lngChangeLabel.setText('xxxx')
        self.lngUnitLabel = QLabel(self)
        self.lngUnitLabel.move(250, 300)
        self.lngUnitLabel.setText('°')

        # 当前纬度
        self.latLabel = QLabel(self)
        self.latLabel.move(65, 320)
        self.latLabel.setText('当前纬度:')
        self.latChangeLabel = QLabel(self)
        self.latChangeLabel.move(120, 320)
        self.latChangeLabel.setText('xxxx')
        # self.latChangeLabel.setGeometry(QRect(328, 240, 329, 27 * 4))
        # self.latChangeLabel.setWordWrap(True)
        # self.latChangeLabel.setAlignment(Qt.AlignTop)
        self.latUnitLabel = QLabel(self)
        self.latUnitLabel.move(250, 320)
        self.latUnitLabel.setText('°')



        ## 下位机上传的图像信息
        self.angleLabel = QLabel(self)
        self.angleLabel.move(400, 150)
        self.angleLabel.setText('图像:')

        pix = QPixmap('background.jpg')
        self.lb1 = QLabel(self)
        self.lb1.setGeometry(450, 5, 400, 200)  # x1 x2 x3 x4,从（x1,x2）开始显示一个x3长x4宽的矩形
        self.lb1.setPixmap(QPixmap('background.jpg'))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
        self.lb1.setStyleSheet("border: 2px solid red")


        # 方法三
        self.angleLabel = QLabel(self)  # 标签
        self.angleLabel.move(390, 350)
        self.angleLabel.setText('导航图像:')
        # 调用Mapwindow函数，建立一个他的对象
        SettingBox_Map1 = QGroupBox("导航地图")
        Map1 = Map_load2()
        v_map1_layout = QVBoxLayout()
        v_map1_layout.addWidget(Map1)
        v_map1_layout.setContentsMargins(450, 200, 50, 50)  # 左上右下距离边框的长度
        self.setLayout(v_map1_layout)
        # QApplication.processEvents()  # 使得图像界面可以实时更新


        # 状态栏显示
        # self.setGeometry(100, 100, 370, 550)
        self.setGeometry(100, 100, 900, 450)
        self.setWindowTitle('Eighth')
        self.show()

    def slot_btn_function(self):
        # self.hide()
        self.f1 = First_ID1()
        self.f1.show()



    ## 响应槽函数
    def mapshow(self, text):
        map = (Map().add(text, [list(z) for z in zip(Faker.provinces, Faker.values())], text)
               .set_global_opts(title_opts=opts.TitleOpts(title="map")))
        map.render('BD_map8.html')  # 读取对应车辆的百度地图API程序
        # self.browser.load(QUrl(QFileInfo("file:///E:/pycharm_project/TCP%2010%2025/BD_map.html").absoluteFilePath()))
        self.browser.load(QUrl(QFileInfo("BD_map8.html").absoluteFilePath()))
        print("更新BD地图============")
        if text in self.knowledge:
            self.knowledge_label.setText(self.knowledge[text])
        else:
            self.knowledge_label.setText('')

    def IDchange(self,ID):  # 更新车辆ID的槽函数
        self.IDChangeLabel.setText(ID)

    def Statechange(self,State):  # 更新车辆状态
        self.StatechangeLable.setText(str(State))


    def L2vchange(self, L2v):  # 更新左轮电机转速的槽函数
        self.L2vChangeLabel.setText(str(L2v))

    def R2vchange(self, R2v):  # 更新右轮电机转速的槽函数
        self.R2vChangeLabel.setText(str(R2v))
    def anglechange(self, angle):  # 更新转向角度的槽函数
        self.angleChangeLabel.setText(str(angle))

    def Uchange(self,U):
        self.UchangeLabel.setText(U)

    def LPWMchange(self, LPWM):
        self.LPWMChangeLabel.setText(str(LPWM))

    def RPWMchange(self,RPWM):
        self.RPWMChangeLabel.setText(str(RPWM))

    def Aychange(self,Ay):
        self.AyChangeLabel.setText(str(Ay))

    def Yawchange(self,Yaw):
        self.YawChangeLabel.setText(str(Yaw))

    def Tnchange(self,Tn):
        self.TnChangeLabel.setText(str(Tn))

    def Vychange(self,Vy):
        self.VyChangeLabel.setText(str(Vy))


    def lngChange(self,lng):
        self.lngChangeLabel.setText(str(lng))

    def latChange(self,lat):
        self.latChangeLabel.setText(str(lat))


    # 修改显示的图像
    def QPixmapchange(self,Image):
        self.lb1.setPixmap(QPixmap(str(Image)))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
    # 修改显示的图像


    def start(self):  # start按钮的槽函数
        global startFlag
        startFlag = 1



    def listenToClient(self):  # 点击Listen后的响应事件
        localIP = self.serverIPLineEdit.text()  # 定义Listener类中的属性值
        localPort = self.serverPortLineEdit.text()
        serverIP = self.clientIPLineEdit.text()
        serverPort = self.clientPortLineEdit.text()
        length = self.lengthOfCarLienEdit.text()
        weight = self.weightOfCarLienEdit.text()
        maxV = self.maxVelocityOfCarLienEdit.text()
        minV = self.minVelocityOfCarLienEdit.text()
        maxA = self.maxAccelationOfCarLienEdit.text()
        maxD = self.maxDecelerationOfCarLienEdit.text()
        self._thread = Listener_ID8(localIP, int(localPort), serverIP, int(serverPort),
                                int(length), int(weight), int(maxV),
                                int(minV), int(maxA), int(maxD))  # 定义一个Listener的对象
        self._thread.sigID_ID8.connect(self.IDchange)  # 调用修改参数方法，实时传输显示下位机传输的数据
        self._thread.sigRPWM_ID8.connect(self.RPWMchange)
        self._thread.sigLPWM_ID8.connect(self.LPWMchange)
        self._thread.sigL2v_ID8.connect(self.L2vchange)
        self._thread.sigR2v_ID8.connect(self.R2vchange)
        self._thread.sigangle_ID8.connect(self.anglechange)
        self._thread.sigImage_ID8.connect(self.QPixmapchange)  # 更新显示的图片

        self._thread.sigAy_ID8.connect(self.Aychange)
        self._thread.sigYaw_ID8.connect(self.Yawchange)
        self._thread.sigTn_ID8.connect(self.Tnchange)
        self._thread.sigVy_ID8.connect(self.Vychange)

        self._thread.siglat_ID8.connect(self.latChange)
        self._thread.siglng_ID8.connect(self.lngChange)  # 更新当前经纬度数据


        self._thread.start()  # 执行Litener类中的run方法
        self.listenButton.setText('Listening')  # 开始执行监听后标识为“正在监听”




    def askstate(self):  # askstate按钮的槽函数
        global askstateFlag_ID8
        askstateFlag_ID8 = 1
        print('askstateFlag_ID8_change_to:', askstateFlag_ID8)

    def askimage(self):  # askimage按钮的槽函数
        global askimageFlag_ID8
        askimageFlag_ID8 = 1
        print('askimageFlag_ID8_change_to:', askimageFlag_ID8)

        # self._thread = Image_listen()
        # self._thread.start()

    def send(self):  # send按钮的槽函数
        global sendFlag_ID8
        sendFlag_ID8 = 1
        print('sendFlag_ID8_change_to:', sendFlag_ID8)




    def closeEvent(self, event):  # GUI窗口右上角关闭按钮的槽函数
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# 第九辆车
class Ninth_ID9(QWidget):

    serverSig = pyqtSignal()  # 申明无参数信号

    def __init__(self):  # 初始化
        self.myname = socket.getfqdn(socket.gethostname())  # gethostname() ： 返回本地主机的标准主机名。
        self.myaddr = socket.gethostbyname(self.myname)  # gethostbyname()：用域名或主机名获取IP地址
        super(Ninth_ID9, self).__init__()  # 继承父类的属性和方法
        self.initUI()  # 调用自己的方法

    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)

        if int(i) == 1:  ## 传过来的是str型参数，转换成int型才可
            # self.hide()
            self.f1 = First_ID1()
            self.f1.show()

        elif int(i) == 2:
            # self.hide()
            self.s2 = Second_ID2()
            self.s2.show()

        elif int(i) == 3:
            # self.hide()
            self.t3 = Third_ID3()
            self.t3.show()

        elif int(i) == 4:
            # self.hide()
            self.f4 = Forth_ID4()
            self.f4.show()

        elif int(i) == 5:
            # self.hide()
            self.f5 = Fifth_ID5()
            self.f5.show()

        elif int(i) == 6:
            # self.hide()
            self.s6 = Sixth_ID6()
            self.s6.show()

        elif int(i) == 7:
            # self.hide()
            self.s7 = Seventh_ID7()
            self.s7.show()

        elif int(i) == 8:
            # self.hide()
            self.e8 = Eighth_ID8()
            self.e8.show()

        elif int(i) == 10:
            # self.hide()
            self.t10 = Tenth_ID10()
            self.t10.show()

    def initUI(self):

        self.btn = QPushButton('jump to FirstUI', self)  # 用来返回到第一个界面
        self.btn.setGeometry(350, 50, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function)

        self.cb = QComboBox(self)
        self.cb.move(350, 10)
        self.cb.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容

        ##=======================================================第四层按钮组件
        # 退出按钮
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(QCoreApplication.instance().quit)  # 信号与槽，槽可以是QT内置的槽也可以是python内置方法
        self.quitButton.resize(self.quitButton.sizeHint())  # sizeHint()提供一个推荐大小
        self.quitButton.move(50, 360)  # 放置位子
        # 监听按钮
        self.listenButton = QPushButton('Listen', self)
        self.listenButton.setCheckable(True)  # 可以点击
        self.listenButton.clicked.connect(self.listenToClient)  # 链接到槽方法listenToClient,开始监听
        self.listenButton.resize(self.quitButton.sizeHint())  # 和quitButton按钮一样大
        self.listenButton.move(250, 360)  # 改变大小并移动

        #  开始按钮
        self.startButton = QPushButton('Start', self)
        self.startButton.setCheckable(True)
        self.startButton.clicked.connect(self.start)  # self.StartFlag = 1,表示开始向下位机发送数据
        self.startButton.resize(self.quitButton.sizeHint())
        self.startButton.move(50, 400)

        #  发送第一组数据按钮
        self.sendButton = QPushButton('Send', self)
        self.sendButton.setCheckable(True)
        self.sendButton.clicked.connect(self.send)  # 发送第一组经纬度
        self.sendButton.resize(self.quitButton.sizeHint())
        self.sendButton.move(250, 400)

        #  请求车辆的状态
        self.stateButton = QPushButton('AskState', self)
        self.stateButton.setCheckable(True)
        self.stateButton.clicked.connect(self.askstate)  # 发送停止信号 “ST”
        self.stateButton.resize(self.quitButton.sizeHint())
        self.stateButton.move(150, 360)

        #  请求车辆的图像
        self.imageButton = QPushButton('AskImage', self)
        self.imageButton.setCheckable(True)
        self.imageButton.clicked.connect(self.askimage)  # 发送停止信号 “ST”
        self.imageButton.resize(self.quitButton.sizeHint())
        self.imageButton.move(150, 400)

        #  请求百度地图
        # self.imageButton = QPushButton('BD_map', self)
        # self.imageButton.setCheckable(True)
        # self.imageButton.clicked.connect(self.mapshow)  # 发送显示地图指令
        # self.imageButton.resize(self.quitButton.sizeHint())
        # self.imageButton.move(150, 320)
        ##====================================================第四层按钮组件


        ##==============================================第一层按钮组件
        # 服务器角色 控件布局
        # 上位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(85, 10)
        self.carIPLabel.setText('上位机')
        # IP Label (20, 20) default size
        self.serverIPLabel = QLabel(self)
        self.serverIPLabel.move(20, 30)
        self.serverIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.serverIPLineEdit = QLineEdit(self)
        self.serverIPLineEdit.move(50, 38)
        self.serverIPLineEdit.resize(120, 15)
        self.serverIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverIPLineEdit.setText(self.myaddr)  # 本地主机的IP
        # IP Label (20, 40) default size
        self.serverPortLabel = QLabel(self)
        self.serverPortLabel.move(20, 50)
        self.serverPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.serverPortLineEdit = QLineEdit(self)
        self.serverPortLineEdit.move(50, 58)
        self.serverPortLineEdit.resize(120, 15)
        self.serverPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverPortLineEdit.setText('7890')  # 自己选取的端口号

        # 客户端角色 控件布局
        # 下位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(255, 10)
        self.carIPLabel.setText('阿里云')
        # IP Label (20, 20) default size
        self.clientIPLabel = QLabel(self)  # IP标签
        self.clientIPLabel.move(190, 30)
        self.clientIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.clientIPLineEdit = QLineEdit(self)  # IP显示文本框
        self.clientIPLineEdit.move(220, 38)
        self.clientIPLineEdit.resize(120, 15)
        self.clientIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        # self.clientIPLineEdit.setText(self.myaddr)
        ######################################################################################
        self.clientIPLineEdit.setText("47.102.36.187")  # 输入自定义IP
        # IP Label (20, 40) default size
        self.clientPortLabel = QLabel(self)  # port标签
        self.clientPortLabel.move(190, 50)
        self.clientPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.clientPortLineEdit = QLineEdit(self)
        self.clientPortLineEdit.move(220, 58)
        self.clientPortLineEdit.resize(120, 15)
        self.clientPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.clientPortLineEdit.setText('8098')
        ##==============================================第一层按钮组件

        ##=========================================================第二层按钮组件
        # 参数设置
        # 车辆长度 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(40, 85)
        self.lengthOfCarLabel.setText('车辆长度:')
        # 车辆长度 Edit  (50, 18) (120, 15)
        self.lengthOfCarLienEdit = QLineEdit(self)
        self.lengthOfCarLienEdit.move(95, 91)
        self.lengthOfCarLienEdit.resize(50, 15)
        self.lengthOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.lengthOfCarLienEdit.setText('1')
        # 车辆长度单位 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(150, 85)
        self.lengthOfCarLabel.setText('m')

        # 车辆重量 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(210, 85)
        self.weightOfCarLabel.setText('车辆重量:')
        # 车辆重量 Edit  (50, 18) (120, 15)
        self.weightOfCarLienEdit = QLineEdit(self)
        self.weightOfCarLienEdit.move(265, 91)
        self.weightOfCarLienEdit.resize(50, 15)
        self.weightOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.weightOfCarLienEdit.setText('1')
        # 车辆重量单位 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(320, 85)
        self.weightOfCarLabel.setText('kg')

        # 最大速度 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(40, 110)
        self.maxVelocityOfCarLabel.setText('最大速度:')
        # 最大速度 Edit  (50, 18) (120, 15)
        self.maxVelocityOfCarLienEdit = QLineEdit(self)
        self.maxVelocityOfCarLienEdit.move(95, 116)
        self.maxVelocityOfCarLienEdit.resize(50, 15)
        self.maxVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxVelocityOfCarLienEdit.setText('1')
        # 最大速度单位 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(150, 110)
        self.maxVelocityOfCarLabel.setText('m/s')

        # 最小速度 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(210, 110)
        self.minVelocityOfCarLabel.setText('最小速度:')
        # 最小速度 Edit  (50, 18) (120, 15)
        self.minVelocityOfCarLienEdit = QLineEdit(self)
        self.minVelocityOfCarLienEdit.move(265, 116)
        self.minVelocityOfCarLienEdit.resize(50, 15)
        self.minVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.minVelocityOfCarLienEdit.setText('1')
        # 最小速度单位 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(320, 110)
        self.minVelocityOfCarLabel.setText('m/s')

        # 最大加速度 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(30, 135)
        self.maxAccelationOfCarLabel.setText('最大加速度:')
        # 最大加速度 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 141)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 最大加速度单位 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 135)
        self.maxAccelationOfCarLabel.setText('m/s^2')

        # 最大减速度 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(200, 135)
        self.maxDecelerationOfCarLabel.setText('最大减速度:')
        # 最大减速度 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 141)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 最大减速度单位 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 135)
        self.maxDecelerationOfCarLabel.setText('m/s^2')

        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(40, 160)
        self.maxAccelationOfCarLabel.setText('转动惯量:')
        # 转动惯量 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 166)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 160)
        self.maxAccelationOfCarLabel.setText('kg·m^2')

        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(235, 160)
        self.maxDecelerationOfCarLabel.setText('轴距:')
        # 轴距 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 166)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 160)
        self.maxDecelerationOfCarLabel.setText('m')





        ##=========================================================第二层按钮组件


        ##======================================================第三层按钮组件
        # 数据显示部分
        # 车辆ID
        self.IDLabel = QLabel(self)
        self.IDLabel.move(65, 190)
        self.IDLabel.setText('车辆编号:')
        self.IDChangeLabel = QLabel(self)
        self.IDChangeLabel.move(120, 190)
        self.IDChangeLabel.setText('xx')

        # 左轮速度
        self.L2vLabel = QLabel(self)
        self.L2vLabel.move(65, 210)
        self.L2vLabel.setText('左轮电机速度:')
        self.L2vChangeLabel = QLabel(self)
        self.L2vChangeLabel.move(145, 210)
        self.L2vChangeLabel.setText('xxxx')
        self.L2vUnitLabel = QLabel(self)
        self.L2vUnitLabel.move(170, 210)
        self.L2vUnitLabel.setText('cm/s')

        # 右轮速度
        self.R2vLabel = QLabel(self)
        self.R2vLabel.move(210, 210)
        self.R2vLabel.setText('右轮电机速度:')
        self.R2vChangeLabel = QLabel(self)
        self.R2vChangeLabel.move(290, 210)
        self.R2vChangeLabel.setText('xxxxx')
        self.R2vUnitLabel = QLabel(self)
        self.R2vUnitLabel.move(320, 210)
        self.R2vUnitLabel.setText('cm/s')

        # 舵机转角
        self.angleLabel = QLabel(self)
        self.angleLabel.move(210, 230)
        self.angleLabel.setText('转向角度:')
        self.angleChangeLabel = QLabel(self)
        self.angleChangeLabel.move(265, 230)
        self.angleChangeLabel.setText('xxxx')
        self.angleUnitLabel = QLabel(self)
        self.angleUnitLabel.move(295, 230)
        self.angleUnitLabel.setText('°')

        # 车辆状态
        self.LPWMLabel = QLabel(self)
        self.LPWMLabel.move(210, 190)
        self.LPWMLabel.setText('车辆状态:')
        self.LPWMChangeLabel = QLabel(self)
        self.LPWMChangeLabel.move(265, 190)
        self.LPWMChangeLabel.setText('xxxx')

        # 电池电压
        self.RPWMLabel = QLabel(self)
        self.RPWMLabel.move(65, 230)
        self.RPWMLabel.setText('电池电压:')
        self.RPWMChangeLabel = QLabel(self)
        self.RPWMChangeLabel.move(120, 230)
        self.RPWMChangeLabel.setText('xxxx')
        self.RPWMUnitLabel = QLabel(self)
        self.RPWMUnitLabel.move(150, 230)
        self.RPWMUnitLabel.setText('v')

        # 横向加速度
        self.AyLabel = QLabel(self)
        self.AyLabel.move(65, 250)
        self.AyLabel.setText('横向加速度:')
        self.AyChangeLabel = QLabel(self)
        self.AyChangeLabel.move(135, 250)
        self.AyChangeLabel.setText('xxxx')
        self.AyUnitLabel = QLabel(self)
        self.AyUnitLabel.move(165, 250)
        self.AyUnitLabel.setText('m/s^2')

        # 横摆角速度
        self.YawLabel = QLabel(self)
        self.YawLabel.move(210, 250)
        self.YawLabel.setText('横摆角速度:')
        self.YawChangeLabel = QLabel(self)
        self.YawChangeLabel.move(280, 250)
        self.YawChangeLabel.setText('xxxx')
        self.YawUnitLabel = QLabel(self)
        self.YawUnitLabel.move(310, 250)
        self.YawUnitLabel.setText('°/s')

        # 电机转矩
        self.TnLabel = QLabel(self)
        self.TnLabel.move(210, 270)
        self.TnLabel.setText('电机转矩:')
        self.TnChangeLabel = QLabel(self)
        self.TnChangeLabel.move(265, 270)
        self.TnChangeLabel.setText('xxxx')
        self.TnUnitLabel = QLabel(self)
        self.TnUnitLabel.move(295, 270)
        self.TnUnitLabel.setText('N·m')

        # 横向速度
        self.VyLabel = QLabel(self)
        self.VyLabel.move(65, 270)
        self.VyLabel.setText('横向速度:')
        self.VyChangeLabel = QLabel(self)
        self.VyChangeLabel.move(125, 270)
        self.VyChangeLabel.setText('xxxx')
        self.VyUnitLabel = QLabel(self)
        self.VyUnitLabel.move(155, 270)
        self.VyUnitLabel.setText('m/s')

        # 当前经度
        self.lngLabel = QLabel(self)
        self.lngLabel.move(65, 300)
        self.lngLabel.setText('当前经度:')
        self.lngChangeLabel = QLabel(self)
        self.lngChangeLabel.move(120, 300)
        self.lngChangeLabel.setText('xxxx')
        self.lngUnitLabel = QLabel(self)
        self.lngUnitLabel.move(250, 300)
        self.lngUnitLabel.setText('°')

        # 当前纬度
        self.latLabel = QLabel(self)
        self.latLabel.move(65, 320)
        self.latLabel.setText('当前纬度:')
        self.latChangeLabel = QLabel(self)
        self.latChangeLabel.move(120, 320)
        self.latChangeLabel.setText('xxxx')
        # self.latChangeLabel.setGeometry(QRect(328, 240, 329, 27 * 4))
        # self.latChangeLabel.setWordWrap(True)
        # self.latChangeLabel.setAlignment(Qt.AlignTop)
        self.latUnitLabel = QLabel(self)
        self.latUnitLabel.move(250, 320)
        self.latUnitLabel.setText('°')



        ## 下位机上传的图像信息
        self.angleLabel = QLabel(self)
        self.angleLabel.move(400, 150)
        self.angleLabel.setText('图像:')

        pix = QPixmap('background.jpg')
        self.lb1 = QLabel(self)
        self.lb1.setGeometry(450, 5, 400, 200)  # x1 x2 x3 x4,从（x1,x2）开始显示一个x3长x4宽的矩形
        self.lb1.setPixmap(QPixmap('background.jpg'))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
        self.lb1.setStyleSheet("border: 2px solid red")


        # 方法三
        self.angleLabel = QLabel(self)  # 标签
        self.angleLabel.move(390, 350)
        self.angleLabel.setText('导航图像:')
        # 调用Mapwindow函数，建立一个他的对象
        SettingBox_Map1 = QGroupBox("导航地图")
        Map1 = Map_load2()
        v_map1_layout = QVBoxLayout()
        v_map1_layout.addWidget(Map1)
        v_map1_layout.setContentsMargins(450, 200, 50, 50)  # 左上右下距离边框的长度
        self.setLayout(v_map1_layout)
        # QApplication.processEvents()  # 使得图像界面可以实时更新


        # 状态栏显示
        # self.setGeometry(100, 100, 370, 550)
        self.setGeometry(100, 100, 900, 450)
        self.setWindowTitle('Ninth')
        self.show()

    def slot_btn_function(self):
        # self.hide()
        self.f1 = First_ID1()
        self.f1.show()



    ## 响应槽函数
    def mapshow(self, text):
        map = (Map().add(text, [list(z) for z in zip(Faker.provinces, Faker.values())], text)
               .set_global_opts(title_opts=opts.TitleOpts(title="map")))
        map.render('BD_map9.html')  # 读取对应车辆的百度地图API程序
        # self.browser.load(QUrl(QFileInfo("file:///E:/pycharm_project/TCP%2010%2025/BD_map.html").absoluteFilePath()))
        self.browser.load(QUrl(QFileInfo("BD_map9.html").absoluteFilePath()))
        print("更新BD地图============")
        if text in self.knowledge:
            self.knowledge_label.setText(self.knowledge[text])
        else:
            self.knowledge_label.setText('')

    def IDchange(self,ID):  # 更新车辆ID的槽函数
        self.IDChangeLabel.setText(ID)

    def Statechange(self,State):  # 更新车辆状态
        self.StatechangeLable.setText(str(State))


    def L2vchange(self, L2v):  # 更新左轮电机转速的槽函数
        self.L2vChangeLabel.setText(str(L2v))

    def R2vchange(self, R2v):  # 更新右轮电机转速的槽函数
        self.R2vChangeLabel.setText(str(R2v))
    def anglechange(self, angle):  # 更新转向角度的槽函数
        self.angleChangeLabel.setText(str(angle))

    def Uchange(self,U):
        self.UchangeLabel.setText(U)

    def LPWMchange(self, LPWM):
        self.LPWMChangeLabel.setText(str(LPWM))

    def RPWMchange(self,RPWM):
        self.RPWMChangeLabel.setText(str(RPWM))

    def Aychange(self,Ay):
        self.AyChangeLabel.setText(str(Ay))

    def Yawchange(self,Yaw):
        self.YawChangeLabel.setText(str(Yaw))

    def Tnchange(self,Tn):
        self.TnChangeLabel.setText(str(Tn))

    def Vychange(self,Vy):
        self.VyChangeLabel.setText(str(Vy))


    def lngChange(self,lng):
        self.lngChangeLabel.setText(str(lng))

    def latChange(self,lat):
        self.latChangeLabel.setText(str(lat))


    # 修改显示的图像
    def QPixmapchange(self,Image):
        self.lb1.setPixmap(QPixmap(str(Image)))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
    # 修改显示的图像


    def start(self):  # start按钮的槽函数
        global startFlag
        startFlag = 1



    def listenToClient(self):  # 点击Listen后的响应事件
        localIP = self.serverIPLineEdit.text()  # 定义Listener类中的属性值
        localPort = self.serverPortLineEdit.text()
        serverIP = self.clientIPLineEdit.text()
        serverPort = self.clientPortLineEdit.text()
        length = self.lengthOfCarLienEdit.text()
        weight = self.weightOfCarLienEdit.text()
        maxV = self.maxVelocityOfCarLienEdit.text()
        minV = self.minVelocityOfCarLienEdit.text()
        maxA = self.maxAccelationOfCarLienEdit.text()
        maxD = self.maxDecelerationOfCarLienEdit.text()
        self._thread = Listener_ID9(localIP, int(localPort), serverIP, int(serverPort),
                                int(length), int(weight), int(maxV),
                                int(minV), int(maxA), int(maxD))  # 定义一个Listener的对象
        self._thread.sigID_ID9.connect(self.IDchange)  # 调用修改参数方法，实时传输显示下位机传输的数据
        self._thread.sigRPWM_ID9.connect(self.RPWMchange)
        self._thread.sigLPWM_ID9.connect(self.LPWMchange)
        self._thread.sigL2v_ID9.connect(self.L2vchange)
        self._thread.sigR2v_ID9.connect(self.R2vchange)
        self._thread.sigangle_ID9.connect(self.anglechange)
        self._thread.sigImage_ID9.connect(self.QPixmapchange)  # 更新显示的图片

        self._thread.sigAy_ID9.connect(self.Aychange)
        self._thread.sigYaw_ID9.connect(self.Yawchange)
        self._thread.sigTn_ID9.connect(self.Tnchange)
        self._thread.sigVy_ID9.connect(self.Vychange)

        self._thread.siglat_ID9.connect(self.latChange)
        self._thread.siglng_ID9.connect(self.lngChange)  # 更新当前经纬度数据


        self._thread.start()  # 执行Litener类中的run方法
        self.listenButton.setText('Listening')  # 开始执行监听后标识为“正在监听”




    def askstate(self):  # askstate按钮的槽函数
        global askstateFlag_ID9
        askstateFlag_ID9 = 1
        print('askstateFlag_ID9_change_to:', askstateFlag_ID9)

    def askimage(self):  # askimage按钮的槽函数
        global askimageFlag_ID9
        askimageFlag_ID9 = 1
        print('askimageFlag_ID9_change_to:', askimageFlag_ID9)

        # self._thread = Image_listen()
        # self._thread.start()

    def send(self):  # send按钮的槽函数
        global sendFlag_ID9
        sendFlag_ID9 = 1
        print('sendFlag_ID9_change_to:', sendFlag_ID9)




    def closeEvent(self, event):  # GUI窗口右上角关闭按钮的槽函数
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# 第十辆车
class Tenth_ID10(QWidget):

    serverSig = pyqtSignal()  # 申明无参数信号

    def __init__(self):  # 初始化
        self.myname = socket.getfqdn(socket.gethostname())  # gethostname() ： 返回本地主机的标准主机名。
        self.myaddr = socket.gethostbyname(self.myname)  # gethostbyname()：用域名或主机名获取IP地址
        super(Tenth_ID10, self).__init__()  # 继承父类的属性和方法
        self.initUI()  # 调用自己的方法

    def print_value(self, i):  ## 设置选中下拉列表的项的响应事件
        print(i)


        if int(i) == 1:  ## 传过来的是str型参数，转换成int型才可
            # self.hide()
            self.f1 = First_ID1()
            self.f1.show()

        elif int(i) == 2:
            # self.hide()
            self.s2 = Second_ID2()
            self.s2.show()

        elif int(i) == 3:

            # self.hide()

            self.t3 = Third_ID3()
            self.t3.show()

        elif int(i) == 4:
            # self.hide()
            self.f4 = Forth_ID4()
            self.f4.show()

        elif int(i) == 5:
            # self.hide()
            self.f5 = Fifth_ID5()
            self.f5.show()

        elif int(i) == 6:
            # self.hide()
            self.s6 = Sixth_ID6()
            self.s6.show()

        elif int(i) == 7:
            # self.hide()
            self.s7 = Seventh_ID7()
            self.s7.show()

        elif int(i) == 8:
            # self.hide()
            self.e8 = Eighth_ID8()
            self.e8.show()

        elif int(i) == 9:
            # self.hide()
            self.n9 = Ninth_ID9()
            self.n9.show()

    def initUI(self):

        self.btn = QPushButton('jump to FirstUI', self)  # 用来返回到第一个界面
        self.btn.setGeometry(350, 50, 100, 50)
        self.btn.clicked.connect(self.slot_btn_function)

        self.cb = QComboBox(self)
        self.cb.move(350, 10)
        self.cb.addItems(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        self.cb.currentIndexChanged[str].connect(self.print_value)  # 条目发生改变，发射信号，传递条目内容

        ##=======================================================第四层按钮组件
        # 退出按钮
        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(QCoreApplication.instance().quit)  # 信号与槽，槽可以是QT内置的槽也可以是python内置方法
        self.quitButton.resize(self.quitButton.sizeHint())  # sizeHint()提供一个推荐大小
        self.quitButton.move(50, 360)  # 放置位子
        # 监听按钮
        self.listenButton = QPushButton('Listen', self)
        self.listenButton.setCheckable(True)  # 可以点击
        self.listenButton.clicked.connect(self.listenToClient)  # 链接到槽方法listenToClient,开始监听
        self.listenButton.resize(self.quitButton.sizeHint())  # 和quitButton按钮一样大
        self.listenButton.move(250, 360)  # 改变大小并移动

        #  开始按钮
        self.startButton = QPushButton('Start', self)
        self.startButton.setCheckable(True)
        self.startButton.clicked.connect(self.start)  # self.StartFlag = 1,表示开始向下位机发送数据
        self.startButton.resize(self.quitButton.sizeHint())
        self.startButton.move(50, 400)

        #  发送第一组数据按钮
        self.sendButton = QPushButton('Send', self)
        self.sendButton.setCheckable(True)
        self.sendButton.clicked.connect(self.send)  # 发送第一组经纬度
        self.sendButton.resize(self.quitButton.sizeHint())
        self.sendButton.move(250, 400)

        #  请求车辆的状态
        self.stateButton = QPushButton('AskState', self)
        self.stateButton.setCheckable(True)
        self.stateButton.clicked.connect(self.askstate)  # 发送停止信号 “ST”
        self.stateButton.resize(self.quitButton.sizeHint())
        self.stateButton.move(150, 360)

        #  请求车辆的图像
        self.imageButton = QPushButton('AskImage', self)
        self.imageButton.setCheckable(True)
        self.imageButton.clicked.connect(self.askimage)  # 发送停止信号 “ST”
        self.imageButton.resize(self.quitButton.sizeHint())
        self.imageButton.move(150, 400)

        #  请求百度地图
        # self.imageButton = QPushButton('BD_map', self)
        # self.imageButton.setCheckable(True)
        # self.imageButton.clicked.connect(self.mapshow)  # 发送显示地图指令
        # self.imageButton.resize(self.quitButton.sizeHint())
        # self.imageButton.move(150, 320)
        ##====================================================第四层按钮组件


        ##==============================================第一层按钮组件
        # 服务器角色 控件布局
        # 上位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(85, 10)
        self.carIPLabel.setText('上位机')
        # IP Label (20, 20) default size
        self.serverIPLabel = QLabel(self)
        self.serverIPLabel.move(20, 30)
        self.serverIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.serverIPLineEdit = QLineEdit(self)
        self.serverIPLineEdit.move(50, 38)
        self.serverIPLineEdit.resize(120, 15)
        self.serverIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverIPLineEdit.setText(self.myaddr)  # 本地主机的IP
        # IP Label (20, 40) default size
        self.serverPortLabel = QLabel(self)
        self.serverPortLabel.move(20, 50)
        self.serverPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.serverPortLineEdit = QLineEdit(self)
        self.serverPortLineEdit.move(50, 58)
        self.serverPortLineEdit.resize(120, 15)
        self.serverPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.serverPortLineEdit.setText('7890')  # 自己选取的端口号

        # 客户端角色 控件布局
        # 下位机
        self.carIPLabel = QLabel(self)
        self.carIPLabel.move(255, 10)
        self.carIPLabel.setText('阿里云')
        # IP Label (20, 20) default size
        self.clientIPLabel = QLabel(self)  # IP标签
        self.clientIPLabel.move(190, 30)
        self.clientIPLabel.setText('IP:')
        # IP Edit  (50, 18) (120, 15)
        self.clientIPLineEdit = QLineEdit(self)  # IP显示文本框
        self.clientIPLineEdit.move(220, 38)
        self.clientIPLineEdit.resize(120, 15)
        self.clientIPLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        # self.clientIPLineEdit.setText(self.myaddr)
        ######################################################################################
        self.clientIPLineEdit.setText("47.102.36.187")  # 输入自定义IP
        # IP Label (20, 40) default size
        self.clientPortLabel = QLabel(self)  # port标签
        self.clientPortLabel.move(190, 50)
        self.clientPortLabel.setText('Port:')
        # IP Edit  (50, 38) (120, 15)
        self.clientPortLineEdit = QLineEdit(self)
        self.clientPortLineEdit.move(220, 58)
        self.clientPortLineEdit.resize(120, 15)
        self.clientPortLineEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.clientPortLineEdit.setText('8100')
        ##==============================================第一层按钮组件

        ##=========================================================第二层按钮组件
        # 参数设置
        # 车辆长度 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(40, 85)
        self.lengthOfCarLabel.setText('车辆长度:')
        # 车辆长度 Edit  (50, 18) (120, 15)
        self.lengthOfCarLienEdit = QLineEdit(self)
        self.lengthOfCarLienEdit.move(95, 91)
        self.lengthOfCarLienEdit.resize(50, 15)
        self.lengthOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.lengthOfCarLienEdit.setText('1')
        # 车辆长度单位 Label
        self.lengthOfCarLabel = QLabel(self)
        self.lengthOfCarLabel.move(150, 85)
        self.lengthOfCarLabel.setText('m')

        # 车辆重量 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(210, 85)
        self.weightOfCarLabel.setText('车辆重量:')
        # 车辆重量 Edit  (50, 18) (120, 15)
        self.weightOfCarLienEdit = QLineEdit(self)
        self.weightOfCarLienEdit.move(265, 91)
        self.weightOfCarLienEdit.resize(50, 15)
        self.weightOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.weightOfCarLienEdit.setText('1')
        # 车辆重量单位 Label
        self.weightOfCarLabel = QLabel(self)
        self.weightOfCarLabel.move(320, 85)
        self.weightOfCarLabel.setText('kg')

        # 最大速度 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(40, 110)
        self.maxVelocityOfCarLabel.setText('最大速度:')
        # 最大速度 Edit  (50, 18) (120, 15)
        self.maxVelocityOfCarLienEdit = QLineEdit(self)
        self.maxVelocityOfCarLienEdit.move(95, 116)
        self.maxVelocityOfCarLienEdit.resize(50, 15)
        self.maxVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxVelocityOfCarLienEdit.setText('1')
        # 最大速度单位 Label
        self.maxVelocityOfCarLabel = QLabel(self)
        self.maxVelocityOfCarLabel.move(150, 110)
        self.maxVelocityOfCarLabel.setText('m/s')

        # 最小速度 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(210, 110)
        self.minVelocityOfCarLabel.setText('最小速度:')
        # 最小速度 Edit  (50, 18) (120, 15)
        self.minVelocityOfCarLienEdit = QLineEdit(self)
        self.minVelocityOfCarLienEdit.move(265, 116)
        self.minVelocityOfCarLienEdit.resize(50, 15)
        self.minVelocityOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.minVelocityOfCarLienEdit.setText('1')
        # 最小速度单位 Label
        self.minVelocityOfCarLabel = QLabel(self)
        self.minVelocityOfCarLabel.move(320, 110)
        self.minVelocityOfCarLabel.setText('m/s')

        # 最大加速度 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(30, 135)
        self.maxAccelationOfCarLabel.setText('最大加速度:')
        # 最大加速度 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 141)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 最大加速度单位 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 135)
        self.maxAccelationOfCarLabel.setText('m/s^2')

        # 最大减速度 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(200, 135)
        self.maxDecelerationOfCarLabel.setText('最大减速度:')
        # 最大减速度 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 141)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 最大减速度单位 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 135)
        self.maxDecelerationOfCarLabel.setText('m/s^2')

        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(40, 160)
        self.maxAccelationOfCarLabel.setText('转动惯量:')
        # 转动惯量 Edit  (50, 18) (120, 15)
        self.maxAccelationOfCarLienEdit = QLineEdit(self)
        self.maxAccelationOfCarLienEdit.move(95, 166)
        self.maxAccelationOfCarLienEdit.resize(50, 15)
        self.maxAccelationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxAccelationOfCarLienEdit.setText('1')
        # 转动惯量 Label
        self.maxAccelationOfCarLabel = QLabel(self)
        self.maxAccelationOfCarLabel.move(150, 160)
        self.maxAccelationOfCarLabel.setText('kg·m^2')

        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(235, 160)
        self.maxDecelerationOfCarLabel.setText('轴距:')
        # 轴距 Edit  (50, 18) (120, 15)
        self.maxDecelerationOfCarLienEdit = QLineEdit(self)
        self.maxDecelerationOfCarLienEdit.move(265, 166)
        self.maxDecelerationOfCarLienEdit.resize(50, 15)
        self.maxDecelerationOfCarLienEdit.setAlignment(Qt.AlignCenter)  # 定义输入内容剧居中
        self.maxDecelerationOfCarLienEdit.setText('1')
        # 轴距 Label
        self.maxDecelerationOfCarLabel = QLabel(self)
        self.maxDecelerationOfCarLabel.move(320, 160)
        self.maxDecelerationOfCarLabel.setText('m')





        ##=========================================================第二层按钮组件


        ##======================================================第三层按钮组件
        # 数据显示部分
        # 车辆ID
        self.IDLabel = QLabel(self)
        self.IDLabel.move(65, 190)
        self.IDLabel.setText('车辆编号:')
        self.IDChangeLabel = QLabel(self)
        self.IDChangeLabel.move(120, 190)
        self.IDChangeLabel.setText('xx')

        # 左轮速度
        self.L2vLabel = QLabel(self)
        self.L2vLabel.move(65, 210)
        self.L2vLabel.setText('左轮电机速度:')
        self.L2vChangeLabel = QLabel(self)
        self.L2vChangeLabel.move(145, 210)
        self.L2vChangeLabel.setText('xxxx')
        self.L2vUnitLabel = QLabel(self)
        self.L2vUnitLabel.move(170, 210)
        self.L2vUnitLabel.setText('cm/s')

        # 右轮速度
        self.R2vLabel = QLabel(self)
        self.R2vLabel.move(210, 210)
        self.R2vLabel.setText('右轮电机速度:')
        self.R2vChangeLabel = QLabel(self)
        self.R2vChangeLabel.move(290, 210)
        self.R2vChangeLabel.setText('xxxxx')
        self.R2vUnitLabel = QLabel(self)
        self.R2vUnitLabel.move(320, 210)
        self.R2vUnitLabel.setText('cm/s')

        # 舵机转角
        self.angleLabel = QLabel(self)
        self.angleLabel.move(210, 230)
        self.angleLabel.setText('转向角度:')
        self.angleChangeLabel = QLabel(self)
        self.angleChangeLabel.move(265, 230)
        self.angleChangeLabel.setText('xxxx')
        self.angleUnitLabel = QLabel(self)
        self.angleUnitLabel.move(295, 230)
        self.angleUnitLabel.setText('°')

        # 车辆状态
        self.LPWMLabel = QLabel(self)
        self.LPWMLabel.move(210, 190)
        self.LPWMLabel.setText('车辆状态:')
        self.LPWMChangeLabel = QLabel(self)
        self.LPWMChangeLabel.move(265, 190)
        self.LPWMChangeLabel.setText('xxxx')

        # 电池电压
        self.RPWMLabel = QLabel(self)
        self.RPWMLabel.move(65, 230)
        self.RPWMLabel.setText('电池电压:')
        self.RPWMChangeLabel = QLabel(self)
        self.RPWMChangeLabel.move(120, 230)
        self.RPWMChangeLabel.setText('xxxx')
        self.RPWMUnitLabel = QLabel(self)
        self.RPWMUnitLabel.move(150, 230)
        self.RPWMUnitLabel.setText('v')

        # 横向加速度
        self.AyLabel = QLabel(self)
        self.AyLabel.move(65, 250)
        self.AyLabel.setText('横向加速度:')
        self.AyChangeLabel = QLabel(self)
        self.AyChangeLabel.move(135, 250)
        self.AyChangeLabel.setText('xxxx')
        self.AyUnitLabel = QLabel(self)
        self.AyUnitLabel.move(165, 250)
        self.AyUnitLabel.setText('m/s^2')

        # 横摆角速度
        self.YawLabel = QLabel(self)
        self.YawLabel.move(210, 250)
        self.YawLabel.setText('横摆角速度:')
        self.YawChangeLabel = QLabel(self)
        self.YawChangeLabel.move(280, 250)
        self.YawChangeLabel.setText('xxxx')
        self.YawUnitLabel = QLabel(self)
        self.YawUnitLabel.move(310, 250)
        self.YawUnitLabel.setText('°/s')

        # 电机转矩
        self.TnLabel = QLabel(self)
        self.TnLabel.move(210, 270)
        self.TnLabel.setText('电机转矩:')
        self.TnChangeLabel = QLabel(self)
        self.TnChangeLabel.move(265, 270)
        self.TnChangeLabel.setText('xxxx')
        self.TnUnitLabel = QLabel(self)
        self.TnUnitLabel.move(295, 270)
        self.TnUnitLabel.setText('N·m')

        # 横向速度
        self.VyLabel = QLabel(self)
        self.VyLabel.move(65, 270)
        self.VyLabel.setText('横向速度:')
        self.VyChangeLabel = QLabel(self)
        self.VyChangeLabel.move(125, 270)
        self.VyChangeLabel.setText('xxxx')
        self.VyUnitLabel = QLabel(self)
        self.VyUnitLabel.move(155, 270)
        self.VyUnitLabel.setText('m/s')

        # 当前经度
        self.lngLabel = QLabel(self)
        self.lngLabel.move(65, 300)
        self.lngLabel.setText('当前经度:')
        self.lngChangeLabel = QLabel(self)
        self.lngChangeLabel.move(120, 300)
        self.lngChangeLabel.setText('xxxx')
        self.lngUnitLabel = QLabel(self)
        self.lngUnitLabel.move(250, 300)
        self.lngUnitLabel.setText('°')

        # 当前纬度
        self.latLabel = QLabel(self)
        self.latLabel.move(65, 320)
        self.latLabel.setText('当前纬度:')
        self.latChangeLabel = QLabel(self)
        self.latChangeLabel.move(120, 320)
        self.latChangeLabel.setText('xxxx')
        # self.latChangeLabel.setGeometry(QRect(328, 240, 329, 27 * 4))
        # self.latChangeLabel.setWordWrap(True)
        # self.latChangeLabel.setAlignment(Qt.AlignTop)
        self.latUnitLabel = QLabel(self)
        self.latUnitLabel.move(250, 320)
        self.latUnitLabel.setText('°')



        ## 下位机上传的图像信息
        self.angleLabel = QLabel(self)
        self.angleLabel.move(400, 150)
        self.angleLabel.setText('图像:')

        pix = QPixmap('background.jpg')
        self.lb1 = QLabel(self)
        self.lb1.setGeometry(450, 5, 400, 200)  # x1 x2 x3 x4,从（x1,x2）开始显示一个x3长x4宽的矩形
        self.lb1.setPixmap(QPixmap('background.jpg'))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
        self.lb1.setStyleSheet("border: 2px solid red")


        # 方法三
        self.angleLabel = QLabel(self)  # 标签
        self.angleLabel.move(390, 350)
        self.angleLabel.setText('导航图像:')
        # 调用Mapwindow函数，建立一个他的对象
        SettingBox_Map1 = QGroupBox("导航地图")
        Map1 = Map_load2()
        v_map1_layout = QVBoxLayout()
        v_map1_layout.addWidget(Map1)
        v_map1_layout.setContentsMargins(450, 200, 50, 50)  # 左上右下距离边框的长度
        self.setLayout(v_map1_layout)
        # QApplication.processEvents()  # 使得图像界面可以实时更新


        # 状态栏显示
        # self.setGeometry(100, 100, 370, 550)
        self.setGeometry(100, 100, 900, 450)
        self.setWindowTitle('Tenth')
        self.show()

    def slot_btn_function(self):
        # self.hide()
        self.f1 = First_ID1()
        self.f1.show()



    ## 响应槽函数
    def mapshow(self, text):
        map = (Map().add(text, [list(z) for z in zip(Faker.provinces, Faker.values())], text)
               .set_global_opts(title_opts=opts.TitleOpts(title="map")))
        map.render('BD_map10.html')  # 读取对应车辆的百度地图API程序
        # self.browser.load(QUrl(QFileInfo("file:///E:/pycharm_project/TCP%2010%2025/BD_map.html").absoluteFilePath()))
        self.browser.load(QUrl(QFileInfo("BD_map10.html").absoluteFilePath()))
        print("更新BD地图============")
        if text in self.knowledge:
            self.knowledge_label.setText(self.knowledge[text])
        else:
            self.knowledge_label.setText('')

    def IDchange(self,ID):  # 更新车辆ID的槽函数
        self.IDChangeLabel.setText(ID)

    def Statechange(self,State):  # 更新车辆状态
        self.StatechangeLable.setText(str(State))


    def L2vchange(self, L2v):  # 更新左轮电机转速的槽函数
        self.L2vChangeLabel.setText(str(L2v))

    def R2vchange(self, R2v):  # 更新右轮电机转速的槽函数
        self.R2vChangeLabel.setText(str(R2v))
    def anglechange(self, angle):  # 更新转向角度的槽函数
        self.angleChangeLabel.setText(str(angle))

    def Uchange(self,U):
        self.UchangeLabel.setText(U)

    def LPWMchange(self, LPWM):
        self.LPWMChangeLabel.setText(str(LPWM))

    def RPWMchange(self,RPWM):
        self.RPWMChangeLabel.setText(str(RPWM))

    def Aychange(self,Ay):
        self.AyChangeLabel.setText(str(Ay))

    def Yawchange(self,Yaw):
        self.YawChangeLabel.setText(str(Yaw))

    def Tnchange(self,Tn):
        self.TnChangeLabel.setText(str(Tn))

    def Vychange(self,Vy):
        self.VyChangeLabel.setText(str(Vy))


    def lngChange(self,lng):
        self.lngChangeLabel.setText(str(lng))

    def latChange(self,lat):
        self.latChangeLabel.setText(str(lat))


    # 修改显示的图像
    def QPixmapchange(self,Image):
        self.lb1.setPixmap(QPixmap(str(Image)))
        self.lb1.setScaledContents(True)  # 图片自适应框的大小
    # 修改显示的图像


    def start(self):  # start按钮的槽函数
        global startFlag
        startFlag = 1



    def listenToClient(self):  # 点击Listen后的响应事件
        localIP = self.serverIPLineEdit.text()  # 定义Listener类中的属性值
        localPort = self.serverPortLineEdit.text()
        serverIP = self.clientIPLineEdit.text()
        serverPort = self.clientPortLineEdit.text()
        length = self.lengthOfCarLienEdit.text()
        weight = self.weightOfCarLienEdit.text()
        maxV = self.maxVelocityOfCarLienEdit.text()
        minV = self.minVelocityOfCarLienEdit.text()
        maxA = self.maxAccelationOfCarLienEdit.text()
        maxD = self.maxDecelerationOfCarLienEdit.text()
        self._thread = Listener_ID10(localIP, int(localPort), serverIP, int(serverPort),
                                int(length), int(weight), int(maxV),
                                int(minV), int(maxA), int(maxD))  # 定义一个Listener的对象
        self._thread.sigID_ID10.connect(self.IDchange)  # 调用修改参数方法，实时传输显示下位机传输的数据
        self._thread.sigRPWM_ID10.connect(self.RPWMchange)
        self._thread.sigLPWM_ID10.connect(self.LPWMchange)
        self._thread.sigL2v_ID10.connect(self.L2vchange)
        self._thread.sigR2v_ID10.connect(self.R2vchange)
        self._thread.sigangle_ID10.connect(self.anglechange)
        self._thread.sigImage_ID10.connect(self.QPixmapchange)  # 更新显示的图片

        self._thread.sigAy_ID10.connect(self.Aychange)
        self._thread.sigYaw_ID10.connect(self.Yawchange)
        self._thread.sigTn_ID10.connect(self.Tnchange)
        self._thread.sigVy_ID10.connect(self.Vychange)

        self._thread.siglat_ID10.connect(self.latChange)
        self._thread.siglng_ID10.connect(self.lngChange)  # 更新当前经纬度数据


        self._thread.start()  # 执行Litener类中的run方法
        self.listenButton.setText('Listening')  # 开始执行监听后标识为“正在监听”




    def askstate(self):  # askstate按钮的槽函数
        global askstateFlag_ID10
        askstateFlag_ID10 = 1
        print('askstateFlag_ID10_change_to:', askstateFlag_ID10)

    def askimage(self):  # askimage按钮的槽函数
        global askimageFlag_ID10
        askimageFlag_ID10 = 1
        print('askimageFlag_ID10_change_to:', askimageFlag_ID10)

        # self._thread = Image_listen()
        # self._thread.start()

    def send(self):  # send按钮的槽函数
        global sendFlag_ID10
        sendFlag_ID10 = 1
        print('sendFlag_ID10_change_to:', sendFlag_ID10)




    def closeEvent(self, event):  # GUI窗口右上角关闭按钮的槽函数
        reply = QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QMessageBox.Yes |
            QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()




def main():
    app = QApplication(sys.argv)
    w = First_ID1()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
