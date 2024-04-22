一个工具，用于将C/C++的类/结构体转为对应pb协议，并生成一份C++类对象和pb对象互相转换的C++代码
此工具的输入：
* 一份包含了C的类或结构体的代码片段
此工具的输出：
* 对应类或结构体的pb协议.proto文件
* 将C++对象和pb对象互相转换的C++代码文件
* 可选的中间输出（执行参数-E）

文件列表：
* analyze.py 程序主文件
* run.sh 运行脚本
在demo/下，包含如下内容：
* demo.cpp 是一份代码片段，包含了大量结构体定义
* demo.cpp.ii 是-E参数输出的中间处理结果，每行开头的括号中的bool字符串表示是否是注释代码、是否忽略本行
* out_cpp.cpp 是上述提到的互相转换用的C++代码
* out_pb.proto 是上述提到的根据demo.cpp生成的pb文件

# Thanks for your reading me.
