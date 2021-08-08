import re
import numpy as np
import math

x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # ¦Ð
a = 6378245.0  # ³¤°ëÖá
ee = 0.00669342162296594323  # Æ«ÐÄÂÊÆ½·½
coordinate = []
lng = []
lat = []
converted_lng = []
converted_lat = []

def first_fenhang():
    file1 = open("omap_input.txt", "r")

    with open("fenhang_output.txt", "w") as file2:
        data = file1.read()

        data2 = re.split(' |,', data)  # 多个分割条件 空格和逗号
        # data2 = data.split(',')
        # print(data2)
        i = 0

        while (i < len(data2) - 3):
            t1 = data2[i]
            t2 = data2[i + 1]
            #             t = [data2[i],data2[i+1]]    #输出文档里存在[]

            #            c= json.load(t.replace('(','').replace(')',''))

            #            file2.write(str(t) + '\n') #因为是str字符串，输出文档里有''
            file2.write(t1 + ',' + t2 + '\n')  # 输出文档没有[]也没有‘’

            # print(t)
            i = i + 3
    return()


def second_chazhi():
    with open("fenhang_output.txt", "r") as file1:
        data = file1.read()

        data2 = re.split('\n|,', data)
        # print (data2)

        #    with open ("result.txt","w") as file2:
        i = 0
        x = []
        y = []
        while i <= len(data2) - 2:
            x.append(float(data2[i]))  # 逐个向数组里添加经度数据
            y.append(float(data2[i + 1]))  # 逐个添加维度数据
            i = i + 2

        # print(x)
        #        print(y)
        #        return

        j = 0
        k = 0
        xadd = []
        yadd = []
        while j < len(x) - 1:
            x1 = np.linspace(x[j], x[j + 1], 10)
            # print(x1)
            xadd.extend(x1)  ###用extend而不是append，可以实现数组的加，而不会引入[]
            j = j + 1

        sum1 = len(xadd)
        # print(sum1)

        while k < len(y) - 1:
            y1 = np.linspace(y[k], y[k + 1], 10)
            # print(y1)
            yadd.extend(y1)
            k = k + 1

        sum2 = len(yadd)
        # print(sum2)

    with open("chazhi_result.txt", "w") as file2:
        ii = 0
        while ii < len(xadd):
            file2.write(str(xadd[ii]) + ',' + str(yadd[ii]) + '\n')
            ii = ii + 1

    file2.close()

    #
    file1.close()
    return ()



def gcj02_to_bd09(lng, lat):
    """
    火星坐标系(GCJ-02)转百度坐标系(BD-09)
    谷歌、高德——>百度
    :param lng:火星坐标经度
    :param lat:火星坐标纬度
    :return:
    """
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * x_pi)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * x_pi)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return bd_lng, bd_lat
    # return [bd_lng, bd_lat]


def bd09_to_gcj02(bd_lon, bd_lat):
    """
    百度坐标系(BD-09)转火星坐标系(GCJ-02)
    百度——>谷歌、高德
    :param bd_lat:百度坐标纬度
    :param bd_lon:百度坐标经度
    :return:转换后的坐标列表形式
    """
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return gg_lng, gg_lat
    # return [gg_lng, gg_lat]


def wgs84_to_gcj02(lng, lat):
    """
    WGS84转GCJ02(火星坐标系)
    :param lng:WGS84坐标系的经度
    :param lat:WGS84坐标系的纬度
    :return:
    """
    if out_of_china(lng, lat):  # ÅÐ¶ÏÊÇ·ñÔÚ¹úÄÚ
        return [lng, lat]
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return mglng, mglat
    # return [mglng, mglat]


def gcj02_to_wgs84(lng, lat):
    """
   GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    if out_of_china(lng, lat):
        return [lng, lat]
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return lng * 2 - mglng, lat * 2 - mglat
    # return [lng * 2 - mglng, lat * 2 - mglat]


def bd09_to_wgs84(bd_lon, bd_lat):
    lon, lat = bd09_to_gcj02(bd_lon, bd_lat)
    return gcj02_to_wgs84(lon, lat)


def wgs84_to_bd09(lon, lat):
    lon, lat = wgs84_to_gcj02(lon, lat)
    return gcj02_to_bd09(lon, lat)


def _transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def _transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


def out_of_china(lng, lat):
    """
     判断是否在国内，不在国内不做偏移
    :param lng:
    :param lat:
    :return:
    """
    return not (lng > 73.66 and lng < 135.05 and lat > 3.86 and lat < 53.55)


pathIn = r"E:\pycharm_project\MapData\chazhi_result.txt"
pathOut = r"E:\pycharm_project\MapData\change_result_ouput.txt"
result = []
count = 0


if __name__ == "__main__":
    first_fenhang()
    second_chazhi()
    with open(pathIn, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if (len(line) == 1): continue
            tmp = line.rstrip().split(',')
            lng.append(float(tmp[0]))
            lat.append(float(tmp[1]))
    #            lng.append(tmp[0])
    #            lat.append(tmp[1])
    try:
        for i in range(len(lng)):
            converted = wgs84_to_gcj02(lng[i], lat[i])
            with open(pathOut, 'a') as f:
                print(str(converted))
                # f.writelines(str(converted) + "\n")
                f.writelines("new BMap.Point"+str(converted)+ ',' + "\n")    ####
                ###########----------------改成html文件所需的格式
                count += 1
            print("第" + str(count) + "条数据写入成功...")
    except Exception as err:
        print(err)