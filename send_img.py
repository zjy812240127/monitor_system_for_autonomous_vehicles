# --coding:utf-8--
import socket

files = open("send_image_test.jpg", 'rb')

# 创建一个socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 建立连接
s.connect(('10.81.231.116', 7890))


print("send image")
baotou1 = 0xdd  # char
baotou2 = 0xdd  # char
baotou3 = 0xdd  # char
baotou4 = 0xdd  # char
baochang = 300  # int  i包长 字节对齐会在double前面加上四个字节00000000
baoxuhao = 1  # int  i发送次数
shijianchuo = 0  # int  i上位机下发设为0
zhongduanID = 1  # int  i终端ID
shujuyu_1 = 3  # Uint  I 类型3表示上传图像


## 数据块之前的内容
data_1 = [baotou1, baotou2, baotou3, baotou4, baochang, baoxuhao, shijianchuo,zhongduanID,

          shujuyu_1]

# data_len = 0  # 图片文件的总子节数
data_image = []
while (True):
    print("读取图片")
    image_msg = files.read(1024)
    data_image += image_msg  # 缓存读到的字节
    if not image_msg:
        break
data_len = len(data_image)  # 图片文件的总字节数
print("图片文件的总字节数",data_len)

buquan = (data_len +1) % 4  # 满足4的倍数补上的字节数

shujuyu_2 = data_len + 5 + buquan # int  图像数据块字节数（要加上前面的五个字节和补上的字节数）
geshi = 1
num = data_len  # 图片的总子节数

data_1.append(shujuyu_2)
data_1.append(geshi)
data_1.append(num)
for j in range(num):
    data_1.append(data_image[j])
for i in range(buquan):
    data_1.append(0x00)



yuliu = 0x00
for n in range(0, 12):
    data_1.append(yuliu)

baowei = 0xcc
# 循环加入四个0xee表示包尾
for m in range(0, 4):
    data_1.append(baowei)

print(data_1)

s.send(data_1)
# print(data_1)
files.close()
s.close()
