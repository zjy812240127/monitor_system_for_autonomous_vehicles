# 1.定义一个函数recv_from_up从上位机接收数据，然后调用函数send_to_car将数据转发给小车
# 2.定义一个函数recv_from_car从小车接收数据，然后调用函数send_to_up将数据发给上位机
# 3.定义函数send_to_car
# 4.定义函数send_to_up
# 5.建立线程t1 = threading.Thread(target = recv_from_up)
# 6.建立线程t1 = threading.Thread(target = recv_from_car)


import socket
import time       # 可以用来得到时间戳
import threading   #同时执行多任务
import struct



def main():

    # 定义写入log事件的方法
    def writelog(log_data):
        # 获取当前时间（含毫秒）
        ct = time.time()
        local_time = time.localtime(ct)
        data_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
        data_secs = (ct - int(ct)) * 1000
        time_stamp = "%s.%03d" % (data_head, data_secs)

        with open("log.txt","a") as file1:
            file1.write(time_stamp + ":" + log_data + '\n')  # with open方法就不需要每次调用.close方法
            print("成功写入数据")


# 车辆一：
#  ===========================定义数据接收函数并调用数据发送函数=======================
    def recv_from_up():
        global ip_Ali
        global port_up
        global tcp_server_up
        global  client_up
        print("从上位机接收数据为：")

        tcp_server_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_up.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用，下位机断开连接后不用再重启服务器，下位机可以直接在此发起连接请求
        # ip_Ali = input("请输入阿里云的公网ip"+"\n") # 服务器的ip地址
        ip_Ali = "47.102.36.187"  # 服务器的ip地址
        # port_up = input("请输入与上位机联通的端口:")  # 服务器的端口号
        port_up = 8082  # 接通上位机的端口号
        tcp_server_up.bind(("0", 8082 ))
        tcp_server_up.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            # flag = True
            client_up, cltadd_up = tcp_server_up.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            # while True:
            i = 0  # 记录发送次数

            while True:
                # data_from_up = client_up.recv(1024).decode('utf-8')  # 接收客户端发送的数据进行解码
                # data_from_up = client_up.recv(1024)  # 接收客户端发送的数据进行解码

                #=================写入log文档
                # 1、解码如果判为上位机上发的经纬度数据，则写入文档：time: 上位机上发经纬度数据
                # 2、解码如果判为上位机上发的请求状态数据的指令，则写入文档：time: 上位机上发请求状态数据的指令
                # 3、解码如果判为上位机上发的请求图像数据的指令，则写入文档：time: 上位机上发请求图像数据的指令
                # 4、分三种情况写send_to_car,每种情况后写入文档：time: 向下位机发送......
                while True:

                    data_from_up1 = client_up.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        m1 = struct.unpack('B',data_from_up1)
                    except:
                        print("解析包头错误")
                    if (m1 == (255,)):  # 如果读到包头则一次性读完包头
                        data_from_up2 = client_up.recv(3)
                        break

                data_from_up3 = client_up.recv(20)
                try:
                    x5, x6, x7, x8, x9 = struct.unpack('5i', data_from_up3)  # x5:包长x6：包序号 x7:时间戳 x8:数据域1 x9:数据域2
                except:
                    print("解析前缀信息错误")

                if (x8 ==1):
                    # 上位机下发经纬度数据
                    data_from_up_lnglat = client_up.recv(1024)
                    log1 = "ID1 收到上位机要传给下位机的未来经纬度序列"
                    writelog(log1)  # 写入事件

                    data_from_up_Lnglat_ID1 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_lnglat
                    send_to_car(data_from_up_Lnglat_ID1)  # 将数据转发
                    log2 ="ID1 将上位机发送的未来经纬度序列传输给下位机"
                    writelog(log2)
                    print("成功转发经纬度给小车")

                if (x8 == 2):
                    # 请求上发状态数据
                    data_from_up_state = client_up.recv(1024)
                    log3 = "ID1 收到上位机要传给下位机的请求状态指令"
                    writelog(log3)  # 写入事件

                    data_from_up_State_ID1 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_state
                    send_to_car(data_from_up_State_ID1)  # 将数据转发
                    log4 = "ID1 将上位机发送的请求状态指令传输给下位机"
                    writelog(log4)
                    print("成功转发状态请求指令给小车")

                if (x8 == 3):
                    # 请求上发图像数据
                    data_from_up_image = client_up.recv(1024)
                    log5 = "ID1 收到上位机要传给下位机的请求图像指令"
                    writelog(log5)  # 写入事件

                    data_from_up_Image_ID1 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_image
                    send_to_car(data_from_up_Image_ID1)  # 将数据转发
                    log6 = "ID1 将上位机发送的请求图像指令传输给下位机"
                    writelog(log6)
                    print("成功转发图像请求指令给小车")



                #=================写入log文档

                # print("客户端发送的数据是：", data_from_up)
                # # if data:  # 如果收到的数据不为空，表示客户端仍在请求服务，继续为其服务
                # if data_from_up:
                #     send_to_car(data_from_up)  # 将数据转发
                #     print("成功转发给小车")
                #     # break
                # else:
                #     break

# =======================================定义数据发送函数======================================
    def send_to_car(data_from_up):
        # print("发送给小车的数据为：", data_from_up)
        global tcp_server_car
        global client_car
        flag = True
        # -----------------------------------------------------------------------------------------------
        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_car = "2222222"
            # client_car.send(data_to_car.encode("utf-8"))  # 向下位机发送数据包
            client_car.send(data_from_up)  # 向下位机发送数据包
            break


