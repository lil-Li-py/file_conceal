import os
import re


def encrypt_main(prototype_file, target_files, out_file_name='default', is_remove=False):
    """
    隐藏文件专用
    :param prototype_file: 原型文件
    :param target_files: 待隐藏的文件族, 可为单文件或单层文件夹
    :param out_file_name: 输出的文件名
    :param is_remove: 是否删除待隐藏的文件
    :return:
    """
    with open(f"{out_file_name}.png", 'wb') as o, open(prototype_file, 'rb') as p:
        o.write(p.read())
        if os.path.isdir(target_files):
            for target_file in os.listdir(target_files):
                # 获取待隐藏的文件的文件名
                name = os.path.basename(target_file)
                path = os.path.join(target_files, target_file)
                with open(path, 'rb') as t:
                    o.write(f" start{name}|".encode('utf-8') + t.read() + b"end")
            if is_remove:
                for target_file in target_files:
                    os.remove(target_file)
        else:
            # 获取待隐藏的文件的文件名
            name = os.path.basename(target_files)
            with open(target_files, 'rb') as t:
                o.write(f" start{name}|".encode('utf-8') + t.read() + b"end")
            if is_remove:
                os.remove(target_files)


def decrypt_main(target_file, is_all=0):
    """
    解构隐藏的文件
    :param target_file: 目标解构文件
    :param is_all: 默认为所有的文件, 可设置解构的文件个数, 当设置个数大于总个数时，为全部
    :return:
    """
    out_path = os.path.join(os.path.splitext(target_file)[0], "out")
    os.makedirs(out_path, exist_ok=True)
    pattern = re.compile(br"start(.*?)end", re.S)
    with open(target_file, 'rb') as t:
        datas = pattern.findall(t.read())
        if not datas:
            return False
        if is_all > len(datas) or not is_all:
            is_all = len(datas)
        for data in datas[:is_all]:
            name = re.match(br"(.*?)\|", data).group(1)
            name = os.path.join(out_path, name.decode())
            with open(name, 'wb') as f:
                f.write(re.findall(br"\|(.*)", data, re.S)[0])
    return True


def img_wash(target_file):
    with open(target_file, 'rb') as t:
        data = re.match(br"(.*?)start", t.read(), re.S)
    if data:
        with open(target_file, 'wb') as t:
            t.write(data.group()[:-6])
        return True
    return False


if __name__ == '__main__':
    # encrypt_main("prototype.png", "preview.gif", is_remove=False)
    # decrypt_main("default.png")
    img_wash("default.png")
