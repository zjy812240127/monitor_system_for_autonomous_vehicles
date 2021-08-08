import os
import sys
import os.path
import re


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


#


first_fenhang()