#  ===========================定义数据接收函数并调用数据发送函数=======================
    def recv_from_car():
        global ip_Ali
        global port_car  # 与小车接通的端口
        global tcp_server_car
        global client_car
        print("从小车接收数据为：")

        tcp_server_car = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_car.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

        # ip_Ali = input("请输入阿里云的公网ip")  # 服务器的ip地址
        # port_car = input("请输入与小车联通的端口:")  # 服务器的端口号
        port_car = 8083  # 与小车接通的端口号
        tcp_server_car.bind(("0", 8083))
        tcp_server_car.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            # flag = True
            client_car, cltadd_car = tcp_server_car.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            # while True:
            i = 0  # 记录发送次数
            while True:

                while True:

                    dataFromCar1 = client_car.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        z1 = struct.unpack('B',dataFromCar1)
                    except:
                        print("解析包头错误")
                    if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                        dataFromCar2 = client_car.recv(3)
                        break

                dataFromCar3 = client_car.recv(24)
                try:
                    x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar3)
                except:
                    print("解析前缀信息错误")

                if (x9 == 3):  # 如果上传数据字节数过多，则为图像信息
                    print("上传的是图像数据")

                    def ImageRead(client_car):
                        data_image1 = client_car.recv(1)
                        try:
                            image_geshi = struct.unpack('B', data_image1)
                        except:
                            print("解析图像格式错误")
                        # print("图像格式为：", image_geshi)
                        data_image2 = client_car.recv(4)
                        try:
                            image_len = struct.unpack('1I', data_image2)
                        except:
                            print("解析图像字节数错误")
                        # print("图像字节数：", image_len)
                        image_msg = b''
                        len1 = int(image_len[0])
                        image_length = len1  # 图像数据的字节长度
                        readlength = 0  # 从缓冲区读取的字节数
                        while (len1 > 0):
                            if len1 > 1024:  # 如果剩余图像字节数大于1024
                                buffer = client_car.recv(1024, socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                len1 = len1 - 1024
                                readlength += 1024
                            else:
                                buffer = client_car.recv(len1, socket.MSG_WAITALL)
                                image_msg += buffer
                                readlength += len1
                                break

                        print("从缓冲区读取的字节数为：", readlength)
                        print("缓冲区剩余图像数据块字节数为：", image_length - readlength)

                        # tianchong_num = image_length % 4  # 计算填充的字节数
                        # shengyu_num = tianchong_num + 16  # 剩下要读的字节数
                        # data_image_shengyu  = client_car.recv(shengyu_num)
                        # print("读完图像数据块后余下的字节数为，检测是否读到包尾，验证帧信息里的数据块字节数是否正确", data_image_shengyu)

                        # 循环读取余下的字节，直到读完四个字节的包尾
                        left = client_car.recv(1)
                        buffer_left = b''
                        while 1:
                            try:
                                left_baowei = struct.unpack('B', left)
                                print("检测包尾读到的数据为", left_baowei)
                            except:
                                print("检测包尾第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                            if (left_baowei != (204,)):  # 如果读到包尾则一次性读完包尾
                                buffer_left +=  left
                                left = client_car.recv(1)
                            else:
                                buffer_left+=  left
                                left_2 = client_car.recv(3)
                                buffer_left+= left_2
                                print("读完四个包尾")
                                break


                        # data_from_car_image_ID1 =dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg +data_image_shengyu
                        data_from_car_image_ID1 = dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg + buffer_left
                        log7 = "ID1 收到下位机上传的图像数据"
                        writelog(log7)  # 写入事件

                        send_to_up(data_from_car_image_ID1)  # 将图像数据转发
                        log8 = "ID1 将下位机上传的图像数据发送给上位机"
                        writelog(log8)  # 写入事件

                    t_image_ID1 = threading.Thread(target=ImageRead, args=(client_car,))
                    t_image_ID1.start()




                elif (x9 == 0):
                    print("上传的是无效数据")

                elif ( x9 == 1):
                    print("上传的是状态数据")
                    dataFromCar_state = client_car.recv(40)
                    data_from_car_state_ID1 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_state
                    log9 = "ID1 收到下位机上传的状态数据"
                    writelog(log9)  # 写入事件

                    send_to_up(data_from_car_state_ID1)
                    log10 = "ID1 将下位机上传的状态数据发送给上位机"
                    writelog(log10)  # 写入事件


                elif (x9 == 2):
                    print("上传的是经纬度数据")
                    dataFromCar_lnglat = client_car.recv(36)
                    data_from_car_lnglat_ID1 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_lnglat
                    log11 = "ID1 收到下位机上传的小车当前时刻经纬度数据"
                    writelog(log11)  # 写入事件

                    send_to_up(data_from_car_lnglat_ID1)
                    log12 = "ID1 将下位机上传的小车当前时刻经纬度数据发送给上位机"
                    writelog(log12)  # 写入事件


                else:
                    print("数据上发错误")
                    # break

# =======================================定义数据发送函数===============================
    def send_to_up(data_from_car):
        # print("发送给上位机的数据为：", data_from_car)
        global tcp_server_up
        global client_up
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_up = "1111111"
            # client_up.send(data_to_up.encode("utf-8"))  # 向下位机发送数据包
            client_up.send(data_from_car)  # 向下位机发送数据包
            break
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# 车辆二：
        #  ===========================定义数据接收函数并调用数据发送函数=======================
    def recv_from_up_ID2():
            global client_up_ID2
            print("从上位机接收数据为：")
            tcp_server_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_server_up.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
            ip_Ali = "47.102.36.187"  # 服务器的ip地址
            tcp_server_up.bind(("0", 8084))
            tcp_server_up.listen(128)
            flag = True

            while True:  # 在子类中重写run方法，建立与客户端的链接、通信
                print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
                client_up_ID2, cltadd_up = tcp_server_up.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
                print('监听到wifi连接')
                time.sleep(0.5)
                i = 0  # 记录发送次数

                while True:
                    # data_from_up = client_up.recv(1024).decode('utf-8')  # 接收客户端发送的数据进行解码
                    # data_from_up = client_up.recv(1024)  # 接收客户端发送的数据进行解码

                    # =================写入log文档
                    # 1、解码如果判为上位机上发的经纬度数据，则写入文档：time: 上位机上发经纬度数据
                    # 2、解码如果判为上位机上发的请求状态数据的指令，则写入文档：time: 上位机上发请求状态数据的指令
                    # 3、解码如果判为上位机上发的请求图像数据的指令，则写入文档：time: 上位机上发请求图像数据的指令
                    # 4、分三种情况写send_to_car,每种情况后写入文档：time: 向下位机发送......
                    while True:

                        data_from_up1 = client_up_ID2.recv(1)  # 接收客户端发送的数据进行解码
                        print("逐个读取字节")
                        try:
                            m1 = struct.unpack('B', data_from_up1)
                        except:
                            print("解析包头错误")
                        if (m1 == (255,)):  # 如果读到包头则一次性读完包头
                            data_from_up2 = client_up_ID2.recv(3)
                            break

                    data_from_up3 = client_up_ID2.recv(20)
                    try:
                        x5, x6, x7, x8, x9 = struct.unpack('5i', data_from_up3)  # x5:包长x6：包序号 x7:时间戳 x8:数据域1 x9:数据域2
                    except:
                        print("解析前缀信息错误")

                    if (x8 == 1):
                        # 上位机下发经纬度数据
                        data_from_up_lnglat = client_up_ID2.recv(1024)
                        log1 = "ID2 收到上位机要传给下位机的未来经纬度序列"
                        writelog(log1)  # 写入事件

                        data_from_up_Lnglat_ID2 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_lnglat
                        send_to_car_ID2(data_from_up_Lnglat_ID2)  # 将数据转发
                        log2 = "ID2 将上位机发送的未来经纬度序列传输给下位机"
                        writelog(log2)
                        print("成功转发经纬度给小车")

                    if (x8 == 2):
                        # 请求上发状态数据
                        data_from_up_state = client_up_ID2.recv(1024)
                        log3 = "ID2 收到上位机要传给下位机的请求状态指令"
                        writelog(log3)  # 写入事件

                        data_from_up_State_ID2 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_state
                        send_to_car_ID2(data_from_up_State_ID2)  # 将数据转发
                        log4 = "ID2 将上位机发送的请求状态指令传输给下位机"
                        writelog(log4)
                        print("成功转发状态请求指令给小车")

                    if (x8 == 3):
                        # 请求上发图像数据
                        data_from_up_image = client_up_ID2.recv(1024)
                        log5 = "ID2 收到上位机要传给下位机的请求图像指令"
                        writelog(log5)  # 写入事件

                        data_from_up_Image_ID2 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_image
                        send_to_car_ID2(data_from_up_Image_ID2)  # 将数据转发
                        log6 = "ID2 将上位机发送的请求图像指令传输给下位机"
                        writelog(log6)
                        print("成功转发图像请求指令给小车")

                    # =================写入log文档

                    # print("客户端发送的数据是：", data_from_up)
                    # # if data:  # 如果收到的数据不为空，表示客户端仍在请求服务，继续为其服务
                    # if data_from_up:
                    #     send_to_car_ID2(data_from_up)  # 将数据转发
                    #     print("成功转发给小车")
                    #     # break
                    # else:
                    #     break
        # =======================================定义数据发送函数======================================
    def send_to_car_ID2(data_from_up):
            # print("发送给小车的数据为：", data_from_up)
            global client_car_ID2
            flag = True
            # -----------------------------------------------------------------------------------------------
            while True:  # 在子类中重写run方法，建立与客户端的链接、通信
                data_to_car = "2222222"
                client_car_ID2.send(data_from_up)  # 向下位机发送数据包
                break

        #  ===========================定义数据接收函数并调用数据发送函数=======================
    def recv_from_car_ID2():
        global ip_Ali
        global port_car  # 与小车接通的端口
        global tcp_server_car_ID2
        global client_car_ID2
        print("从小车接收数据为：")

        tcp_server_car_ID2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_car_ID2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用


        tcp_server_car_ID2.bind(("0", 8085))
        tcp_server_car_ID2.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            # flag = True
            client_car_ID2, cltadd_car = tcp_server_car_ID2.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            # while True:
            i = 0  # 记录发送次数
            while True:

                while True:

                    dataFromCar1_ID2 = client_car_ID2.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        z1_ID2 = struct.unpack('B', dataFromCar1_ID2)
                    except:
                        print("解析包头错误")
                    if (z1_ID2 == (221,)):  # 如果读到包头则一次性读完包头
                        dataFromCar2_ID2 = client_car_ID2.recv(3)
                        break

                dataFromCar3_ID2 = client_car_ID2.recv(24)
                try:
                    x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar3_ID2)
                except:
                    print("解析前缀信息错误")

                if (x9 == 3):  # 如果上传数据字节数过多，则为图像信息
                    print("上传的是图像数据")

                    def ImageRead(client_car_ID2):
                        data_image1 = client_car_ID2.recv(1)
                        try:
                            image_geshi = struct.unpack('B', data_image1)
                        except:
                            print("解析图像格式错误")
                        # print("图像格式为：", image_geshi)
                        data_image2 = client_car_ID2.recv(4)
                        try:
                            image_len = struct.unpack('1I', data_image2)
                        except:
                            print("解析图像字节数错误")
                        # print("图像字节数：", image_len)
                        image_msg = b''
                        len1 = int(image_len[0])
                        image_length = len1  # 图像数据的字节长度
                        readlength = 0  # 从缓冲区读取的字节数
                        while (len1 > 0):
                            if len1 > 1024:  # 如果剩余图像字节数大于1024
                                buffer = client_car_ID2.recv(1024,
                                                         socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                len1 = len1 - 1024
                                readlength += 1024
                            else:
                                buffer = client_car_ID2.recv(len1, socket.MSG_WAITALL)
                                image_msg += buffer
                                readlength += len1
                                break

                        print("从缓冲区读取的字节数为：", readlength)
                        print("缓冲区剩余图像数据块字节数为：", image_length - readlength)

                        # tianchong_num = image_length % 4  # 计算填充的字节数
                        # shengyu_num = tianchong_num + 16  # 剩下要读的字节数
                        # data_image_shengyu  = client_car.recv(shengyu_num)
                        # print("读完图像数据块后余下的字节数为，检测是否读到包尾，验证帧信息里的数据块字节数是否正确", data_image_shengyu)

                        # 循环读取余下的字节，直到读完四个字节的包尾
                        left = client_car_ID2.recv(1)
                        buffer_left = b''
                        while 1:
                            try:
                                left_baowei = struct.unpack('B', left)
                                print("检测包尾读到的数据为", left_baowei)
                            except:
                                print("检测包尾第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                            if (left_baowei != (204,)):  # 如果读到包尾则一次性读完包尾
                                buffer_left += left
                                left = client_car_ID2.recv(1)
                            else:
                                buffer_left += left
                                left_2 = client_car_ID2.recv(3)
                                buffer_left += left_2
                                print("读完四个包尾")
                                break

                        # data_from_car_image_ID1 =dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg +data_image_shengyu
                        data_from_car_image_ID2 = dataFromCar1_ID2 + dataFromCar2_ID2 + dataFromCar3_ID2 + data_image1 + data_image2 + image_msg + buffer_left
                        log7 = "ID2 收到下位机上传的图像数据"
                        writelog(log7)  # 写入事件

                        send_to_up(data_from_car_image_ID2)  # 将图像数据转发
                        log8 = "ID2 将下位机上传的图像数据发送给上位机"
                        writelog(log8)  # 写入事件

                    t_image_ID2 = threading.Thread(target=ImageRead, args=(client_car_ID2,))
                    t_image_ID2.start()


                elif (x9 == 0):
                    print("上传的是无效数据")

                elif (x9 == 1):
                    print("上传的是状态数据")
                    dataFromCar_state_ID2 = client_car_ID2.recv(40)
                    data_from_car_state_ID2 = dataFromCar1_ID2 + dataFromCar2_ID2 + dataFromCar3_ID2 + dataFromCar_state_ID2
                    log9 = "ID2 收到下位机上传的状态数据"
                    writelog(log9)  # 写入事件

                    send_to_up_ID2(data_from_car_state_ID2)
                    log10 = "ID2 将下位机上传的状态数据发送给上位机"
                    writelog(log10)  # 写入事件


                elif (x9 == 2):
                    print("上传的是经纬度数据")
                    dataFromCar_lnglat_ID2 = client_car_ID2.recv(36)
                    data_from_car_lnglat_ID2 = dataFromCar1_ID2 + dataFromCar2_ID2 + dataFromCar3_ID2 + dataFromCar_lnglat_ID2
                    log11 = "ID2 收到下位机上传的小车当前时刻经纬度数据"
                    writelog(log11)  # 写入事件

                    send_to_up_ID2(data_from_car_lnglat_ID2)
                    log12 = "ID2 将下位机上传的小车当前时刻经纬度数据发送给上位机"
                    writelog(log12)  # 写入事件


                else:
                    print("数据上发错误")
                    # break

        # =======================================定义数据发送函数===============================

        # =======================================定义数据发送函数===============================

    def send_to_up_ID2(data_from_car_ID2):
            # print("发送给上位机的数据为：", data_from_car_ID2)
            global tcp_server_up
            global client_up_ID2
            flag = True

            while True:  # 在子类中重写run方法，建立与客户端的链接、通信
                data_to_up = "1111111"
                # client_up.send(data_to_up.encode("utf-8"))  # 向下位机发送数据包
                client_up_ID2.send(data_from_car_ID2)  # 向下位机发送数据包
                break
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# 车辆三：
#  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_up_ID3():
        global client_up_ID3
        print("从上位机接收数据为：")
        tcp_server_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_up.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
        ip_Ali = "47.102.36.187"  # 服务器的ip地址
        tcp_server_up.bind(("0", 8086))
        tcp_server_up.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            client_up_ID3, cltadd_up = tcp_server_up.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            i = 0  # 记录发送次数

            while True:
                # data_from_up = client_up.recv(1024).decode('utf-8')  # 接收客户端发送的数据进行解码
                # data_from_up = client_up.recv(1024)  # 接收客户端发送的数据进行解码

                # =================写入log文档
                # 1、解码如果判为上位机上发的经纬度数据，则写入文档：time: 上位机上发经纬度数据
                # 2、解码如果判为上位机上发的请求状态数据的指令，则写入文档：time: 上位机上发请求状态数据的指令
                # 3、解码如果判为上位机上发的请求图像数据的指令，则写入文档：time: 上位机上发请求图像数据的指令
                # 4、分三种情况写send_to_car,每种情况后写入文档：time: 向下位机发送......
                while True:

                    data_from_up1 = client_up_ID3.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        m1 = struct.unpack('B', data_from_up1)
                    except:
                        print("解析包头错误")
                    if (m1 == (255,)):  # 如果读到包头则一次性读完包头
                        data_from_up2 = client_up_ID3.recv(3)
                        break

                data_from_up3 = client_up_ID3.recv(20)
                try:
                    x5, x6, x7, x8, x9 = struct.unpack('5i', data_from_up3)  # x5:包长x6：包序号 x7:时间戳 x8:数据域1 x9:数据域2
                except:
                    print("解析前缀信息错误")

                if (x8 == 1):
                    # 上位机下发经纬度数据
                    data_from_up_lnglat = client_up_ID3.recv(1024)
                    log1 = "ID3 收到上位机要传给下位机的未来经纬度序列"
                    writelog(log1)  # 写入事件

                    data_from_up_Lnglat_ID3 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_lnglat
                    send_to_car_ID3(data_from_up_Lnglat_ID3)  # 将数据转发
                    log2 = "ID3 将上位机发送的未来经纬度序列传输给下位机"
                    writelog(log2)
                    print("成功转发经纬度给小车")

                if (x8 == 2):
                    # 请求上发状态数据
                    data_from_up_state = client_up_ID3.recv(1024)
                    log3 = "ID3 收到上位机要传给下位机的请求状态指令"
                    writelog(log3)  # 写入事件

                    data_from_up_State_ID3 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_state
                    send_to_car_ID3(data_from_up_State_ID3)  # 将数据转发
                    log4 = "ID3 将上位机发送的请求状态指令传输给下位机"
                    writelog(log4)
                    print("成功转发状态请求指令给小车")

                if (x8 == 3):
                    # 请求上发图像数据
                    data_from_up_image = client_up_ID3.recv(1024)
                    log5 = "ID3 收到上位机要传给下位机的请求图像指令"
                    writelog(log5)  # 写入事件

                    data_from_up_Image_ID3 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_image
                    send_to_car_ID3(data_from_up_Image_ID3)  # 将数据转发
                    log6 = "ID3 将上位机发送的请求图像指令传输给下位机"
                    writelog(log6)
                    print("成功转发图像请求指令给小车")

                # =================写入log文档

                # print("客户端发送的数据是：", data_from_up)
                # # if data:  # 如果收到的数据不为空，表示客户端仍在请求服务，继续为其服务
                # if data_from_up:
                #     send_to_car_ID3(data_from_up)  # 将数据转发
                #     print("成功转发给小车")
                #     # break
                # else:
                #     break
        # =======================================定义数据发送函数======================================

    def send_to_car_ID3(data_from_up):
        # print("发送给小车的数据为：", data_from_up)
        global client_car_ID3
        flag = True
        # -----------------------------------------------------------------------------------------------
        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_car = "2222222"
            client_car_ID3.send(data_from_up)  # 向下位机发送数据包
            break

        #  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_car_ID3():
        global ip_Ali
        global port_car  # 与小车接通的端口
        global tcp_server_car_ID3
        global client_car_ID3
        print("从小车接收数据为：")

        tcp_server_car_ID3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_car_ID3.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

        # ip_Ali = input("请输入阿里云的公网ip")  # 服务器的ip地址
        # port_car = input("请输入与小车联通的端口:")  # 服务器的端口号
        port_car = 8083  # 与小车接通的端口号
        tcp_server_car_ID3.bind(("0", 8087))
        tcp_server_car_ID3.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            # flag = True
            client_car_ID3, cltadd_car = tcp_server_car_ID3.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            # while True:
            i = 0  # 记录发送次数
            while True:

                while True:

                    dataFromCar1_ID3 = client_car_ID3.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        z1 = struct.unpack('B', dataFromCar1_ID3)
                    except:
                        print("解析包头错误")
                    if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                        dataFromCar2_ID3 = client_car_ID3.recv(3)
                        break

                dataFromCar3_ID3 = client_car_ID3.recv(24)
                try:
                    x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar3_ID3)
                except:
                    print("解析前缀信息错误")

                if (x9 == 3):  # 如果上传数据字节数过多，则为图像信息
                    print("上传的是图像数据")

                    def ImageRead(client_car_ID3):
                        data_image1 = client_car_ID3.recv(1)
                        try:
                            image_geshi = struct.unpack('B', data_image1)
                        except:
                            print("解析图像格式错误")
                        # print("图像格式为：", image_geshi)
                        data_image2 = client_car_ID3.recv(4)
                        try:
                            image_len = struct.unpack('1I', data_image2)
                        except:
                            print("解析图像字节数错误")
                        # print("图像字节数：", image_len)
                        image_msg = b''
                        len1 = int(image_len[0])
                        image_length = len1  # 图像数据的字节长度
                        readlength = 0  # 从缓冲区读取的字节数
                        while (len1 > 0):
                            if len1 > 1024:  # 如果剩余图像字节数大于1024
                                buffer = client_car_ID3.recv(1024,
                                                             socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                len1 = len1 - 1024
                                readlength += 1024
                            else:
                                buffer = client_car_ID3.recv(len1, socket.MSG_WAITALL)
                                image_msg += buffer
                                readlength += len1
                                break

                        print("从缓冲区读取的字节数为：", readlength)
                        print("缓冲区剩余图像数据块字节数为：", image_length - readlength)

                        # tianchong_num = image_length % 4  # 计算填充的字节数
                        # shengyu_num = tianchong_num + 16  # 剩下要读的字节数
                        # data_image_shengyu  = client_car.recv(shengyu_num)
                        # print("读完图像数据块后余下的字节数为，检测是否读到包尾，验证帧信息里的数据块字节数是否正确", data_image_shengyu)

                        # 循环读取余下的字节，直到读完四个字节的包尾
                        left = client_car_ID3.recv(1)
                        buffer_left = b''
                        while 1:
                            try:
                                left_baowei = struct.unpack('B', left)
                                print("检测包尾读到的数据为", left_baowei)
                            except:
                                print("检测包尾第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                            if (left_baowei != (204,)):  # 如果读到包尾则一次性读完包尾
                                buffer_left += left
                                left = client_car_ID3.recv(1)
                            else:
                                buffer_left += left
                                left_2 = client_car_ID3.recv(3)
                                buffer_left += left_2
                                print("读完四个包尾")
                                break

                        # data_from_car_image_ID1 =dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg +data_image_shengyu
                        data_from_car_image_ID3 = dataFromCar1_ID3 + dataFromCar2_ID3 + dataFromCar3_ID3 + data_image1 + data_image2 + image_msg + buffer_left
                        log7 = "ID3 收到下位机上传的图像数据"
                        writelog(log7)  # 写入事件

                        send_to_up(data_from_car_image_ID3)  # 将图像数据转发
                        log8 = "ID3 将下位机上传的图像数据发送给上位机"
                        writelog(log8)  # 写入事件

                    t_image_ID3 = threading.Thread(target=ImageRead, args=(client_car_ID3,))
                    t_image_ID3.start()



                elif (x9 == 0):
                    print("上传的是无效数据")

                elif (x9 == 1):
                    print("上传的是状态数据")
                    dataFromCar_state = client_car_ID3.recv(40)
                    data_from_car_state_ID3 = dataFromCar1_ID3 + dataFromCar2_ID3 + dataFromCar3_ID3 + dataFromCar_state
                    log9 = "ID3 收到下位机上传的状态数据"
                    writelog(log9)  # 写入事件

                    send_to_up_ID3(data_from_car_state_ID3)
                    log10 = "ID3 将下位机上传的状态数据发送给上位机"
                    writelog(log10)  # 写入事件


                elif (x9 == 2):
                    print("上传的是经纬度数据")
                    dataFromCar_lnglat = client_car_ID3.recv(36)
                    data_from_car_lnglat_ID3 = dataFromCar1_ID3 + dataFromCar2_ID3 + dataFromCar3_ID3 + dataFromCar_lnglat
                    log11 = "ID3 收到下位机上传的小车当前时刻经纬度数据"
                    writelog(log11)  # 写入事件

                    send_to_up_ID3(data_from_car_lnglat_ID3)
                    log12 = "ID3 将下位机上传的小车当前时刻经纬度数据发送给上位机"
                    writelog(log12)  # 写入事件


                else:
                    print("数据上发错误")
                    # break

        # =======================================定义数据发送函数===============================

    def send_to_up_ID3(data_from_car):
        # print("发送给上位机的数据为：", data_from_car)
        global tcp_server_up
        global client_up_ID3
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_up = "1111111"
            # client_up.send(data_to_up.encode("utf-8"))  # 向下位机发送数据包
            client_up_ID3.send(data_from_car)  # 向下位机发送数据包
            break


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# 车辆四：
#  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_up_ID4():
        global client_up_ID4
        print("从上位机接收数据为：")
        tcp_server_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_up.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
        ip_Ali = "47.102.36.187"  # 服务器的ip地址
        tcp_server_up.bind(("0", 8088))
        tcp_server_up.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            client_up_ID4, cltadd_up = tcp_server_up.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            i = 0  # 记录发送次数

            while True:
                # data_from_up = client_up.recv(1024).decode('utf-8')  # 接收客户端发送的数据进行解码
                # data_from_up = client_up.recv(1024)  # 接收客户端发送的数据进行解码

                # =================写入log文档
                # 1、解码如果判为上位机上发的经纬度数据，则写入文档：time: 上位机上发经纬度数据
                # 2、解码如果判为上位机上发的请求状态数据的指令，则写入文档：time: 上位机上发请求状态数据的指令
                # 3、解码如果判为上位机上发的请求图像数据的指令，则写入文档：time: 上位机上发请求图像数据的指令
                # 4、分三种情况写send_to_car,每种情况后写入文档：time: 向下位机发送......
                while True:

                    data_from_up1 = client_up_ID4.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        m1 = struct.unpack('B', data_from_up1)
                    except:
                        print("解析包头错误")
                    if (m1 == (255,)):  # 如果读到包头则一次性读完包头
                        data_from_up2 = client_up_ID4.recv(3)
                        break

                data_from_up3 = client_up_ID4.recv(20)
                try:
                    x5, x6, x7, x8, x9 = struct.unpack('5i', data_from_up3)  # x5:包长x6：包序号 x7:时间戳 x8:数据域1 x9:数据域2
                except:
                    print("解析前缀信息错误")

                if (x8 == 1):
                    # 上位机下发经纬度数据
                    data_from_up_lnglat = client_up_ID4.recv(1024)
                    log1 = "ID4 收到上位机要传给下位机的未来经纬度序列"
                    writelog(log1)  # 写入事件

                    data_from_up_Lnglat_ID4 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_lnglat
                    send_to_car_ID4(data_from_up_Lnglat_ID4)  # 将数据转发
                    log2 = "ID4 将上位机发送的未来经纬度序列传输给下位机"
                    writelog(log2)
                    print("成功转发经纬度给小车")

                if (x8 == 2):
                    # 请求上发状态数据
                    data_from_up_state = client_up_ID4.recv(1024)
                    log3 = "ID4 收到上位机要传给下位机的请求状态指令"
                    writelog(log3)  # 写入事件

                    data_from_up_State_ID4 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_state
                    send_to_car_ID4(data_from_up_State_ID4)  # 将数据转发
                    log4 = "ID4 将上位机发送的请求状态指令传输给下位机"
                    writelog(log4)
                    print("成功转发状态请求指令给小车")

                if (x8 == 3):
                    # 请求上发图像数据
                    data_from_up_image = client_up_ID4.recv(1024)
                    log5 = "ID4 收到上位机要传给下位机的请求图像指令"
                    writelog(log5)  # 写入事件

                    data_from_up_Image_ID4 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_image
                    send_to_car_ID4(data_from_up_Image_ID4)  # 将数据转发
                    log6 = "ID4 将上位机发送的请求图像指令传输给下位机"
                    writelog(log6)
                    print("成功转发图像请求指令给小车")

                # =================写入log文档

                # print("客户端发送的数据是：", data_from_up)
                # # if data:  # 如果收到的数据不为空，表示客户端仍在请求服务，继续为其服务
                # if data_from_up:
                #     send_to_car_ID4(data_from_up)  # 将数据转发
                #     print("成功转发给小车")
                #     # break
                # else:
                #     break
        # =======================================定义数据发送函数======================================

    def send_to_car_ID4(data_from_up):
        # print("发送给小车的数据为：", data_from_up)
        global client_car_ID4
        flag = True
        # -----------------------------------------------------------------------------------------------
        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_car = "2222222"
            client_car_ID4.send(data_from_up)  # 向下位机发送数据包
            break

        #  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_car_ID4():
        global ip_Ali
        global port_car  # 与小车接通的端口
        global tcp_server_car
        global client_car_ID4
        print("从小车接收数据为：")

        tcp_server_car = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_car.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

        # ip_Ali = input("请输入阿里云的公网ip")  # 服务器的ip地址
        # port_car = input("请输入与小车联通的端口:")  # 服务器的端口号
        port_car = 8083  # 与小车接通的端口号
        tcp_server_car.bind(("0", 8089))
        tcp_server_car.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            # flag = True
            client_car_ID4, cltadd_car = tcp_server_car.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            # while True:
            i = 0  # 记录发送次数
            while True:

                while True:

                    dataFromCar1_ID4 = client_car_ID4.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        z1 = struct.unpack('B', dataFromCar1_ID4)
                    except:
                        print("解析包头错误")
                    if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                        dataFromCar2_ID4 = client_car_ID4.recv(3)
                        break

                dataFromCar3_ID4 = client_car_ID4.recv(24)
                try:
                    x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar3_ID4)
                except:
                    print("解析前缀信息错误")

                if (x9 == 3):  # 如果上传数据字节数过多，则为图像信息
                    print("上传的是图像数据")

                    def ImageRead(client_car_ID4):
                        data_image1 = client_car_ID4.recv(1)
                        try:
                            image_geshi = struct.unpack('B', data_image1)
                        except:
                            print("解析图像格式错误")
                        # print("图像格式为：", image_geshi)
                        data_image2 = client_car_ID4.recv(4)
                        try:
                            image_len = struct.unpack('1I', data_image2)
                        except:
                            print("解析图像字节数错误")
                        # print("图像字节数：", image_len)
                        image_msg = b''
                        len1 = int(image_len[0])
                        image_length = len1  # 图像数据的字节长度
                        readlength = 0  # 从缓冲区读取的字节数
                        while (len1 > 0):
                            if len1 > 1024:  # 如果剩余图像字节数大于1024
                                buffer = client_car_ID4.recv(1024,
                                                             socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                len1 = len1 - 1024
                                readlength += 1024
                            else:
                                buffer = client_car_ID4.recv(len1, socket.MSG_WAITALL)
                                image_msg += buffer
                                readlength += len1
                                break

                        print("从缓冲区读取的字节数为：", readlength)
                        print("缓冲区剩余图像数据块字节数为：", image_length - readlength)

                        # tianchong_num = image_length % 4  # 计算填充的字节数
                        # shengyu_num = tianchong_num + 16  # 剩下要读的字节数
                        # data_image_shengyu  = client_car.recv(shengyu_num)
                        # print("读完图像数据块后余下的字节数为，检测是否读到包尾，验证帧信息里的数据块字节数是否正确", data_image_shengyu)

                        # 循环读取余下的字节，直到读完四个字节的包尾
                        left = client_car_ID4.recv(1)
                        buffer_left = b''
                        while 1:
                            try:
                                left_baowei = struct.unpack('B', left)
                                print("检测包尾读到的数据为", left_baowei)
                            except:
                                print("检测包尾第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                            if (left_baowei != (204,)):  # 如果读到包尾则一次性读完包尾
                                buffer_left += left
                                left = client_car_ID4.recv(1)
                            else:
                                buffer_left += left
                                left_2 = client_car_ID4.recv(3)
                                buffer_left += left_2
                                print("读完四个包尾")
                                break

                        # data_from_car_image_ID1 =dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg +data_image_shengyu
                        data_from_car_image_ID4 = dataFromCar1_ID4 + dataFromCar2_ID4 + dataFromCar3_ID4 + data_image1 + data_image2 + image_msg + buffer_left
                        log7 = "ID4 收到下位机上传的图像数据"
                        writelog(log7)  # 写入事件

                        send_to_up(data_from_car_image_ID4)  # 将图像数据转发
                        log8 = "ID4 将下位机上传的图像数据发送给上位机"
                        writelog(log8)  # 写入事件

                    t_image_ID4 = threading.Thread(target=ImageRead, args=(client_car_ID4,))
                    t_image_ID4.start()


                elif (x9 == 0):
                    print("上传的是无效数据")

                elif (x9 == 1):
                    print("上传的是状态数据")
                    dataFromCar_state = client_car_ID4.recv(40)
                    data_from_car_state_ID4 = dataFromCar1_ID4 + dataFromCar2_ID4 + dataFromCar3_ID4 + dataFromCar_state
                    log9 = "ID4 收到下位机上传的状态数据"
                    writelog(log9)  # 写入事件

                    send_to_up_ID4(data_from_car_state_ID4)
                    log10 = "ID4 将下位机上传的状态数据发送给上位机"
                    writelog(log10)  # 写入事件


                elif (x9 == 2):
                    print("上传的是经纬度数据")
                    dataFromCar_lnglat = client_car_ID4.recv(36)
                    data_from_car_lnglat_ID4 = dataFromCar1_ID4 + dataFromCar2_ID4 + dataFromCar3_ID4 + dataFromCar_lnglat
                    log11 = "ID4 收到下位机上传的小车当前时刻经纬度数据"
                    writelog(log11)  # 写入事件

                    send_to_up_ID4(data_from_car_lnglat_ID4)
                    log12 = "ID4 将下位机上传的小车当前时刻经纬度数据发送给上位机"
                    writelog(log12)  # 写入事件


                else:
                    print("数据上发错误")
                    # break

        # =======================================定义数据发送函数===============================

    def send_to_up_ID4(data_from_car):
        # print("发送给上位机的数据为：", data_from_car)
        global tcp_server_up
        global client_up_ID4
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_up = "1111111"
            # client_up.send(data_to_up.encode("utf-8"))  # 向下位机发送数据包
            client_up_ID4.send(data_from_car)  # 向下位机发送数据包
            break

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# 车辆五：
#  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_up_ID5():
        global client_up_ID5
        print("从上位机接收数据为：")
        tcp_server_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_up.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
        ip_Ali = "47.102.36.187"  # 服务器的ip地址
        tcp_server_up.bind(("0", 8090))
        tcp_server_up.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            client_up_ID5, cltadd_up = tcp_server_up.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            i = 0  # 记录发送次数

            while True:
                # data_from_up = client_up.recv(1024).decode('utf-8')  # 接收客户端发送的数据进行解码
                # data_from_up = client_up.recv(1024)  # 接收客户端发送的数据进行解码

                # =================写入log文档
                # 1、解码如果判为上位机上发的经纬度数据，则写入文档：time: 上位机上发经纬度数据
                # 2、解码如果判为上位机上发的请求状态数据的指令，则写入文档：time: 上位机上发请求状态数据的指令
                # 3、解码如果判为上位机上发的请求图像数据的指令，则写入文档：time: 上位机上发请求图像数据的指令
                # 4、分三种情况写send_to_car,每种情况后写入文档：time: 向下位机发送......
                while True:

                    data_from_up1 = client_up_ID5.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        m1 = struct.unpack('B', data_from_up1)
                    except:
                        print("解析包头错误")
                    if (m1 == (255,)):  # 如果读到包头则一次性读完包头
                        data_from_up2 = client_up_ID5.recv(3)
                        break

                data_from_up3 = client_up_ID5.recv(20)
                try:
                    x5, x6, x7, x8, x9 = struct.unpack('5i', data_from_up3)  # x5:包长x6：包序号 x7:时间戳 x8:数据域1 x9:数据域2
                except:
                    print("解析前缀信息错误")

                if (x8 == 1):
                    # 上位机下发经纬度数据
                    data_from_up_lnglat = client_up_ID5.recv(1024)
                    log1 = "ID5 收到上位机要传给下位机的未来经纬度序列"
                    writelog(log1)  # 写入事件

                    data_from_up_Lnglat_ID5 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_lnglat
                    send_to_car_ID5(data_from_up_Lnglat_ID5)  # 将数据转发
                    log2 = "ID5 将上位机发送的未来经纬度序列传输给下位机"
                    writelog(log2)
                    print("成功转发经纬度给小车")

                if (x8 == 2):
                    # 请求上发状态数据
                    data_from_up_state = client_up_ID5.recv(1024)
                    log3 = "ID5 收到上位机要传给下位机的请求状态指令"
                    writelog(log3)  # 写入事件

                    data_from_up_State_ID5 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_state
                    send_to_car_ID5(data_from_up_State_ID5)  # 将数据转发
                    log4 = "ID5 将上位机发送的请求状态指令传输给下位机"
                    writelog(log4)
                    print("成功转发状态请求指令给小车")

                if (x8 == 3):
                    # 请求上发图像数据
                    data_from_up_image = client_up_ID5.recv(1024)
                    log5 = "ID5 收到上位机要传给下位机的请求图像指令"
                    writelog(log5)  # 写入事件

                    data_from_up_Image_ID5 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_image
                    send_to_car_ID5(data_from_up_Image_ID5)  # 将数据转发
                    log6 = "ID5 将上位机发送的请求图像指令传输给下位机"
                    writelog(log6)
                    print("成功转发图像请求指令给小车")

                # =================写入log文档

                # print("客户端发送的数据是：", data_from_up)
                # # if data:  # 如果收到的数据不为空，表示客户端仍在请求服务，继续为其服务
                # if data_from_up:
                #     send_to_car_ID5(data_from_up)  # 将数据转发
                #     print("成功转发给小车")
                #     # break
                # else:
                #     break
        # =======================================定义数据发送函数======================================

    def send_to_car_ID5(data_from_up):
        # print("发送给小车的数据为：", data_from_up)
        global client_car_ID5
        flag = True
        # -----------------------------------------------------------------------------------------------
        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_car = "2222222"
            client_car_ID5.send(data_from_up)  # 向下位机发送数据包
            break

        #  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_car_ID5():
        global ip_Ali
        global port_car  # 与小车接通的端口
        global tcp_server_car
        global client_car_ID5
        print("从小车接收数据为：")

        tcp_server_car = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_car.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

        # ip_Ali = input("请输入阿里云的公网ip")  # 服务器的ip地址
        # port_car = input("请输入与小车联通的端口:")  # 服务器的端口号
        port_car = 8083  # 与小车接通的端口号
        tcp_server_car.bind(("0", 8091))
        tcp_server_car.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            # flag = True
            client_car_ID5, cltadd_car = tcp_server_car.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            # while True:
            i = 0  # 记录发送次数
            while True:

                while True:

                    dataFromCar1 = client_car_ID5.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        z1 = struct.unpack('B', dataFromCar1)
                    except:
                        print("解析包头错误")
                    if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                        dataFromCar2 = client_car_ID5.recv(3)
                        break

                dataFromCar3 = client_car_ID5.recv(24)
                try:
                    x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar3)
                except:
                    print("解析前缀信息错误")

                if (x9 == 3):  # 如果上传数据字节数过多，则为图像信息
                    print("上传的是图像数据")

                    def ImageRead(client_car_ID5):
                        data_image1 = client_car_ID5.recv(1)
                        try:
                            image_geshi = struct.unpack('B', data_image1)
                        except:
                            print("解析图像格式错误")
                        # print("图像格式为：", image_geshi)
                        data_image2 = client_car_ID5.recv(4)
                        try:
                            image_len = struct.unpack('1I', data_image2)
                        except:
                            print("解析图像字节数错误")
                        # print("图像字节数：", image_len)
                        image_msg = b''
                        len1 = int(image_len[0])
                        image_length = len1  # 图像数据的字节长度
                        readlength = 0  # 从缓冲区读取的字节数
                        while (len1 > 0):
                            if len1 > 1024:  # 如果剩余图像字节数大于1024
                                buffer = client_car_ID5.recv(1024,
                                                             socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                len1 = len1 - 1024
                                readlength += 1024
                            else:
                                buffer = client_car_ID5.recv(len1, socket.MSG_WAITALL)
                                image_msg += buffer
                                readlength += len1
                                break

                        print("从缓冲区读取的字节数为：", readlength)
                        print("缓冲区剩余图像数据块字节数为：", image_length - readlength)

                        # tianchong_num = image_length % 4  # 计算填充的字节数
                        # shengyu_num = tianchong_num + 16  # 剩下要读的字节数
                        # data_image_shengyu  = client_car.recv(shengyu_num)
                        # print("读完图像数据块后余下的字节数为，检测是否读到包尾，验证帧信息里的数据块字节数是否正确", data_image_shengyu)

                        # 循环读取余下的字节，直到读完四个字节的包尾
                        left = client_car_ID5.recv(1)
                        buffer_left = b''
                        while 1:
                            try:
                                left_baowei = struct.unpack('B', left)
                                print("检测包尾读到的数据为", left_baowei)
                            except:
                                print("检测包尾第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                            if (left_baowei != (204,)):  # 如果读到包尾则一次性读完包尾
                                buffer_left += left
                                left = client_car_ID5.recv(1)
                            else:
                                buffer_left += left
                                left_2 = client_car_ID5.recv(3)
                                buffer_left += left_2
                                print("读完四个包尾")
                                break

                        # data_from_car_image_ID1 =dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg +data_image_shengyu
                        data_from_car_image_ID5 = dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg + buffer_left
                        log7 = "ID5 收到下位机上传的图像数据"
                        writelog(log7)  # 写入事件

                        send_to_up(data_from_car_image_ID5)  # 将图像数据转发
                        log8 = "ID5 将下位机上传的图像数据发送给上位机"
                        writelog(log8)  # 写入事件

                    t_image_ID5 = threading.Thread(target=ImageRead, args=(client_car_ID5,))
                    t_image_ID5.start()



                elif (x9 == 0):
                    print("上传的是无效数据")

                elif (x9 == 1):
                    print("上传的是状态数据")
                    dataFromCar_state = client_car_ID5.recv(40)
                    data_from_car_state_ID5 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_state
                    log9 = "ID5 收到下位机上传的状态数据"
                    writelog(log9)  # 写入事件

                    send_to_up_ID5(data_from_car_state_ID5)
                    log10 = "ID5 将下位机上传的状态数据发送给上位机"
                    writelog(log10)  # 写入事件


                elif (x9 == 2):
                    print("上传的是经纬度数据")
                    dataFromCar_lnglat = client_car_ID5.recv(36)
                    data_from_car_lnglat_ID5 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_lnglat
                    log11 = "ID5 收到下位机上传的小车当前时刻经纬度数据"
                    writelog(log11)  # 写入事件

                    send_to_up_ID5(data_from_car_lnglat_ID5)
                    log12 = "ID5 将下位机上传的小车当前时刻经纬度数据发送给上位机"
                    writelog(log12)  # 写入事件


                else:
                    print("数据上发错误")
                    # break

        # =======================================定义数据发送函数===============================

    def send_to_up_ID5(data_from_car):
        # print("发送给上位机的数据为：", data_from_car)
        global tcp_server_up
        global client_up_ID5
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_up = "1111111"
            # client_up.send(data_to_up.encode("utf-8"))  # 向下位机发送数据包
            client_up_ID5.send(data_from_car)  # 向下位机发送数据包
            break

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# 车辆六：
#  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_up_ID6():
        global client_up_ID6
        print("从上位机接收数据为：")
        tcp_server_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_up.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
        ip_Ali = "47.102.36.187"  # 服务器的ip地址
        tcp_server_up.bind(("0", 8092))
        tcp_server_up.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            client_up_ID6, cltadd_up = tcp_server_up.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            i = 0  # 记录发送次数

            while True:
                # data_from_up = client_up.recv(1024).decode('utf-8')  # 接收客户端发送的数据进行解码
                # data_from_up = client_up.recv(1024)  # 接收客户端发送的数据进行解码

                # =================写入log文档
                # 1、解码如果判为上位机上发的经纬度数据，则写入文档：time: 上位机上发经纬度数据
                # 2、解码如果判为上位机上发的请求状态数据的指令，则写入文档：time: 上位机上发请求状态数据的指令
                # 3、解码如果判为上位机上发的请求图像数据的指令，则写入文档：time: 上位机上发请求图像数据的指令
                # 4、分三种情况写send_to_car,每种情况后写入文档：time: 向下位机发送......
                while True:

                    data_from_up1 = client_up_ID6.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        m1 = struct.unpack('B', data_from_up1)
                    except:
                        print("解析包头错误")
                    if (m1 == (255,)):  # 如果读到包头则一次性读完包头
                        data_from_up2 = client_up_ID6.recv(3)
                        break

                data_from_up3 = client_up_ID6.recv(20)
                try:
                    x5, x6, x7, x8, x9 = struct.unpack('5i', data_from_up3)  # x5:包长x6：包序号 x7:时间戳 x8:数据域1 x9:数据域2
                except:
                    print("解析前缀信息错误")

                if (x8 == 1):
                    # 上位机下发经纬度数据
                    data_from_up_lnglat = client_up_ID6.recv(1024)
                    log1 = "ID6 收到上位机要传给下位机的未来经纬度序列"
                    writelog(log1)  # 写入事件

                    data_from_up_Lnglat_ID6 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_lnglat
                    send_to_car_ID6(data_from_up_Lnglat_ID6)  # 将数据转发
                    log2 = "ID6 将上位机发送的未来经纬度序列传输给下位机"
                    writelog(log2)
                    print("成功转发经纬度给小车")

                if (x8 == 2):
                    # 请求上发状态数据
                    data_from_up_state = client_up_ID6.recv(1024)
                    log3 = "ID6 收到上位机要传给下位机的请求状态指令"
                    writelog(log3)  # 写入事件

                    data_from_up_State_ID6 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_state
                    send_to_car_ID6(data_from_up_State_ID6)  # 将数据转发
                    log4 = "ID6 将上位机发送的请求状态指令传输给下位机"
                    writelog(log4)
                    print("成功转发状态请求指令给小车")

                if (x8 == 3):
                    # 请求上发图像数据
                    data_from_up_image = client_up_ID6.recv(1024)
                    log5 = "ID6 收到上位机要传给下位机的请求图像指令"
                    writelog(log5)  # 写入事件

                    data_from_up_Image_ID6 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_image
                    send_to_car_ID6(data_from_up_Image_ID6)  # 将数据转发
                    log6 = "ID6 将上位机发送的请求图像指令传输给下位机"
                    writelog(log6)
                    print("成功转发图像请求指令给小车")

                # =================写入log文档

                # print("客户端发送的数据是：", data_from_up)
                # # if data:  # 如果收到的数据不为空，表示客户端仍在请求服务，继续为其服务
                # if data_from_up:
                #     send_to_car_ID6(data_from_up)  # 将数据转发
                #     print("成功转发给小车")
                #     # break
                # else:
                #     break
        # =======================================定义数据发送函数======================================

    def send_to_car_ID6(data_from_up):
        # print("发送给小车的数据为：", data_from_up)
        global client_car_ID6
        flag = True
        # -----------------------------------------------------------------------------------------------
        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_car = "2222222"
            client_car_ID6.send(data_from_up)  # 向下位机发送数据包
            break

        #  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_car_ID6():
        global ip_Ali
        global port_car  # 与小车接通的端口
        global tcp_server_car
        global client_car_ID6
        print("从小车接收数据为：")

        tcp_server_car = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_car.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

        # ip_Ali = input("请输入阿里云的公网ip")  # 服务器的ip地址
        # port_car = input("请输入与小车联通的端口:")  # 服务器的端口号
        port_car = 8083  # 与小车接通的端口号
        tcp_server_car.bind(("0", 8093))
        tcp_server_car.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            # flag = True
            client_car_ID6, cltadd_car = tcp_server_car.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            # while True:
            i = 0  # 记录发送次数
            while True:

                while True:

                    dataFromCar1 = client_car_ID6.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        z1 = struct.unpack('B', dataFromCar1)
                    except:
                        print("解析包头错误")
                    if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                        dataFromCar2 = client_car_ID6.recv(3)
                        break

                dataFromCar3 = client_car_ID6.recv(24)
                try:
                    x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar3)
                except:
                    print("解析前缀信息错误")

                if (x9 == 3):  # 如果上传数据字节数过多，则为图像信息
                    print("上传的是图像数据")

                    def ImageRead(client_car_ID6):
                        data_image1 = client_car_ID6.recv(1)
                        try:
                            image_geshi = struct.unpack('B', data_image1)
                        except:
                            print("解析图像格式错误")
                        # print("图像格式为：", image_geshi)
                        data_image2 = client_car_ID6.recv(4)
                        try:
                            image_len = struct.unpack('1I', data_image2)
                        except:
                            print("解析图像字节数错误")
                        # print("图像字节数：", image_len)
                        image_msg = b''
                        len1 = int(image_len[0])
                        image_length = len1  # 图像数据的字节长度
                        readlength = 0  # 从缓冲区读取的字节数
                        while (len1 > 0):
                            if len1 > 1024:  # 如果剩余图像字节数大于1024
                                buffer = client_car_ID6.recv(1024,
                                                             socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                len1 = len1 - 1024
                                readlength += 1024
                            else:
                                buffer = client_car_ID6.recv(len1, socket.MSG_WAITALL)
                                image_msg += buffer
                                readlength += len1
                                break

                        print("从缓冲区读取的字节数为：", readlength)
                        print("缓冲区剩余图像数据块字节数为：", image_length - readlength)

                        # tianchong_num = image_length % 4  # 计算填充的字节数
                        # shengyu_num = tianchong_num + 16  # 剩下要读的字节数
                        # data_image_shengyu  = client_car.recv(shengyu_num)
                        # print("读完图像数据块后余下的字节数为，检测是否读到包尾，验证帧信息里的数据块字节数是否正确", data_image_shengyu)

                        # 循环读取余下的字节，直到读完四个字节的包尾
                        left = client_car_ID6.recv(1)
                        buffer_left = b''
                        while 1:
                            try:
                                left_baowei = struct.unpack('B', left)
                                print("检测包尾读到的数据为", left_baowei)
                            except:
                                print("检测包尾第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                            if (left_baowei != (204,)):  # 如果读到包尾则一次性读完包尾
                                buffer_left += left
                                left = client_car_ID6.recv(1)
                            else:
                                buffer_left += left
                                left_2 = client_car_ID6.recv(3)
                                buffer_left += left_2
                                print("读完四个包尾")
                                break

                        # data_from_car_image_ID1 =dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg +data_image_shengyu
                        data_from_car_image_ID6 = dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg + buffer_left
                        log7 = "ID6 收到下位机上传的图像数据"
                        writelog(log7)  # 写入事件

                        send_to_up(data_from_car_image_ID6)  # 将图像数据转发
                        log8 = "ID6 将下位机上传的图像数据发送给上位机"
                        writelog(log8)  # 写入事件

                    t_image_ID6 = threading.Thread(target=ImageRead, args=(client_car_ID6,))
                    t_image_ID6.start()


                elif (x9 == 0):
                    print("上传的是无效数据")

                elif (x9 == 1):
                    print("上传的是状态数据")
                    dataFromCar_state = client_car_ID6.recv(40)
                    data_from_car_state_ID6 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_state
                    log9 = "ID6 收到下位机上传的状态数据"
                    writelog(log9)  # 写入事件

                    send_to_up_ID6(data_from_car_state_ID6)
                    log10 = "ID6 将下位机上传的状态数据发送给上位机"
                    writelog(log10)  # 写入事件


                elif (x9 == 2):
                    print("上传的是经纬度数据")
                    dataFromCar_lnglat = client_car_ID6.recv(36)
                    data_from_car_lnglat_ID6 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_lnglat
                    log11 = "ID6 收到下位机上传的小车当前时刻经纬度数据"
                    writelog(log11)  # 写入事件

                    send_to_up_ID6(data_from_car_lnglat_ID6)
                    log12 = "ID6 将下位机上传的小车当前时刻经纬度数据发送给上位机"
                    writelog(log12)  # 写入事件


                else:
                    print("数据上发错误")
                    # break

        # =======================================定义数据发送函数===============================

    def send_to_up_ID6(data_from_car):
        # print("发送给上位机的数据为：", data_from_car)
        global tcp_server_up
        global client_up_ID6
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_up = "1111111"
            # client_up.send(data_to_up.encode("utf-8"))  # 向下位机发送数据包
            client_up_ID6.send(data_from_car)  # 向下位机发送数据包
            break

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# 车辆七：
#  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_up_ID7():
        global client_up_ID7
        print("从上位机接收数据为：")
        tcp_server_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_up.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
        ip_Ali = "47.102.36.187"  # 服务器的ip地址
        tcp_server_up.bind(("0", 8094))
        tcp_server_up.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            client_up_ID7, cltadd_up = tcp_server_up.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            i = 0  # 记录发送次数

            while True:
                # data_from_up = client_up.recv(1024).decode('utf-8')  # 接收客户端发送的数据进行解码
                # data_from_up = client_up.recv(1024)  # 接收客户端发送的数据进行解码

                # =================写入log文档
                # 1、解码如果判为上位机上发的经纬度数据，则写入文档：time: 上位机上发经纬度数据
                # 2、解码如果判为上位机上发的请求状态数据的指令，则写入文档：time: 上位机上发请求状态数据的指令
                # 3、解码如果判为上位机上发的请求图像数据的指令，则写入文档：time: 上位机上发请求图像数据的指令
                # 4、分三种情况写send_to_car,每种情况后写入文档：time: 向下位机发送......
                while True:

                    data_from_up1 = client_up_ID7.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        m1 = struct.unpack('B', data_from_up1)
                    except:
                        print("解析包头错误")
                    if (m1 == (255,)):  # 如果读到包头则一次性读完包头
                        data_from_up2 = client_up_ID7.recv(3)
                        break

                data_from_up3 = client_up_ID7.recv(20)
                try:
                    x5, x6, x7, x8, x9 = struct.unpack('5i', data_from_up3)  # x5:包长x6：包序号 x7:时间戳 x8:数据域1 x9:数据域2
                except:
                    print("解析前缀信息错误")

                if (x8 == 1):
                    # 上位机下发经纬度数据
                    data_from_up_lnglat = client_up_ID7.recv(1024)
                    log1 = "ID7 收到上位机要传给下位机的未来经纬度序列"
                    writelog(log1)  # 写入事件

                    data_from_up_Lnglat_ID7 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_lnglat
                    send_to_car_ID7(data_from_up_Lnglat_ID7)  # 将数据转发
                    log2 = "ID7 将上位机发送的未来经纬度序列传输给下位机"
                    writelog(log2)
                    print("成功转发经纬度给小车")

                if (x8 == 2):
                    # 请求上发状态数据
                    data_from_up_state = client_up_ID7.recv(1024)
                    log3 = "ID7 收到上位机要传给下位机的请求状态指令"
                    writelog(log3)  # 写入事件

                    data_from_up_State_ID7 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_state
                    send_to_car_ID7(data_from_up_State_ID7)  # 将数据转发
                    log4 = "ID7 将上位机发送的请求状态指令传输给下位机"
                    writelog(log4)
                    print("成功转发状态请求指令给小车")

                if (x8 == 3):
                    # 请求上发图像数据
                    data_from_up_image = client_up_ID7.recv(1024)
                    log5 = "ID7 收到上位机要传给下位机的请求图像指令"
                    writelog(log5)  # 写入事件

                    data_from_up_Image_ID7 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_image
                    send_to_car_ID7(data_from_up_Image_ID7)  # 将数据转发
                    log6 = "ID7 将上位机发送的请求图像指令传输给下位机"
                    writelog(log6)
                    print("成功转发图像请求指令给小车")

                # =================写入log文档

                # print("客户端发送的数据是：", data_from_up)
                # # if data:  # 如果收到的数据不为空，表示客户端仍在请求服务，继续为其服务
                # if data_from_up:
                #     send_to_car_ID7(data_from_up)  # 将数据转发
                #     print("成功转发给小车")
                #     # break
                # else:
                #     break
        # =======================================定义数据发送函数======================================

    def send_to_car_ID7(data_from_up):
        # print("发送给小车的数据为：", data_from_up)
        global client_car_ID7
        flag = True
        # -----------------------------------------------------------------------------------------------
        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_car = "2222222"
            client_car_ID7.send(data_from_up)  # 向下位机发送数据包
            break

        #  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_car_ID7():
        global ip_Ali
        global port_car  # 与小车接通的端口
        global tcp_server_car
        global client_car_ID7
        print("从小车接收数据为：")

        tcp_server_car = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_car.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

        # ip_Ali = input("请输入阿里云的公网ip")  # 服务器的ip地址
        # port_car = input("请输入与小车联通的端口:")  # 服务器的端口号
        port_car = 8083  # 与小车接通的端口号
        tcp_server_car.bind(("0", 8095))
        tcp_server_car.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            # flag = True
            client_car_ID7, cltadd_car = tcp_server_car.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            # while True:
            i = 0  # 记录发送次数
            while True:

                while True:

                    dataFromCar1 = client_car_ID7.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        z1 = struct.unpack('B', dataFromCar1)
                    except:
                        print("解析包头错误")
                    if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                        dataFromCar2 = client_car_ID7.recv(3)
                        break

                dataFromCar3 = client_car_ID7.recv(24)
                try:
                    x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar3)
                except:
                    print("解析前缀信息错误")

                if (x9 == 3):  # 如果上传数据字节数过多，则为图像信息
                    print("上传的是图像数据")

                    def ImageRead(client_car_ID7):
                        data_image1 = client_car_ID7.recv(1)
                        try:
                            image_geshi = struct.unpack('B', data_image1)
                        except:
                            print("解析图像格式错误")
                        # print("图像格式为：", image_geshi)
                        data_image2 = client_car_ID7.recv(4)
                        try:
                            image_len = struct.unpack('1I', data_image2)
                        except:
                            print("解析图像字节数错误")
                        # print("图像字节数：", image_len)
                        image_msg = b''
                        len1 = int(image_len[0])
                        image_length = len1  # 图像数据的字节长度
                        readlength = 0  # 从缓冲区读取的字节数
                        while (len1 > 0):
                            if len1 > 1024:  # 如果剩余图像字节数大于1024
                                buffer = client_car_ID7.recv(1024,
                                                             socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                len1 = len1 - 1024
                                readlength += 1024
                            else:
                                buffer = client_car_ID7.recv(len1, socket.MSG_WAITALL)
                                image_msg += buffer
                                readlength += len1
                                break

                        print("从缓冲区读取的字节数为：", readlength)
                        print("缓冲区剩余图像数据块字节数为：", image_length - readlength)

                        # tianchong_num = image_length % 4  # 计算填充的字节数
                        # shengyu_num = tianchong_num + 16  # 剩下要读的字节数
                        # data_image_shengyu  = client_car.recv(shengyu_num)
                        # print("读完图像数据块后余下的字节数为，检测是否读到包尾，验证帧信息里的数据块字节数是否正确", data_image_shengyu)

                        # 循环读取余下的字节，直到读完四个字节的包尾
                        left = client_car_ID7.recv(1)
                        buffer_left = b''
                        while 1:
                            try:
                                left_baowei = struct.unpack('B', left)
                                print("检测包尾读到的数据为", left_baowei)
                            except:
                                print("检测包尾第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                            if (left_baowei != (204,)):  # 如果读到包尾则一次性读完包尾
                                buffer_left += left
                                left = client_car_ID7.recv(1)
                            else:
                                buffer_left += left
                                left_2 = client_car_ID7.recv(3)
                                buffer_left += left_2
                                print("读完四个包尾")
                                break

                        # data_from_car_image_ID1 =dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg +data_image_shengyu
                        data_from_car_image_ID7 = dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg + buffer_left
                        log7 = "ID7 收到下位机上传的图像数据"
                        writelog(log7)  # 写入事件

                        send_to_up(data_from_car_image_ID7)  # 将图像数据转发
                        log8 = "ID7 将下位机上传的图像数据发送给上位机"
                        writelog(log8)  # 写入事件

                    t_image_ID7 = threading.Thread(target=ImageRead, args=(client_car_ID7,))
                    t_image_ID7.start()


                elif (x9 == 0):
                    print("上传的是无效数据")

                elif (x9 == 1):
                    print("上传的是状态数据")
                    dataFromCar_state = client_car_ID7.recv(40)
                    data_from_car_state_ID7 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_state
                    log9 = "ID7 收到下位机上传的状态数据"
                    writelog(log9)  # 写入事件

                    send_to_up_ID7(data_from_car_state_ID7)
                    log10 = "ID7 将下位机上传的状态数据发送给上位机"
                    writelog(log10)  # 写入事件


                elif (x9 == 2):
                    print("上传的是经纬度数据")
                    dataFromCar_lnglat = client_car_ID7.recv(36)
                    data_from_car_lnglat_ID7 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_lnglat
                    log11 = "ID7 收到下位机上传的小车当前时刻经纬度数据"
                    writelog(log11)  # 写入事件

                    send_to_up_ID7(data_from_car_lnglat_ID7)
                    log12 = "ID7 将下位机上传的小车当前时刻经纬度数据发送给上位机"
                    writelog(log12)  # 写入事件


                else:
                    print("数据上发错误")
                    # break

        # =======================================定义数据发送函数===============================

    def send_to_up_ID7(data_from_car):
        # print("发送给上位机的数据为：", data_from_car)
        global tcp_server_up
        global client_up_ID7
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_up = "1111111"
            # client_up.send(data_to_up.encode("utf-8"))  # 向下位机发送数据包
            client_up_ID7.send(data_from_car)  # 向下位机发送数据包
            break

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# 车辆八：
#  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_up_ID8():
        global client_up_ID8
        print("从上位机接收数据为：")
        tcp_server_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_up.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
        ip_Ali = "47.102.36.187"  # 服务器的ip地址
        tcp_server_up.bind(("0", 8096))
        tcp_server_up.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            client_up_ID8, cltadd_up = tcp_server_up.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            i = 0  # 记录发送次数

            while True:
                # data_from_up = client_up.recv(1024).decode('utf-8')  # 接收客户端发送的数据进行解码
                # data_from_up = client_up.recv(1024)  # 接收客户端发送的数据进行解码

                # =================写入log文档
                # 1、解码如果判为上位机上发的经纬度数据，则写入文档：time: 上位机上发经纬度数据
                # 2、解码如果判为上位机上发的请求状态数据的指令，则写入文档：time: 上位机上发请求状态数据的指令
                # 3、解码如果判为上位机上发的请求图像数据的指令，则写入文档：time: 上位机上发请求图像数据的指令
                # 4、分三种情况写send_to_car,每种情况后写入文档：time: 向下位机发送......
                while True:

                    data_from_up1 = client_up_ID8.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        m1 = struct.unpack('B', data_from_up1)
                    except:
                        print("解析包头错误")
                    if (m1 == (255,)):  # 如果读到包头则一次性读完包头
                        data_from_up2 = client_up_ID8.recv(3)
                        break

                data_from_up3 = client_up_ID8.recv(20)
                try:
                    x5, x6, x7, x8, x9 = struct.unpack('5i', data_from_up3)  # x5:包长x6：包序号 x7:时间戳 x8:数据域1 x9:数据域2
                except:
                    print("解析前缀信息错误")

                if (x8 == 1):
                    # 上位机下发经纬度数据
                    data_from_up_lnglat = client_up_ID8.recv(1024)
                    log1 = "ID8 收到上位机要传给下位机的未来经纬度序列"
                    writelog(log1)  # 写入事件

                    data_from_up_Lnglat_ID8 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_lnglat
                    send_to_car_ID8(data_from_up_Lnglat_ID8)  # 将数据转发
                    log2 = "ID8 将上位机发送的未来经纬度序列传输给下位机"
                    writelog(log2)
                    print("成功转发经纬度给小车")

                if (x8 == 2):
                    # 请求上发状态数据
                    data_from_up_state = client_up_ID8.recv(1024)
                    log3 = "ID8 收到上位机要传给下位机的请求状态指令"
                    writelog(log3)  # 写入事件

                    data_from_up_State_ID8 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_state
                    send_to_car_ID8(data_from_up_State_ID8)  # 将数据转发
                    log4 = "ID8 将上位机发送的请求状态指令传输给下位机"
                    writelog(log4)
                    print("成功转发状态请求指令给小车")

                if (x8 == 3):
                    # 请求上发图像数据
                    data_from_up_image = client_up_ID8.recv(1024)
                    log5 = "ID8 收到上位机要传给下位机的请求图像指令"
                    writelog(log5)  # 写入事件

                    data_from_up_Image_ID8 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_image
                    send_to_car_ID8(data_from_up_Image_ID8)  # 将数据转发
                    log6 = "ID8 将上位机发送的请求图像指令传输给下位机"
                    writelog(log6)
                    print("成功转发图像请求指令给小车")

                # =================写入log文档

                # print("客户端发送的数据是：", data_from_up)
                # # if data:  # 如果收到的数据不为空，表示客户端仍在请求服务，继续为其服务
                # if data_from_up:
                #     send_to_car_ID8(data_from_up)  # 将数据转发
                #     print("成功转发给小车")
                #     # break
                # else:
                #     break
        # =======================================定义数据发送函数======================================

    def send_to_car_ID8(data_from_up):
        # print("发送给小车的数据为：", data_from_up)
        global client_car_ID8
        flag = True
        # -----------------------------------------------------------------------------------------------
        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_car = "2222222"
            client_car_ID8.send(data_from_up)  # 向下位机发送数据包
            break

        #  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_car_ID8():
        global ip_Ali
        global port_car  # 与小车接通的端口
        global tcp_server_car
        global client_car_ID8
        print("从小车接收数据为：")

        tcp_server_car = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_car.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

        # ip_Ali = input("请输入阿里云的公网ip")  # 服务器的ip地址
        # port_car = input("请输入与小车联通的端口:")  # 服务器的端口号
        port_car = 8083  # 与小车接通的端口号
        tcp_server_car.bind(("0", 8097))
        tcp_server_car.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            # flag = True
            client_car_ID8, cltadd_car = tcp_server_car.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            # while True:
            i = 0  # 记录发送次数
            while True:

                while True:

                    dataFromCar1 = client_car_ID8.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        z1 = struct.unpack('B', dataFromCar1)
                    except:
                        print("解析包头错误")
                    if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                        dataFromCar2 = client_car_ID8.recv(3)
                        break

                dataFromCar3 = client_car_ID8.recv(24)
                try:
                    x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar3)
                except:
                    print("解析前缀信息错误")

                if (x9 == 3):  # 如果上传数据字节数过多，则为图像信息
                    print("上传的是图像数据")

                    def ImageRead(client_car_ID8):
                        data_image1 = client_car_ID8.recv(1)
                        try:
                            image_geshi = struct.unpack('B', data_image1)
                        except:
                            print("解析图像格式错误")
                        # print("图像格式为：", image_geshi)
                        data_image2 = client_car_ID8.recv(4)
                        try:
                            image_len = struct.unpack('1I', data_image2)
                        except:
                            print("解析图像字节数错误")
                        # print("图像字节数：", image_len)
                        image_msg = b''
                        len1 = int(image_len[0])
                        image_length = len1  # 图像数据的字节长度
                        readlength = 0  # 从缓冲区读取的字节数
                        while (len1 > 0):
                            if len1 > 1024:  # 如果剩余图像字节数大于1024
                                buffer = client_car_ID8.recv(1024,
                                                             socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                len1 = len1 - 1024
                                readlength += 1024
                            else:
                                buffer = client_car_ID8.recv(len1, socket.MSG_WAITALL)
                                image_msg += buffer
                                readlength += len1
                                break

                        print("从缓冲区读取的字节数为：", readlength)
                        print("缓冲区剩余图像数据块字节数为：", image_length - readlength)

                        # tianchong_num = image_length % 4  # 计算填充的字节数
                        # shengyu_num = tianchong_num + 16  # 剩下要读的字节数
                        # data_image_shengyu  = client_car.recv(shengyu_num)
                        # print("读完图像数据块后余下的字节数为，检测是否读到包尾，验证帧信息里的数据块字节数是否正确", data_image_shengyu)

                        # 循环读取余下的字节，直到读完四个字节的包尾
                        left = client_car_ID8.recv(1)
                        buffer_left = b''
                        while 1:
                            try:
                                left_baowei = struct.unpack('B', left)
                                print("检测包尾读到的数据为", left_baowei)
                            except:
                                print("检测包尾第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                            if (left_baowei != (204,)):  # 如果读到包尾则一次性读完包尾
                                buffer_left += left
                                left = client_car_ID8.recv(1)
                            else:
                                buffer_left += left
                                left_2 = client_car_ID8.recv(3)
                                buffer_left += left_2
                                print("读完四个包尾")
                                break

                        # data_from_car_image_ID1 =dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg +data_image_shengyu
                        data_from_car_image_ID8 = dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg + buffer_left
                        log7 = "ID8 收到下位机上传的图像数据"
                        writelog(log7)  # 写入事件

                        send_to_up(data_from_car_image_ID8)  # 将图像数据转发
                        log8 = "ID8 将下位机上传的图像数据发送给上位机"
                        writelog(log8)  # 写入事件

                    t_image_ID8 = threading.Thread(target=ImageRead, args=(client_car_ID8,))
                    t_image_ID8.start()


                elif (x9 == 0):
                    print("上传的是无效数据")

                elif (x9 == 1):
                    print("上传的是状态数据")
                    dataFromCar_state = client_car_ID8.recv(40)
                    data_from_car_state_ID8 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_state
                    log9 = "ID8 收到下位机上传的状态数据"
                    writelog(log9)  # 写入事件

                    send_to_up_ID8(data_from_car_state_ID8)
                    log10 = "ID8 将下位机上传的状态数据发送给上位机"
                    writelog(log10)  # 写入事件


                elif (x9 == 2):
                    print("上传的是经纬度数据")
                    dataFromCar_lnglat = client_car_ID8.recv(36)
                    data_from_car_lnglat_ID8 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_lnglat
                    log11 = "ID8 收到下位机上传的小车当前时刻经纬度数据"
                    writelog(log11)  # 写入事件

                    send_to_up_ID8(data_from_car_lnglat_ID8)
                    log12 = "ID8 将下位机上传的小车当前时刻经纬度数据发送给上位机"
                    writelog(log12)  # 写入事件


                else:
                    print("数据上发错误")
                    # break

        # =======================================定义数据发送函数===============================

    def send_to_up_ID8(data_from_car):
        # print("发送给上位机的数据为：", data_from_car)
        global tcp_server_up
        global client_up_ID8
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_up = "1111111"
            # client_up.send(data_to_up.encode("utf-8"))  # 向下位机发送数据包
            client_up_ID8.send(data_from_car)  # 向下位机发送数据包
            break

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# 车辆九：
#  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_up_ID9():
        global client_up_ID9
        print("从上位机接收数据为：")
        tcp_server_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_up.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
        ip_Ali = "47.102.36.187"  # 服务器的ip地址
        tcp_server_up.bind(("0", 8098))
        tcp_server_up.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            client_up_ID9, cltadd_up = tcp_server_up.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            i = 0  # 记录发送次数

            while True:
                # data_from_up = client_up.recv(1024).decode('utf-8')  # 接收客户端发送的数据进行解码
                # data_from_up = client_up.recv(1024)  # 接收客户端发送的数据进行解码

                # =================写入log文档
                # 1、解码如果判为上位机上发的经纬度数据，则写入文档：time: 上位机上发经纬度数据
                # 2、解码如果判为上位机上发的请求状态数据的指令，则写入文档：time: 上位机上发请求状态数据的指令
                # 3、解码如果判为上位机上发的请求图像数据的指令，则写入文档：time: 上位机上发请求图像数据的指令
                # 4、分三种情况写send_to_car,每种情况后写入文档：time: 向下位机发送......
                while True:

                    data_from_up1 = client_up_ID9.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        m1 = struct.unpack('B', data_from_up1)
                    except:
                        print("解析包头错误")
                    if (m1 == (255,)):  # 如果读到包头则一次性读完包头
                        data_from_up2 = client_up_ID9.recv(3)
                        break

                data_from_up3 = client_up_ID9.recv(20)
                try:
                    x5, x6, x7, x8, x9 = struct.unpack('5i', data_from_up3)  # x5:包长x6：包序号 x7:时间戳 x8:数据域1 x9:数据域2
                except:
                    print("解析前缀信息错误")

                if (x8 == 1):
                    # 上位机下发经纬度数据
                    data_from_up_lnglat = client_up_ID9.recv(1024)
                    log1 = "ID9 收到上位机要传给下位机的未来经纬度序列"
                    writelog(log1)  # 写入事件

                    data_from_up_Lnglat_ID9 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_lnglat
                    send_to_car_ID9(data_from_up_Lnglat_ID9)  # 将数据转发
                    log2 = "ID9 将上位机发送的未来经纬度序列传输给下位机"
                    writelog(log2)
                    print("成功转发经纬度给小车")

                if (x8 == 2):
                    # 请求上发状态数据
                    data_from_up_state = client_up_ID9.recv(1024)
                    log3 = "ID9 收到上位机要传给下位机的请求状态指令"
                    writelog(log3)  # 写入事件

                    data_from_up_State_ID9 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_state
                    send_to_car_ID9(data_from_up_State_ID9)  # 将数据转发
                    log4 = "ID9 将上位机发送的请求状态指令传输给下位机"
                    writelog(log4)
                    print("成功转发状态请求指令给小车")

                if (x8 == 3):
                    # 请求上发图像数据
                    data_from_up_image = client_up_ID9.recv(1024)
                    log5 = "ID9 收到上位机要传给下位机的请求图像指令"
                    writelog(log5)  # 写入事件

                    data_from_up_Image_ID9 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_image
                    send_to_car_ID9(data_from_up_Image_ID9)  # 将数据转发
                    log6 = "ID9 将上位机发送的请求图像指令传输给下位机"
                    writelog(log6)
                    print("成功转发图像请求指令给小车")

                # =================写入log文档

                # print("客户端发送的数据是：", data_from_up)
                # # if data:  # 如果收到的数据不为空，表示客户端仍在请求服务，继续为其服务
                # if data_from_up:
                #     send_to_car_ID9(data_from_up)  # 将数据转发
                #     print("成功转发给小车")
                #     # break
                # else:
                #     break
        # =======================================定义数据发送函数======================================

    def send_to_car_ID9(data_from_up):
        # print("发送给小车的数据为：", data_from_up)
        global client_car_ID9
        flag = True
        # -----------------------------------------------------------------------------------------------
        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_car = "2222222"
            client_car_ID9.send(data_from_up)  # 向下位机发送数据包
            break

        #  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_car_ID9():
        global ip_Ali
        global port_car  # 与小车接通的端口
        global tcp_server_car
        global client_car_ID9
        print("从小车接收数据为：")

        tcp_server_car = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_car.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

        # ip_Ali = input("请输入阿里云的公网ip")  # 服务器的ip地址
        # port_car = input("请输入与小车联通的端口:")  # 服务器的端口号
        port_car = 8083  # 与小车接通的端口号
        tcp_server_car.bind(("0", 8099))
        tcp_server_car.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            # flag = True
            client_car_ID9, cltadd_car = tcp_server_car.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            # while True:
            i = 0  # 记录发送次数
            while True:

                while True:

                    dataFromCar1 = client_car_ID9.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        z1 = struct.unpack('B', dataFromCar1)
                    except:
                        print("解析包头错误")
                    if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                        dataFromCar2 = client_car_ID9.recv(3)
                        break

                dataFromCar3 = client_car_ID9.recv(24)
                try:
                    x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar3)
                except:
                    print("解析前缀信息错误")

                if (x9 == 3):  # 如果上传数据字节数过多，则为图像信息
                    print("上传的是图像数据")

                    def ImageRead(client_car_ID9):
                        data_image1 = client_car_ID9.recv(1)
                        try:
                            image_geshi = struct.unpack('B', data_image1)
                        except:
                            print("解析图像格式错误")
                        # print("图像格式为：", image_geshi)
                        data_image2 = client_car_ID9.recv(4)
                        try:
                            image_len = struct.unpack('1I', data_image2)
                        except:
                            print("解析图像字节数错误")
                        # print("图像字节数：", image_len)
                        image_msg = b''
                        len1 = int(image_len[0])
                        image_length = len1  # 图像数据的字节长度
                        readlength = 0  # 从缓冲区读取的字节数
                        while (len1 > 0):
                            if len1 > 1024:  # 如果剩余图像字节数大于1024
                                buffer = client_car_ID9.recv(1024,
                                                             socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                len1 = len1 - 1024
                                readlength += 1024
                            else:
                                buffer = client_car_ID9.recv(len1, socket.MSG_WAITALL)
                                image_msg += buffer
                                readlength += len1
                                break

                        print("从缓冲区读取的字节数为：", readlength)
                        print("缓冲区剩余图像数据块字节数为：", image_length - readlength)

                        # tianchong_num = image_length % 4  # 计算填充的字节数
                        # shengyu_num = tianchong_num + 16  # 剩下要读的字节数
                        # data_image_shengyu  = client_car.recv(shengyu_num)
                        # print("读完图像数据块后余下的字节数为，检测是否读到包尾，验证帧信息里的数据块字节数是否正确", data_image_shengyu)

                        # 循环读取余下的字节，直到读完四个字节的包尾
                        left = client_car_ID9.recv(1)
                        buffer_left = b''
                        while 1:
                            try:
                                left_baowei = struct.unpack('B', left)
                                print("检测包尾读到的数据为", left_baowei)
                            except:
                                print("检测包尾第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                            if (left_baowei != (204,)):  # 如果读到包尾则一次性读完包尾
                                buffer_left += left
                                left = client_car_ID9.recv(1)
                            else:
                                buffer_left += left
                                left_2 = client_car_ID9.recv(3)
                                buffer_left += left_2
                                print("读完四个包尾")
                                break

                        # data_from_car_image_ID1 =dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg +data_image_shengyu
                        data_from_car_image_ID9 = dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg + buffer_left
                        log7 = "ID9 收到下位机上传的图像数据"
                        writelog(log7)  # 写入事件

                        send_to_up(data_from_car_image_ID9)  # 将图像数据转发
                        log8 = "ID9 将下位机上传的图像数据发送给上位机"
                        writelog(log8)  # 写入事件

                    t_image_ID9 = threading.Thread(target=ImageRead, args=(client_car_ID9,))
                    t_image_ID9.start()



                elif (x9 == 0):
                    print("上传的是无效数据")

                elif (x9 == 1):
                    print("上传的是状态数据")
                    dataFromCar_state = client_car_ID9.recv(40)
                    data_from_car_state_ID9 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_state
                    log9 = "ID9 收到下位机上传的状态数据"
                    writelog(log9)  # 写入事件

                    send_to_up_ID9(data_from_car_state_ID9)
                    log10 = "ID9 将下位机上传的状态数据发送给上位机"
                    writelog(log10)  # 写入事件


                elif (x9 == 2):
                    print("上传的是经纬度数据")
                    dataFromCar_lnglat = client_car_ID9.recv(36)
                    data_from_car_lnglat_ID9 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_lnglat
                    log11 = "ID9 收到下位机上传的小车当前时刻经纬度数据"
                    writelog(log11)  # 写入事件

                    send_to_up_ID9(data_from_car_lnglat_ID9)
                    log12 = "ID9 将下位机上传的小车当前时刻经纬度数据发送给上位机"
                    writelog(log12)  # 写入事件


                else:
                    print("数据上发错误")
                    # break

        # =======================================定义数据发送函数===============================

    def send_to_up_ID9(data_from_car):
        # print("发送给上位机的数据为：", data_from_car)
        global tcp_server_up
        global client_up_ID9
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_up = "1111111"
            # client_up.send(data_to_up.encode("utf-8"))  # 向下位机发送数据包
            client_up_ID9.send(data_from_car)  # 向下位机发送数据包
            break

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# 车辆十：
#  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_up_ID10():
        global client_up_ID10
        print("从上位机接收数据为：")
        tcp_server_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_up.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
        ip_Ali = "47.102.36.187"  # 服务器的ip地址
        tcp_server_up.bind(("0", 8100))
        tcp_server_up.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            client_up_ID10, cltadd_up = tcp_server_up.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            i = 0  # 记录发送次数

            while True:
                # data_from_up = client_up.recv(1024).decode('utf-8')  # 接收客户端发送的数据进行解码
                # data_from_up = client_up.recv(1024)  # 接收客户端发送的数据进行解码

                # =================写入log文档
                # 1、解码如果判为上位机上发的经纬度数据，则写入文档：time: 上位机上发经纬度数据
                # 2、解码如果判为上位机上发的请求状态数据的指令，则写入文档：time: 上位机上发请求状态数据的指令
                # 3、解码如果判为上位机上发的请求图像数据的指令，则写入文档：time: 上位机上发请求图像数据的指令
                # 4、分三种情况写send_to_car,每种情况后写入文档：time: 向下位机发送......
                while True:

                    data_from_up1 = client_up_ID10.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        m1 = struct.unpack('B', data_from_up1)
                    except:
                        print("解析包头错误")
                    if (m1 == (255,)):  # 如果读到包头则一次性读完包头
                        data_from_up2 = client_up_ID10.recv(3)
                        break

                data_from_up3 = client_up_ID10.recv(20)
                try:
                    x5, x6, x7, x8, x9 = struct.unpack('5i', data_from_up3)  # x5:包长x6：包序号 x7:时间戳 x8:数据域1 x9:数据域2
                except:
                    print("解析前缀信息错误")

                if (x8 == 1):
                    # 上位机下发经纬度数据
                    data_from_up_lnglat = client_up_ID10.recv(1024)
                    log1 = "ID10 收到上位机要传给下位机的未来经纬度序列"
                    writelog(log1)  # 写入事件

                    data_from_up_Lnglat_ID10 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_lnglat
                    send_to_car_ID10(data_from_up_Lnglat_ID10)  # 将数据转发
                    log2 = "ID10 将上位机发送的未来经纬度序列传输给下位机"
                    writelog(log2)
                    print("成功转发经纬度给小车")

                if (x8 == 2):
                    # 请求上发状态数据
                    data_from_up_state = client_up_ID10.recv(1024)
                    log3 = "ID10 收到上位机要传给下位机的请求状态指令"
                    writelog(log3)  # 写入事件

                    data_from_up_State_ID10 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_state
                    send_to_car_ID10(data_from_up_State_ID10)  # 将数据转发
                    log4 = "ID10 将上位机发送的请求状态指令传输给下位机"
                    writelog(log4)
                    print("成功转发状态请求指令给小车")

                if (x8 == 3):
                    # 请求上发图像数据
                    data_from_up_image = client_up_ID10.recv(1024)
                    log5 = "ID10 收到上位机要传给下位机的请求图像指令"
                    writelog(log5)  # 写入事件

                    data_from_up_Image_ID10 = data_from_up1 + data_from_up2 + data_from_up3 + data_from_up_image
                    send_to_car_ID10(data_from_up_Image_ID10)  # 将数据转发
                    log6 = "ID10 将上位机发送的请求图像指令传输给下位机"
                    writelog(log6)
                    print("成功转发图像请求指令给小车")

                # =================写入log文档

                # print("客户端发送的数据是：", data_from_up)
                # # if data:  # 如果收到的数据不为空，表示客户端仍在请求服务，继续为其服务
                # if data_from_up:
                #     send_to_car_ID10(data_from_up)  # 将数据转发
                #     print("成功转发给小车")
                #     # break
                # else:
                #     break
        # =======================================定义数据发送函数======================================

    def send_to_car_ID10(data_from_up):
        # print("发送给小车的数据为：", data_from_up)
        global client_car_ID10
        flag = True
        # -----------------------------------------------------------------------------------------------
        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_car = "2222222"
            client_car_ID10.send(data_from_up)  # 向下位机发送数据包
            break

        #  ===========================定义数据接收函数并调用数据发送函数=======================

    def recv_from_car_ID10():
        global ip_Ali
        global port_car  # 与小车接通的端口
        global tcp_server_car
        global client_car_ID10
        print("从小车接收数据为：")

        tcp_server_car = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_car.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用

        # ip_Ali = input("请输入阿里云的公网ip")  # 服务器的ip地址
        # port_car = input("请输入与小车联通的端口:")  # 服务器的端口号
        port_car = 8083  # 与小车接通的端口号
        tcp_server_car.bind(("0", 8101))
        tcp_server_car.listen(128)
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            print("开启监听线程,等待客户端链接")  # 开始监听是否有客户端链接该服务器
            # flag = True
            client_car_ID10, cltadd_car = tcp_server_car.accept()  # 检测到有客户端链接成功，建立一个新的服务器套接字与客户端通信，以及连接的客户端的地址
            print('监听到wifi连接')
            time.sleep(0.5)
            # while True:
            i = 0  # 记录发送次数
            while True:

                while True:

                    dataFromCar1 = client_car_ID10.recv(1)  # 接收客户端发送的数据进行解码
                    print("逐个读取字节")
                    try:
                        z1 = struct.unpack('B', dataFromCar1)
                    except:
                        print("解析包头错误")
                    if (z1 == (221,)):  # 如果读到包头则一次性读完包头
                        dataFromCar2 = client_car_ID10.recv(3)
                        break

                dataFromCar3 = client_car_ID10.recv(24)
                try:
                    x5, x6, x7, x8, x9, x10 = struct.unpack('6i', dataFromCar3)
                except:
                    print("解析前缀信息错误")

                if (x9 == 3):  # 如果上传数据字节数过多，则为图像信息
                    print("上传的是图像数据")

                    def ImageRead(client_car_ID10):
                        data_image1 = client_car_ID10.recv(1)
                        try:
                            image_geshi = struct.unpack('B', data_image1)
                        except:
                            print("解析图像格式错误")
                        # print("图像格式为：", image_geshi)
                        data_image2 = client_car_ID10.recv(4)
                        try:
                            image_len = struct.unpack('1I', data_image2)
                        except:
                            print("解析图像字节数错误")
                        # print("图像字节数：", image_len)
                        image_msg = b''
                        len1 = int(image_len[0])
                        image_length = len1  # 图像数据的字节长度
                        readlength = 0  # 从缓冲区读取的字节数
                        while (len1 > 0):
                            if len1 > 1024:  # 如果剩余图像字节数大于1024
                                buffer = client_car_ID10.recv(1024,
                                                             socket.MSG_WAITALL)  # MSG_WAITALL，表示在接收的时候，函数一定会等待接收到指定size之后才会返回。
                                image_msg += buffer  # image_msg中储存的是读取的累加的图像数据
                                len1 = len1 - 1024
                                readlength += 1024
                            else:
                                buffer = client_car_ID10.recv(len1, socket.MSG_WAITALL)
                                image_msg += buffer
                                readlength += len1
                                break

                        print("从缓冲区读取的字节数为：", readlength)
                        print("缓冲区剩余图像数据块字节数为：", image_length - readlength)

                        # tianchong_num = image_length % 4  # 计算填充的字节数
                        # shengyu_num = tianchong_num + 16  # 剩下要读的字节数
                        # data_image_shengyu  = client_car.recv(shengyu_num)
                        # print("读完图像数据块后余下的字节数为，检测是否读到包尾，验证帧信息里的数据块字节数是否正确", data_image_shengyu)

                        # 循环读取余下的字节，直到读完四个字节的包尾
                        left = client_car_ID10.recv(1)
                        buffer_left = b''
                        while 1:
                            try:
                                left_baowei = struct.unpack('B', left)
                                print("检测包尾读到的数据为", left_baowei)
                            except:
                                print("检测包尾第一个字节解析错误")

                                # 为了舍去上一次报错没读完的字节，是指针继续加一，直到读到包尾
                            if (left_baowei != (204,)):  # 如果读到包尾则一次性读完包尾
                                buffer_left += left
                                left = client_car_ID10.recv(1)
                            else:
                                buffer_left += left
                                left_2 = client_car_ID10.recv(3)
                                buffer_left += left_2
                                print("读完四个包尾")
                                break

                        # data_from_car_image_ID1 =dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg +data_image_shengyu
                        data_from_car_image_ID10 = dataFromCar1 + dataFromCar2 + dataFromCar3 + data_image1 + data_image2 + image_msg + buffer_left
                        log7 = "ID10 收到下位机上传的图像数据"
                        writelog(log7)  # 写入事件

                        send_to_up(data_from_car_image_ID10)  # 将图像数据转发
                        log8 = "ID10 将下位机上传的图像数据发送给上位机"
                        writelog(log8)  # 写入事件

                    t_image_ID10 = threading.Thread(target=ImageRead, args=(client_car_ID10,))
                    t_image_ID10.start()


                elif (x9 == 0):
                    print("上传的是无效数据")

                elif (x9 == 1):
                    print("上传的是状态数据")
                    dataFromCar_state = client_car_ID10.recv(40)
                    data_from_car_state_ID10 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_state
                    log9 = "ID10 收到下位机上传的状态数据"
                    writelog(log9)  # 写入事件

                    send_to_up_ID10(data_from_car_state_ID10)
                    log10 = "ID10 将下位机上传的状态数据发送给上位机"
                    writelog(log10)  # 写入事件


                elif (x9 == 2):
                    print("上传的是经纬度数据")
                    dataFromCar_lnglat = client_car_ID10.recv(36)
                    data_from_car_lnglat_ID10 = dataFromCar1 + dataFromCar2 + dataFromCar3 + dataFromCar_lnglat
                    log11 = "ID10 收到下位机上传的小车当前时刻经纬度数据"
                    writelog(log11)  # 写入事件

                    send_to_up_ID10(data_from_car_lnglat_ID10)
                    log12 = "ID10 将下位机上传的小车当前时刻经纬度数据发送给上位机"
                    writelog(log12)  # 写入事件


                else:
                    print("数据上发错误")
                    # break

        # =======================================定义数据发送函数===============================

    def send_to_up_ID10(data_from_car):
        # print("发送给上位机的数据为：", data_from_car)
        global tcp_server_up
        global client_up_ID10
        flag = True

        while True:  # 在子类中重写run方法，建立与客户端的链接、通信
            data_to_up = "1111111"
            # client_up.send(data_to_up.encode("utf-8"))  # 向下位机发送数据包
            client_up_ID10.send(data_from_car)  # 向下位机发送数据包
            break







    # =========================================建立两个线程========================================
    t_up1 = threading.Thread(target=recv_from_up)
    t_car1 = threading.Thread(target=recv_from_car)

    # 有几辆车就开几个线程
    t_up2 = threading.Thread(target=recv_from_up_ID2)
    t_car2 = threading.Thread(target=recv_from_car_ID2)

    t_up3 = threading.Thread(target=recv_from_up_ID3)
    t_car3 = threading.Thread(target=recv_from_car_ID3)

    t_up4= threading.Thread(target=recv_from_up_ID4)
    t_car4 = threading.Thread(target=recv_from_car_ID4)

    t_up5 = threading.Thread(target=recv_from_up_ID5)
    t_car5 = threading.Thread(target=recv_from_car_ID5)

    t_up6 = threading.Thread(target=recv_from_up_ID6)
    t_car6 = threading.Thread(target=recv_from_car_ID6)

    t_up7 = threading.Thread(target=recv_from_up_ID7)
    t_car7 = threading.Thread(target=recv_from_car_ID7)

    t_up8 = threading.Thread(target=recv_from_up_ID8)
    t_car8 = threading.Thread(target=recv_from_car_ID8)

    t_up9 = threading.Thread(target=recv_from_up_ID9)
    t_car9 = threading.Thread(target=recv_from_car_ID9)

    t_up10 = threading.Thread(target=recv_from_up_ID10)
    t_car10 = threading.Thread(target=recv_from_car_ID10)

    t_up1.start()
    t_car1.start()

    t_up2.start()
    t_car2.start()

    t_up3.start()
    t_car3.start()

    t_up4.start()
    t_car4.start()

    t_up5.start()
    t_car5.start()

    t_up6.start()
    t_car6.start()

    t_up7.start()
    t_car7.start()

    t_up8.start()
    t_car8.start()

    t_up9.start()
    t_car9.start()

    t_up10.start()
    t_car10.start()

    t_up1.join()
    t_car1.join()
    t_up2.join()
    t_car2.join()
    t_up3.join()
    t_car3.join()
    t_up4.join()
    t_car4.join()
    t_up5.join()
    t_car5.join()
    t_up6.join()
    t_car6.join()
    t_up7.join()
    t_car7.join()
    t_up8.join()
    t_car8.join()
    t_up9.join()
    t_car9.join()
    t_up10.join()
    t_car10.join()
    tcp_server_up.close()
    tcp_server_car.close()





if __name__ == "__main__":
    main()
