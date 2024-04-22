import re
import sys, getopt, time
import logging
from typing import List, Dict, NoReturn, Mapping, Set

class UserClass(object):
    def __init__(self, class_name:str, start_line_idx, line_num):
        self.name = class_name
        self.start_idx = start_line_idx
        self.line_num = line_num
        self.depend_class:Set[UserClass]
        self.referred_by_class:Set[UserClass]
    
    def __str__(self) -> str:
        return "user_class: {}, range {}-{}".format(self.name, self.start_idx + 1, self.start_idx + self.line_num)
    
    def __repr__(self) -> str:
        return "user_class: {}, range {}-{}".format(self.name, self.start_idx + 1, self.start_idx + self.line_num)
    
    def depend(self, one_class):
        self.depend_class.add(one_class)
    
    def referred_by(self, one_class):
        self.referred_by_class.add(one_class)


class LineObject(object):
    exp_pattern1 = re.compile(r'//.*$')
    exp_pattern2 = re.compile(r'/\*.*$')
    exp_pattern3 = re.compile(r'^.*\*/')

    def __init__(self, one_line:str, line_idx:int, in_exp_block:bool=False):
        self.origin_line = one_line
        self.line_idx = line_idx
        self.in_exp_block = in_exp_block

        self.strip_line = one_line.strip()

        self.line_without_exp = re.sub(LineObject.exp_pattern1, "", one_line)
        self.line_without_exp = re.sub(LineObject.exp_pattern2, "", self.line_without_exp)
        self.line_without_exp = re.sub(LineObject.exp_pattern3, "", self.line_without_exp)
        self.line_without_exp = self.line_without_exp.strip()

        self.is_empty = False
        if len(self.line_without_exp) == 0:
            self.is_empty = True

    @property
    def line_num(self):
        return self.line_idx + 1
    
    @property
    def line(self):
        return self.line_without_exp
    
    @property
    def ignore(self):
        return self.in_exp_block or self.is_empty

class Params(object):
    def __init__(self) -> None:
        self.input_file = ""
        self.output_func_file = "output_func.cpp"
        self.output_pb_file = "output_pb.proto"
        self.output_preprocess = False
        self.hide_exp_block = False
    

TYPE_MAP = {
    # 8 bit
    "char" : "int32",
    "unsigned char" : "uint32",
    "int8_t" : "int32",
    "uint8_t" : "uint32",
    "bool" : "bool",
    # 16 bit
    "short" : "int32",
    "unsigned short" : "uint32",
    "int16_t" : "int32",
    "uint16_t" : "uint32",
    # 32 bit
    "int" : "int32",
    "unsigned int" : "uint32",
    "unsigned" : "uint32",
    "int32_t" : "int32",
    "uint32_t" : "uint32",
    "long" : "int32",
    "unsigned long": "uint32",
    "float" : "float",
    # 64 bit
    "long long" : "int64",
    "unsigned long long" : "uint64",
    "int64_t" : "int64",
    "uint64_t" : "uint64",
    "double" : "double",
    # other
    "string" : "string",
}

ignore_member_name = ["szReverse", "reverse"]

TYPE_NOT_FOUND_PREFIX = ">>>>>"
type_map_user_defined = dict()

class_pattern = re.compile(r'(typedef)?\s*(?:class|struct)\s*([^\s{]*)\s*({)?')

# 函数实现
func_pattern = re.compile(r'([^\s{]+)\s*\(.*\).*({)?.*(})?\s*$')
full_func_pattern = re.compile(r'\(.*\).*{.*}\s*$')
half_func_pattern = re.compile(r'\(.*\).*{(?!.*})')
start_func_patter = re.compile(r'^\s*{\s*$')
end_func_patter = re.compile(r'^\s*}\s*$')

