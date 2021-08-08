def start_client():
    # 创建线程锁，防止主线程socket被close了，子线程还在recv而引发的异常
    socket_lock = threading.Lock()

    def read_thread_method():
        while True:
            if not tcp_socket:  # 如果socket关闭，退出
                break
            # 使用select监听客户端（这里客户端需要不停接收服务端的数据，所以监听客户端）
            # 第一个参数是要监听读事件列表，因为是客户端，我们只监听创建的一个socket就ok
            # 第二个参数是要监听写事件列表，
            # 第三个参数是要监听异常事件列表，
            # 最后一个参数是监听超时时间，默认永不超时。如果设置了超时时间，过了超时时间线程就不会阻塞在select方法上，会继续向下执行
            # 返回参数 分别对应监听到的读事件列表，写事件列表，异常事件列表
            rs, _, _ = select.select([tcp_socket], [], [], 10)
            for r in rs:  # 我们这里只监听读事件，所以只管读的返回句柄数组
                socket_lock.acquire()  # 在读取之前先加锁，锁定socket对象（sock是主线程和子线程的共享资源，锁定了sock就能保证子线程在使用sock时，主线程无法对sock进行操作）

                if not tcp_socket:  # 这里需要判断下，因为有可能在select后到加锁之间socket被关闭了
                    socket_lock.release()
                    break

                # data = r.recv(1024)  # 读数据，按自己的方式读
                recv_data = r.recv(1024).decode()
                # print(recv_data)

                socket_lock.release()  # 读取完成之后解锁，释放资源

                if not recv_data:
                    print("小车停止上传数据")
                else:
                    if (len(recv_data) == 44):  # 如果上发的是44字节的数据（请求下发经纬度时设下位机发送数据块为空）
                        # 发送数据示例 dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18  00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                        baotou1 = 0xff  # char
                        baotou2 = 0xff  # char
                        baotou3 = 0xff  # char
                        baotou4 = 0xff  # char
                        baochang = 124  # int  包长
                        baoxuhao = i  # int  发送次数
                        shijianchuo = 0  # int  上位机下发设为0
                        zhongduanID = 1  # int  终端ID
                        shujuyu_1 = 1  # int  类型1表示下发经纬度
                        shujuyu_2 = 80  # int  5个经纬度数组，一共80字节

                        ## 数据块之前的内容
                        data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo, zhongduanID,
                                  shujuyu_1, shujuyu_2]

                        #####################################--------------------------------------------数据域
                        file_path = "jingweidu.txt"  # 经纬度存储文件名

                        with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
                            t_sum = len(f.readlines())  # 总共有的经纬度组数

                            print("ccccccc文档的总行数为：", t_sum)
                            if 5 * i + 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
                                for j in range(5 * i + 1, 5 * i + 6):
                                    line_number = j  # 文件行数从1开始，而i初始值为0
                                    fread_j = linecache.getline(file_path, line_number).strip()  # 读取对应行数的经纬度
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
                        print("data_1", data_1)

                        yuliu = 0x00
                        # 循环加入12个0x00表示预留位和CRC32位
                        for n in range(0, 12):
                            data_1.append(yuliu)

                        baowei = 0xee
                        # 循环加入四个0xee表示包尾
                        for m in range(0, 4):
                            data_1.append(baowei)
                            print(data_1)

                        # 显示完整数据包
                        print(data_1)

                        ## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
                        # 为大端接收模式
                        dataTobytes = struct.pack('!4B6i10d16B', data_1[0], data_1[1], data_1[2], data_1[3], data_1[4],
                                                  data_1[5]
                                                  , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10], data_1[11]
                                                  , data_1[12], data_1[13], data_1[14], data_1[15], data_1[16],
                                                  data_1[17], data_1[18], data_1[19]
                                                  , data_1[20], data_1[21], data_1[22], data_1[23], data_1[24],
                                                  data_1[25], data_1[26], data_1[27]
                                                  , data_1[28], data_1[29], data_1[30], data_1[31], data_1[32],
                                                  data_1[33], data_1[34], data_1[35]

                                                  )
                        print(type(dataTobytes), len(dataTobytes))

                        # print('1111111111111111111111111')
                        # print(data_1)
                        # dataTobytes = dataTobytes[:28]+dataTobytes[32:]
                        # client.send(dataTobytes)
                        tcp_socket.send(dataTobytes)
                        print(i)
                        i += 1

                        # 0xff, 0xff, 0xff, 0xff, 124, 0, 0, 1, 1, 80, 120.04208246406465, 30.231343807768763, \
                        # 120.04207836129298, 30.23134029404531, 120.04207425852078, 30.231336780321374, \
                        # 120.04207015574802, 30.231333266596973, 120.0420660529747, 30.231329752872096, \
                        # 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xee, 0xee, 0xee, 0xee
                    # ==========================================下传经纬度数据

                    ####-------------------  上位机下传指令

                    ####-------------------  接收下位机上传数据

                    ##================================更新车辆状态数据以及检测废数据
                    elif (len(recv_data) == 68):  # 小车上发车辆状态数据
                        # 1. 如果数据域前四个字节为0，则上传的为无效的废数据
                        # 2. 如果数据域前四个字节为1，则上传的是车辆的状态信息，分别更新GUI界面上的数据
                        # 3. 如果数据域前四个字节为2，则上传的是GPS的定位信息，提取经纬度数据用于控制算法
                        # 4. 如果数据区前四个字节为3，则上传的是图像信息，更新GUI界面上的图像数据
                        # 上传结构体数据示例
                        # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                        x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, x15, x16, x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32 = struct.unpack(
                            '!4B12i16B', recv_data)  # 解包C的结构体数据，大端格式加！（网络调试助手为大端格式，下位机上传为小端格式，需要改）

                        ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:16]:数据块， x[17:28]: 预留CRC， x[29:32]: 包尾
                        print("接收数据转换成字符串为：", x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, x15, x16,
                              x17,
                              x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31, x32)

                        if (x9 == 0):  # 数据域前四个字节为0x000x000x000x00,对应情况1
                            print("这是无效的废数据")


                        ##==============================更新车辆状态数据
                        elif (len(recv_data) == 68):  # 数据域前四个字节为0x000x000x000x01,对应情况2
                            print("这是车辆的状态信息")
                            self.serverFlag = 1  # 启动多线程服务器？

                            ID = x8
                            LPWM = x11
                            RPWM = x15
                            L2v = x12
                            R2V = x13
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

                            # self.stateButton.setCheckable(False)
                        ##==============================更新车辆状态数据
                    ##================================更新车辆状态数据以及检测废数据

                    ##================================获取车辆上传的GPS定位数据
                    elif (len(recv_data) == 64):  # 如果上传的数据为64字节，则对应车辆目前GPS获取的经纬度数据
                        print("这是车辆所处的经纬度")
                        # 上传数据示例
                        # dd dd dd dd 00 00 00 44 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 00 00 00 05 00 00 00 05 00 00 00 03 00 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc
                        # 数据块：N 的十六进制为4E; P的十六进制为50；L为4C；B为42；卫星个数：01；填充数据： 00 00
                        # 经度：（120.04208246406465）40 5E 02 B1 7A A5 B9 23  纬度：（30.231343807768763）40 3E 3B 39 59 08 7F BB
                        # 120.04862759640338  \x40\x5e\x03\x1c\xb6\xec\x0f\x14  30.237128736109234  \x40\x3e\x3c\xb4\x78\x06\x87\xee
                        # 120.0457642526888  \x40\x5e\x02\xed\xcd\x30\x27\xf4  30.23500645123769  \x40\x3e\x3c\x29\x61\xfe\x6a\x37

                        y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14, y15, y16, y17, y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31 = struct.unpack(
                            '!4B6i2B1h2d16B',
                            recv_data)  # 解包C的结构体数据,大端格式加！,h表示两个字节的short型数据（网络调试助手为大端格式，下位机上传为小端格式，需要改）

                        ### x[1:4]:包头0xdd， x5:包长， x6:包序号， x7:时间戳， x8:ID， x9:数据域1， x10:数据域2， x[11:15]:数据块， x[16:27]: 预留CRC， x[28:31]: 包尾
                        print("接收数据转换成字符串为：", y1, y2, y3, y4, y5, y6, y7, y8, y9, y10, y11, y12, y13, y14, y15, y16,
                              y17,
                              y18, y19, y20, y21, y22, y23, y24, y25, y26, y27, y28, y29, y30, y31)

                        GPS = y11  # GPS协议类型
                        Star = y12  # 卫星个数
                        jingdu_Car = y14  # 小车所处经度
                        weidu_Car = y15  # 小车所处纬度

                        lng = y14
                        lat = y15
                        converted = []

                        converted = wgs84_to_bd09_change.gcj02_to_bd09(y14, y15)  # 调用外部函数将谷歌地图GPS经纬度数据转换成百度地图格式
                        # print("++++++++++++++++++++++",converted[0],converted[1])

                        ti = threading.Thread(target=fun_time, args=(converted[0], converted[1],))
                        ti.start()

                        self.siglng.emit(float(converted[0]))
                        self.siglat.emit(float(converted[1]))
                        time.sleep(1)  # 延时太大的话程序界面会崩溃

                        print("GPS:", str(GPS))
                        print("卫星个数：", int(Star))
                        print("小车所处经度:", float(jingdu_Car))
                        print("小车所处纬度:", float(weidu_Car))
                    ##================================获取车辆上传的GPS定位数据

                    elif (len(recv_data) > 200):  # 如果上传数据字节数过多，则为图像信息

                        cv.imwrite('Imagechange01.jpg', frame)  # 将f变量中的图片信息保存为一个图片格式文件
                        Image = 'Imagechange01.jpg'
                        # Image = 'picture1.jpg'
                        # print(Image)
                        self.sigImage.emit(Image)
                        print("这是上传的图像数据")

                    else:
                        print("上传数据出错")

            client.close()
            print("已经与小车断开连接")

    # 创建一个线程去读取数据
    read_thread = threading.Thread(target=read_thread_method)
    read_thread.setDaemon(True)
    read_thread.start()

