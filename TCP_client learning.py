# TCP_client learning
import socket
import time
import linecache
import struct
import threading

def main():

	# 1.创建socket
	tcp_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)  # STREAM表示TCP传输
	
	# 2.链接服务器
	tcp_socket.connect(("47.102.36.187",8083))  # 相当于打电话先拨通对方号码
	# =========================================经纬度信息===============================
	# 3.发送数据
	# tcp_socket.send(b"hahhah")  # 相当于把udp里的sendto分成to+send，写信需要每封信都写地址，打电话只要拨一次号码
	# send_data = input(data)
	# tcp_socket.send(send_data.encode("utf-8"))
	# data1 = "dd dd dd dd 00 00 00 40 00 00 00 02 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 18 00 00 00 01 40 5E 02 B1 7A A5 B9 23 40 3E 3B 39 59 08 7F BB 00 00 00 00 00 00 00 00 00 00 00 00 cc cc cc cc"
	i =0
	baotou1 = 0xdd  # char
	baotou2 = 0xdd  # char
	baotou3 = 0xdd  # char
	baotou4 = 0xdd  # char
	baochang = 64  # int  i包长 字节对齐会在double前面加上四个字节00000000
	baoxuhao = i  # int  i发送次数
	shijianchuo = 0  # int  i上位机下发设为0
	zhongduanID = 1  # int  i终端ID
	shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
	shujuyu_2 = 16  # int  I 5个经纬度数组，一共80字节
	dianshu = 1  # Uint32 I 下发5个点

	## 数据块之前的内容
	data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,zhongduanID,

			  shujuyu_1, shujuyu_2, dianshu]

	#####################################--------------------------------------------数据域
	file_path = "jingweidu.txt"  # 经纬度存储文件名

	with open("jingweidu.txt", 'r') as f:  # 此处文档要与上述文档一样
		t_sum = len(f.readlines())  # 总共有的经纬度组数

		# print("ccccccc文档的总行数为：", t_sum)
		if 6 < t_sum:  # 如果最后剩余的经纬度数组少于5，则停止发送，防止报错导致服务器关闭
			for j in range(5 * i + 1, 5 * i + 2):
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
		print(data_1)

	# 显示完整数据包
	# print(data_1)

	## 加上!为了防止int型数据与double交界处自动补上一个四字节int型的0（80与第一个经度之间在调试助手上接收时中间会多出00000000，加了之后会改
	# 为大端接收模式
	dataTobytes = struct.pack('!4B4i3I2d16B', data_1[0], data_1[1], data_1[2], data_1[3],
							  data_1[4],
							  data_1[5]
							  , data_1[6], data_1[7], data_1[8], data_1[9], data_1[10],
							  data_1[11]
							  , data_1[12], data_1[13], data_1[14], data_1[15],
							  data_1[16],
							  data_1[17], data_1[18], data_1[19]
							  , data_1[20], data_1[21], data_1[22], data_1[23],
							  data_1[24],
							  data_1[25], data_1[26], data_1[27],data_1[28]

							  )
	print(type(dataTobytes), len(dataTobytes))

#=========================================经纬度信息===============================

#==================================================状态信息==========================
	baotou1 = 0xdd  # char
	baotou2 = 0xdd  # char
	baotou3 = 0xdd  # char
	baotou4 = 0xdd  # char
	baochang = 68  # int  i包长 字节对齐会在double前面加上四个字节00000000
	baoxuhao = 1  # int  i发送次数
	shijianchuo = 0  # int  i上位机下发设为0
	zhongduanID = 1  # int  i终端ID
	shujuyu_1 = 1  # Uint  I 类型1表示下发经纬度
	shujuyu_2 = 24  # int  I 5个经纬度数组，一共80字节
	# dianshu = 1  # Uint32 I 下发5个点
	zhuangtai = 1
	Lrpm = 12.5
	Rrpm = 12.5
	angle = 50
	pwm = 5
	yuliuwei = 0

	## 数据块之前的内容
	data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo, zhongduanID,

			  shujuyu_1, shujuyu_2,zhuangtai,Lrpm,Rrpm,angle,pwm,yuliuwei]

	yuliu = 0x00
	for n in range(0, 12):
		data_1.append(yuliu)

	baowei = 0xee
	# 循环加入四个0xee表示包尾
	for m in range(0, 4):
		data_1.append(baowei)
	print(data_1)

	data_state = struct.pack('!4B4i2II2fIfI16B', data_1[0], data_1[1], data_1[2], data_1[3],
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
							  , data_1[28], data_1[29], data_1[30], data_1[31]

							  )
	print(type(data_state), len(data_state))




	def send_jingweidu(data_jingweidu):
		while True:
			tcp_socket.send(data_jingweidu)
			time.sleep(2)

	def send_state(data_state_x):
		while True:
			tcp_socket.send(data_state_x)
			time.sleep(5)



	print ("++++++++++++++")
	t1 = threading.Thread(target=send_jingweidu,args=(dataTobytes,))
	t1.start()
	t2 = threading.Thread(target=send_state,args=(data_state,))
	t2.start()
	
	# 4.关闭套接字
	t1.join()  # 要在线程结束之后再关闭套接字
	t2.join()
	tcp_socket.close()


if __name__ == "__main__":
	main()