def findNextMemberVar(cpp_lines:List[LineObject], start_line_idx, end_line_idx) -> int:
    '''
        return
            -1 在范围内没有成员变量了
            >0 成员变量所在行index
    '''
    cur_line_idx = start_line_idx
    member_line_idx = -1

    in_func = False
    has_start = False
    cur_func_name = ""

    brace_stack = 0
    # TODO 暂时认为结构体中除了成员变量外只有成员函数
    # TODO 暂时认为函数中没有嵌套类、嵌套函数
    while cur_line_idx < end_line_idx:
        lineObj:LineObject = cpp_lines[cur_line_idx]
        if lineObj.ignore: 
            cur_line_idx += 1 
            continue
        if not in_func:
            m = re.search(func_pattern, lineObj.line)
            if not m:
                member_line_idx = cur_line_idx
                break
            cur_func_name = m.group(1)
            logging.debug("line num {}, func match: {}".format(lineObj.line_num, m.groups()))
            m = re.search(full_func_pattern, lineObj.line)
            if m:
                logging.info("skip func: [{}] -> line num [{}], [{}]".format(cur_func_name, lineObj.line_num, lineObj.line))
                cur_line_idx += 1
                continue
            in_func = True
            m = re.search(half_func_pattern, lineObj.line)
            if m:
                has_start = True
                brace_stack = 1
            cur_line_idx += 1
            continue

        if not has_start:
            m = re.match(start_func_patter, lineObj.line)
            if m:
                has_start = True
                brace_stack = 1
                l = re.findall(r'[{}]', lineObj.line)
                for b in l[1:]: # 第一个必然是左大括号，忽略
                    if b == '{': brace_stack += 1
                    elif b == '}': brace_stack -= 1
                if brace_stack == 0:
                    has_start = False
                    in_func = False
                    logging.info("skip func: [{}] -> line num [{}], [{}]".format(cur_func_name, lineObj.line_num, lineObj.line))
            else:
                logging.error("bad line [{}]:\n\t{}".format(lineObj.line_num, lineObj.line))

            cur_line_idx += 1
            continue
        
        l = re.findall(r'[{}]', lineObj.line)
        for b in l:
            if b == '{': brace_stack += 1
            elif b == '}': brace_stack -= 1
        if brace_stack == 0:
            has_start = False
            in_func = False
            logging.info("skip func: [{}] -> line num [{}], [{}]".format(cur_func_name, lineObj.line_num, lineObj.line))

        #m = re.match(end_func_patter, lineObj.line)
        #if m:
        #    has_start = False
        #    in_func = False
        #    logging.info("skip func: [{}] -> end line num[{}]".format(cur_func_name, lineObj.line_num))
        cur_line_idx += 1

    if in_func:
        logging.error("incomplete func [{}], has_start[{}]".format(cur_func_name, has_start))
    return member_line_idx

array_pattern = re.compile(r'\[\w+\]\s*;')
array_len_pattern = re.compile(r'(?<=\[)\w+(?=\])')
member_pattern = re.compile(r'^(.*)\s+(\w+)\s*;')
member_with_arr_pattern = re.compile(r'^(.*)\s+(\w+)\s*(?:\[\w+\])+\s*;')

