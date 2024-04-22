struct MyStruct{
    unsigned ip;
    unsigned short port;
};

class MyClass
{
    int m1;
    unsigned int m2;
    long long m3;
    
    uint8_t m4;
    uint32_t m5;
    uint32_t m6;
//  int m7;
/*
    int m8;
    int m9;
*/
    int foo(int& bar) {
        return 0;
    }

    MyStruct   s1;
    MyStruct   s2;

    unsigned arr1[10];
    unsigned arr2[10][20];

    char reverse[100];
};