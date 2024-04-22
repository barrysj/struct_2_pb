void set_pb_func_MyStruct(const ::MyStruct &cppObj, test_namespace::test::MyStruct &pbObj) {
	pbObj.set_ip(cppObj.ip);
	pbObj.set_port(cppObj.port);
}
void get_pb_func_MyStruct(::MyStruct &cppObj, const test_namespace::test::MyStruct &pbObj) {
	cppObj.ip = pbObj.ip();
	cppObj.port = pbObj.port();
}
void set_pb_func_MyClass(const ::MyClass &cppObj, test_namespace::test::MyClass &pbObj) {
	pbObj.set_m1(cppObj.m1);
	pbObj.set_m2(cppObj.m2);
	pbObj.set_m3(cppObj.m3);
	pbObj.set_m4(cppObj.m4);
	pbObj.set_m5(cppObj.m5);
	pbObj.set_m6(cppObj.m6);
	set_pb_func_MyStruct(cppObj.s1, *(pbObj.mutable_s1()));
	set_pb_func_MyStruct(cppObj.s2, *(pbObj.mutable_s2()));
	for (int i = 0; i < (10); ++i) {
		pbObj.add_arr1(((unsigned*)cppObj.arr1)[i]);
	}
	for (int i = 0; i < (10 * 20); ++i) {
		pbObj.add_arr2(((unsigned*)cppObj.arr2)[i]);
	}
}
void get_pb_func_MyClass(::MyClass &cppObj, const test_namespace::test::MyClass &pbObj) {
	cppObj.m1 = pbObj.m1();
	cppObj.m2 = pbObj.m2();
	cppObj.m3 = pbObj.m3();
	cppObj.m4 = pbObj.m4();
	cppObj.m5 = pbObj.m5();
	cppObj.m6 = pbObj.m6();
	get_pb_func_MyStruct(cppObj.s1, pbObj.s1());
	get_pb_func_MyStruct(cppObj.s2, pbObj.s2());
	for (int i = 0; i < pbObj.arr1_size(); ++i) {
		((unsigned*)cppObj.arr1)[i] = pbObj.arr1(i);
	}
	for (int i = 0; i < pbObj.arr2_size(); ++i) {
		((unsigned*)cppObj.arr2)[i] = pbObj.arr2(i);
	}
}