def class2proto(cpp_lines:List[LineObject], user_class:UserClass, cpp_namespace="", pb_namespace="", cpp_object_placeholder="##cpp##", pb_object_placeholder="##pb##"):
    '''
        把一个class生成对应的proto文件
        对一个class中的所有字段生成两个语句: cpp object赋值到pb object, 以及反过来
        共生成一个proto message、一个set函数和一个get函数
    '''
    class_name = user_class.name
    proto_message = 'message ' + class_name + '{\n'
    cpp_class = cpp_namespace + "::" + class_name
    pb_class = pb_namespace +  "::" + class_name
    set_func = 'void set_pb_func_{}(const {} &{}, {} &{}) {{\n'.format(class_name, cpp_class, cpp_object_placeholder, pb_class, pb_object_placeholder)
    get_func = 'void get_pb_func_{}({} &{}, const {} &{}) {{\n'.format(class_name, cpp_class, cpp_object_placeholder, pb_class, pb_object_placeholder)
    
    cur_line_idx = user_class.start_idx
    end_line_idx = user_class.start_idx + user_class.line_num

    member_num = 0
    is_array = False
    arr_len_list:list
    while cur_line_idx < end_line_idx:
        member_line_idx = findNextMemberVar(cpp_lines, cur_line_idx, end_line_idx)
        if member_line_idx < 0 : break

        member_num += 1

        lineObj:LineObject = cpp_lines[member_line_idx]
        line_num = member_line_idx + 1 # 行号
        cur_line_idx = member_line_idx + 1

        proto_type = ""
        # 先检测数组及数组维度
        m = re.search(array_pattern, lineObj.line)
        if m:
            is_array = True
            arr_len_list = re.findall(array_len_pattern, lineObj.line)
            arr_dimen_cnt = len(arr_len_list)
            if arr_dimen_cnt == 0:
                logging.error("ignore invalid array line {}:\n\t{}".format(line_num, lineObj.line))
                proto_message += "\t// {} = {}\n".format(lineObj.line, member_num)
                set_func += "\t// {} = {}\n".format(lineObj.line, line_num)
                get_func += "\t// {} = {}\n".format(lineObj.line, line_num)
                continue
        else:
            is_array = False

        # 使用正则表达式匹配变量类型
        if not is_array:
            m = re.match(member_pattern, lineObj.line)
        else:
            m = re.match(member_with_arr_pattern, lineObj.line)
        if m:
            origin_type = re.sub(r'(mutable|struct)', '', m.group(1)).strip() # 忽略可能的无效类型前缀
            member_name = m.group(2)
            if member_name in ignore_member_name:
                logging.error("ignore specified member [{}] -> [{}:{}]".format(member_name, line_num, lineObj.line))
                continue
            
            origin_type = origin_type.split(':')[-1] # 忽略namespace
            trans_type = TYPE_MAP.get(origin_type)
            if trans_type is None:
                user_trans_type : UserClass = type_map_user_defined.get(origin_type)
                if user_trans_type is None:
                    logging.error("bad line {}, no trans type:\n\t{} -> [{}]".format(line_num, lineObj.line, origin_type))
                    proto_type += TYPE_NOT_FOUND_PREFIX + origin_type
                else:
                    proto_type += user_trans_type.name
            else:
                proto_type += trans_type

            # 拼接字段定义
            if not is_array:
                logging.debug(str(line_num) + " : " + origin_type + " -> " + (trans_type if trans_type is not None else "none"))
                proto_message += "\toptional {} {} = {};\n".format(proto_type, member_name, member_num)
                if trans_type is not None:
                    set_func += "\t{}.set_{}({}.{});\n".format(pb_object_placeholder, member_name.lower(), cpp_object_placeholder, member_name)
                    get_func += "\t{}.{} = {}.{}();\n".format(cpp_object_placeholder, member_name, pb_object_placeholder, member_name.lower())
                elif user_trans_type is not None:
                    set_func += "\tset_pb_func_{}({}.{}, *({}.mutable_{}()));\n".format(user_trans_type.name, cpp_object_placeholder, member_name, pb_object_placeholder, member_name.lower())
                    get_func += "\tget_pb_func_{}({}.{}, {}.{}());\n".format(user_trans_type.name, cpp_object_placeholder, member_name, pb_object_placeholder, member_name.lower())
                else: # 没匹配到类型，由使用者处理
                    set_func += TYPE_NOT_FOUND_PREFIX + "{}\n".format(lineObj.line)
                    get_func += TYPE_NOT_FOUND_PREFIX + "{}\n".format(lineObj.line)
            else:
                logging.debug(str(line_num) + " : " + origin_type + " -> " + (trans_type if trans_type is not None else "none"))
                proto_message += "\trepeated {} {} = {}; // ".format(proto_type, member_name, member_num)
                total_element_cnt_str = ""
                idx = 0
                while idx < arr_dimen_cnt:
                    arr_len = arr_len_list[idx]
                    if idx == (arr_dimen_cnt - 1):
                        total_element_cnt_str += str(arr_len)
                    else:
                        total_element_cnt_str += str(arr_len) + ' * '
                    idx += 1
                proto_message += total_element_cnt_str + "\n"
                # TODO 也许可以提供一个获取数组真实长度的方法，避免稀疏矩阵过大
                set_func += "\tfor (int i = 0; i < ({}); ++i) {{\n".format(total_element_cnt_str)
                get_func += "\tfor (int i = 0; i < {}.{}_size(); ++i) {{\n".format(pb_object_placeholder, member_name.lower())
                if trans_type is not None: # 原生类型，直接set
                    set_func += "\t\t{}.add_{}((({}*){}.{})[i]);\n\t}}\n".format(\
                        pb_object_placeholder, member_name.lower(), origin_type, cpp_object_placeholder, member_name)
                    get_func += "\t\t(({}*){}.{})[i] = {}.{}(i);\n\t}}\n".format(\
                        origin_type, cpp_object_placeholder, member_name, pb_object_placeholder, member_name.lower())
                elif user_trans_type is not None: # 复合类型，使用本脚本生成的set_pb_func函数赋值
                    set_func += "\t\tset_pb_func_{}((({}*){}.{})[i], *({}.add_{}()));\n\t}}\n".format(\
                        user_trans_type.name, user_trans_type.name, cpp_object_placeholder, member_name, pb_object_placeholder, member_name.lower())
                    get_func += "\t\tget_pb_func_{}((({}*){}.{})[i], {}.{}(i));\n\t}}\n".format(\
                        user_trans_type.name, user_trans_type.name, cpp_object_placeholder, member_name, pb_object_placeholder, member_name.lower())
                else:
                    set_func += TYPE_NOT_FOUND_PREFIX + "break; -> {}\n\t}}\n".format(lineObj.line)
                    get_func += TYPE_NOT_FOUND_PREFIX + "break; -> {}\n\t}}\n".format(lineObj.line)
        else :
            logging.error("bad line {} is_array[{}]:\n\t{}".format(line_num, is_array, lineObj.line))
    # 拼接message结束符
    proto_message += '}\n'
    set_func += '}\n'
    get_func += '}\n'

    return proto_message, set_func, get_func

