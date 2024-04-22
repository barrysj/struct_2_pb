#/bin/bash
if [ ${1}x == "clean"x ];then
	rm out_cpp.cpp out_pb.proto demo.cpp.ii
	exit 0
fi

cd demo; python3 ../analyze.py -f demo.cpp -c out_cpp.cpp -p out_pb.proto -E