# =====================================================
    # 测试同时写数据
    if (askstateFlag == 1):  # 如果请求状态按钮被激活则 下发请求状态指令，小车发送任意指令上位机均可以下发请求指令
        print("开始请求车辆状态的数据")
        send_state_baotou = 0xff  # 包头
        send_state_baochang = 44  # 包长度，请求时数据域为0字节
        send_state_xuhao = j  # 包序号
        send_state_timechuo = 0  # int 时间戳上位机 暂时设为零
        send_state_ID = 1  # int 固定车辆ID号
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
            send_state_dataTobytes.append(send_state_ID)
            send_state_dataTobytes.append(send_state_shujuyu_1)
            send_state_dataTobytes.append(send_state_shujuyu_2)
        for state_j in range(0, 8):
            send_state_dataTobytes.append(send_state_yuliu)

        for state_k in range(0, 4):
            send_state_dataTobytes.append(send_state_CRC32)

        for state_l in range(0, 4):
            send_state_dataTobytes.append(send_state_baowei)

        print(send_state_dataTobytes)
        # 4B6i16B

        dataTobytes_state = struct.pack('!4B6i16B', send_state_dataTobytes[0],
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
                                        , send_state_dataTobytes[24], send_state_dataTobytes[25])

        # client.send(dataTobytes_state)  # 发送请求的信号的数据格式

        tcp_socket.send(dataTobytes_state)
        askstateFlag = 0  # 发送完后重新把标志位置零
        j += 1
    ####======================上位机向下位机发送请求状态数据的请求

    ##==========================上位机向下位机请求图像数据
    if (askimageFlag == 1):  # 请求图像按钮被按下时激活，向下发送请求图像指令，小车发送任意数据上位机均可以下发请求指令
        print("开始请求图像的数据")

        send_image_baotou = 0xff  # 包头
        send_image_baochang = 44  # 包长度，请求时数据域为0字节
        send_image_xuhao = h  # 包序号
        send_image_timechuo = 0  # int 时间戳上位机 暂时设为零
        send_image_ID = 1  # int 固定车辆ID号
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
        send_image_dataTobytes.append(send_image_ID)
        send_image_dataTobytes.append(send_image_shujuyu_1)
        send_image_dataTobytes.append(send_image_shujuyu_2)
        for image_j in range(0, 8):
            send_image_dataTobytes.append(send_image_yuliu)

        for state_k in range(0, 4):
            send_image_dataTobytes.append(send_image_CRC32)

        for state_l in range(0, 4):
            send_image_dataTobytes.append(send_image_baowei)

        print(send_image_dataTobytes)
        # 4B6i16B

        dataTobytes_image = struct.pack('!4B6i16B', send_image_dataTobytes[0],
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
                                        , send_image_dataTobytes[24], send_image_dataTobytes[25])

        # client.send(dataTobytes_image)  # 发送请求的信号的数据格式
        tcp_socket.send(dataTobytes_image)
        askimageFlag = 0  # 发送后标志位重新置零
        h += 1
    ##==========================上位机向下位机请求图像数据

    # 清理socket，同样道理，这里需要锁定和解锁
    socket_lock.acquire()
    tcp_socket.close()
    tcp_socket = None
    socket_lock.release()

