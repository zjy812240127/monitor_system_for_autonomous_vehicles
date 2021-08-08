import os
import sys
import os.path
import re
import numpy as np
from scipy import interpolate
import pylab as pl


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


second_chazhi()