def extractClass(cpp_lines:List[LineObject]):
    '''
        分析整个文件,提取出全部class/struct和对应的代码行数范围
    '''
    in_class = False
    has_start = False
    is_typedef = False
    line_idx = -1
    class_start_line_idx = 0
    for lineObj in cpp_lines:
        line_idx += 1
        if lineObj.ignore: continue
        # 不支持嵌套类
        # try find class
        if not in_class:
            m = re.search(class_pattern, lineObj.line)
            if m:
                logging.info("line num {} class match, {} -> {}".format(line_idx + 1, lineObj.line, m.groups()))
                is_typedef = True if m.group(1) is not None else False
                cur_class_name = m.group(2)
                in_class = True
                if m.group(3) is not None:
                    has_start = True
                    class_start_line_idx = line_idx + 1
                else:
                    has_start = False
            continue
        # try find class start
        if in_class and not has_start:
            m = re.match(r'^\s*{', lineObj.line)
            if not m:
                logging.error("{{ not followed by class definition, line num{}".format(line_idx + 1))
            else:
                has_start = True
                class_start_line_idx = line_idx + 1
            continue
        # try class end
        if in_class and has_start:
            if is_typedef:
                m = re.match(r'^\s*}\s*([\w_]*)\s*.*;', lineObj.line) # 这个分号很重要，用于区分class定义和函数定义
            else:
                m = re.match(r'^\s*}.*;', lineObj.line) # 这个分号很重要，用于区分class定义和函数定义
            if m:
                in_class = False
                has_start = False

                if is_typedef and len(m.group(1)) > 0 : cur_class_name = m.group(1)
                is_typedef = False

                c = UserClass(cur_class_name, class_start_line_idx, line_idx - class_start_line_idx)
                type_map_user_defined[cur_class_name] = c
                logging.info("get class: {} -> {} : {}".format(c.name, c.start_idx, c.line_num))
                class_start_line_idx = 0
                
    
    logging.info("found {} classes, {}\n".format(len(type_map_user_defined), type_map_user_defined))

block_exp_start_pattern = re.compile(r'([^\s/]*)\s*/\*')
block_exp_end_pattern = re.compile(r'\*/\s*([^\s/]*)')
full_block_exp_pattern = re.compile(r'/\*.*\*/')

