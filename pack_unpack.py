
##在2i1d1B1B1B1B前加上！，防止int与double数据交界处为了对齐而自动补上的一个四字节的0，同时会改变大小端

import struct
import string

def main():
    data_int1 = 256
    data_int2 = 122
    data_float = 120.03571871343244
    data_float2 =30.224876534638387
    data_head1 = 0xff
    data_head2 = 0xff
    data_head3 = 0xff
    data_head4 = 0xff
    '''
    如果按网络传输接收到字符串，可在2i1d1B1B1B1B前加上！，改为!2i1d1B1B1B1B，会改变大小端
    上位机通过socket.recv接收到了一个c语言编写的下位机的结构体数据，存在字符串dataTobytes中
    a, b, c , d, e, f, g= struct.unpack('!2i1d1B1B1B1B', dataTobytes),
    2i表示对应于c语言2个4字节int类型数据
    1d表示对应于c语言1个8字节double类型数据
    1B表示对应于c语言一个字节无符号char
    '''
    dataTobytes = struct.pack('!2i2d1B1B1B1B', data_int1, data_int2, data_float,data_float2, data_head1,data_head2, data_head3, data_head4  )
    # print (repr(dataTobytes[8:16]))
    # print(type(dataTobytes[0:4]), len(dataTobytes))
    # print(hex(dataTobytes[8]))
    # print(dataTobytes[9])
    # print(dataTobytes[2])
    # print(dataTobytes[3])
    # print(dataTobytes[4])
    '''
    dataTobytes为字符串，对应于data_int1, data_int2, data_float, data_head1,data_head2, data_head3, data_head4在内存中的二进制串
    如，前四个字节传送的是data_int1,则前面四个字符为0x00,0x01,0x00,0x00
    '''
    #dataTobytes = struct.pack('2i1d', data_int1, data_int2, data_float )
    a, b, c , d, e, f, g,h= struct.unpack('2i2d1B1B1B1B', dataTobytes)
    # a, b, c = struct.unpack('2i1d', dataTobytes)
    # print(a)
    # print(b)
    # print(c)
    # print(d)
    # print(e)
    # print(f)
    # print(g)

    # 打印浮点数120.04和30.23的二进制串
    for i in range(8,24):
        print(dataTobytes[i],hex(dataTobytes[i]))  # 打印经纬度的二进制对应的十六进制，socket中传输的字节流
    #      print(dataTobytes[i])  # 打印经纬度的二进制
        
if __name__ == "__main__":
    main()