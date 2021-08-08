奥维地图导出的经纬度格式为wgs


将奥维地图导出的经纬度数据放入“omap_input.txt”文件夹，运行sum.py文件，生成分行结果文件fenhang_output.txt；插值结果文件chazhi_result.txt以及坐标转换结果文件change_result_output.txt；
try中选择导出给下位机格式的文件以及导出给html文件格式的数据f.writelines


note:每次要新生成一组数据的话要先清空文件内的数据，否则运行程序不会覆盖上一次已有的数据