def preProcessCppLines(cpp_lines:List[str]) -> List[LineObject]:
    '''
        对raw text做预处理,去掉每一行的行内注释部分(以//开头);解析注释块(/* */),记录是否需要忽略整行;是否为空行、是否需要忽略
    '''
    the_list:List[LineObject] = list()
    line_idx = -1
    in_exp_block = False
    for line in cpp_lines:
        line_idx += 1
        if not in_exp_block:
            m = re.search(block_exp_start_pattern, line)
            if not m: # 普通的一行
                the_list.append(LineObject(line, line_idx, False))
            else:
                # 看看/*之前有没有非注释部分。没有的话则此行开始进入注释块部分
                if m.group(1) is None or len(m.group(1)) == 0:
                    the_list.append(LineObject(line, line_idx, True))
                else:
                    the_list.append(LineObject(line, line_idx, False))
                # 看看注释是不是只有这一行
                if re.search(full_block_exp_pattern, line):
                    in_exp_block = False
                else:
                    in_exp_block = True
            continue
        else: # 已进入注释块
            m = re.search(block_exp_end_pattern, line)
            if not m: # 被注释掉的一行
                the_list.append(LineObject(line, line_idx, True))
            else:
                in_exp_block = False
                if len(m.group(1)) == 0: # 后面非空非注释部分的长度为0，即整行都是注释
                    the_list.append(LineObject(line, line_idx, True))
                else: # 注释结束后有可用内容 TODO 暂时不考虑注释块结束后，又新增注释块
                    the_list.append(LineObject(line, line_idx, False))
            continue
    
    return the_list
        

def cpp2proto(cpp_lines, out_cpp_file, out_proto_file, params:Params):
    logging.info("Now pre-process the cpp lines...")
    cpp_lines_object = preProcessCppLines(cpp_lines)

    if params.output_preprocess:
        output_preprocess_file = params.input_file + ".ii"
        with open(output_preprocess_file, mode='w') as out_lines:
            for lineObj in cpp_lines_object:
                if not params.hide_exp_block:
                    if lineObj.in_exp_block:
                        out_lines.write("[{}:{}] {}\n".format(lineObj.in_exp_block, lineObj.ignore, lineObj.strip_line))
                    else:
                        out_lines.write("[{}:{}] {}\n".format(lineObj.in_exp_block, lineObj.ignore, lineObj.line))
                else:
                    out_lines.write("[{}:{}] {}\n".format(lineObj.in_exp_block, lineObj.ignore, lineObj.line))

    logging.info(">>>>>>>>>>>>>>>>>>>>>>>")
    logging.info(">>>>>>>>>>>>>>>>>>>>>>> Now extract class or struct...")
    logging.info(">>>>>>>>>>>>>>>>>>>>>>>")
    extractClass(cpp_lines_object)
    
    if len(type_map_user_defined) == 0:
        logging.error("No class or struct found!")
        return

    logging.info(">>>>>>>>>>>>>>>>>>>>>>>")
    logging.info(">>>>>>>>>>>>>>>>>>>>>>> Now generate the pb file and func file...")
    logging.info(">>>>>>>>>>>>>>>>>>>>>>>")
    for userClass in type_map_user_defined.values():
        logging.info(userClass)
        proto, set_func, get_func = class2proto(cpp_lines_object, userClass, "", "test_namespace::test", "cppObj", "pbObj")
        #logging.info(proto)
        #logging.info(set_func)
        #logging.info(get_func)
        out_proto_file.writelines(proto)
        out_cpp_file.writelines(set_func)
        out_cpp_file.writelines(get_func)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    params = Params()

    opts, _ = getopt.getopt(sys.argv[1:], "f:c:p:E", ["hide-exp-block"])
    for opt, v in opts:
        if opt == '-f':
            params.input_file = v
        elif opt == '-c':
            params.output_func_file = v
        elif opt == '-p':
            params.output_pb_file = v
        elif opt == '-E': # 输出预处理结果
            params.output_preprocess = True
        elif opt == "--hide-exp-block": # 使用-E输出预处理结果的时候，是否隐藏注释块的内容
            params.hide_exp_block = True
    
    logging.basicConfig(format='[%(levelname)s][%(funcName)s:%(lineno)d] %(message)s', level=logging.ERROR)

    try:
        start_time = time.time()
        with open(params.input_file, mode='r') as cpp_file, open(params.output_func_file, mode='w') as func_file, open(params.output_pb_file, mode='w') as proto_file :
            ret = cpp2proto(cpp_file.readlines(), func_file, proto_file, params)
        
    except FileNotFoundError as e:
        logging.error(e)

    finally:
        end_time = time.time()
        logging.info("End, cost %fs"%(end_time - start_time))
