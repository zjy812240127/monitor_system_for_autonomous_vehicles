import sys
import linecache

def main():

    filePath = "Source.txt"
    with open("Source.txt",'r') as file_in:
        sum = len(file_in.readlines())  # 读取总共的行数
        print(sum)

        with open("Source_to_pdf.txt",'w') as file_out:  # 打开要输出的文档
            i = 0
            # line_abc = file_in.readline()
            for i in range (0,sum):

                line_i = linecache.getlines("Source.txt",i)   # 读取对应行程序

                # line_i = file_in.readline()
                line_i.lstrip()  # 删去左边空格

                if not line_i.startswith("\#"):  # 如果该行不是以注释标志符开头则为有效代码
                    file_out.write(line_i + '\n')

                    print("写入第"+i+"行代码")








if __name__ =="__main__":
    main()