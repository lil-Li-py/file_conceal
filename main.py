import base64
import os
import random
import struct
import tempfile
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


MAGIC = b"FCNL"
NAME_SIZE = 4
DATA_SIZE = 8
HEADER_SIZE = len(MAGIC) + NAME_SIZE + DATA_SIZE
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
JPEG_SOI = b"\xff\xd8"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
GIF87A_SIGNATURE = b"GIF87a"
GIF89A_SIGNATURE = b"GIF89a"
BMP_SIGNATURE = b"BM"
RIFF_SIGNATURE = b"RIFF"
WEBP_SIGNATURE = b"WEBP"

BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
SEED_LENGTH = 128
PACKAGE_SEPARATOR = "caicaiwoshishenme"


@dataclass(frozen=True)
class MagicBase64Package:
    """保存一次编码后的载荷，以及对应的种子和字母表信息。"""
    seed: str
    alphabet: str
    encoded_text: str

    def as_tuple(self) -> Tuple[str, str]:
        """以元组形式返回种子和编码文本，便于调用方分别使用。"""
        return self.seed, self.encoded_text

    def as_payload(self) -> str:
        """将数据包序列化为隐藏分块中使用的文本格式。"""
        return f"{self.seed}{PACKAGE_SEPARATOR}{self.encoded_text}"


class MagicBase64:
    """基于种子生成的乱序字母表，提供自定义 Base64 编解码能力。"""
    def __init__(self, seed: Optional[str] = None):
        """使用现有种子或新生成的种子初始化编解码器。"""
        self.seed = seed or self.generate_seed()
        self.alphabet = self.build_alphabet(self.seed)
        self._encode_table, self._decode_table = self._build_translate_tables(self.alphabet)

    @staticmethod
    def generate_seed(length: int = SEED_LENGTH) -> str:
        """生成用于打乱 Base64 字母表的随机种子字符串。"""
        secure_random = random.SystemRandom()
        return "".join(secure_random.choice(BASE64_ALPHABET) for _ in range(length))

    @staticmethod
    def build_alphabet(seed: str) -> str:
        """根据给定种子构造可复现的自定义字母表。"""
        rng = random.Random()
        rng.seed(seed)
        chars = list(BASE64_ALPHABET)
        rng.shuffle(chars)
        return "".join(chars)

    @staticmethod
    def _build_translate_tables(custom_alphabet: str):
        """创建标准 Base64 与自定义字母表之间的转换表。"""
        if len(custom_alphabet) != len(BASE64_ALPHABET):
            raise ValueError("自定义字符表长度必须为 64。")
        if len(set(custom_alphabet)) != len(custom_alphabet):
            raise ValueError("自定义字符表中存在重复字符。")

        encode_table = str.maketrans(BASE64_ALPHABET, custom_alphabet)
        decode_table = str.maketrans(custom_alphabet, BASE64_ALPHABET)
        return encode_table, decode_table

    def encode(self, data: bytes) -> str:
        """将原始字节编码为使用自定义字母表的 Base64 文本。"""
        standard_text = base64.b64encode(data).decode("ascii")
        return standard_text.translate(self._encode_table)

    def decode(self, encoded_text: str) -> bytes:
        """将自定义字母表的 Base64 文本还原为原始字节。"""
        standard_text = encoded_text.translate(self._decode_table)
        return base64.b64decode(standard_text.encode("ascii"))

    def pack(self, data: bytes) -> MagicBase64Package:
        """编码字节内容，并以结构化数据包对象返回结果。"""
        return MagicBase64Package(
            seed=self.seed,
            alphabet=self.alphabet,
            encoded_text=self.encode(data),
        )

    @classmethod
    def from_seed(cls, seed: str) -> "MagicBase64":
        """根据已有种子重建编解码器，用于解码同源数据。"""
        return cls(seed=seed)

    @classmethod
    def encode_bytes(cls, data: bytes, seed: Optional[str] = None) -> MagicBase64Package:
        """便捷方法：编码字节并返回完整数据包。"""
        codec = cls(seed=seed)
        return codec.pack(data)

    @classmethod
    def encode_parts(cls, data: bytes, seed: Optional[str] = None) -> Tuple[str, str]:
        """编码字节，并分别返回种子和编码文本。"""
        package = cls.encode_bytes(data, seed=seed)
        return package.as_tuple()

    @classmethod
    def encode_payload(cls, data: bytes, seed: Optional[str] = None) -> str:
        """将字节编码为隐藏文件分块中保存的文本载荷格式。"""
        # 这里的载荷格式必须与 decode_payload() 保持一致。
        package = cls.encode_bytes(data, seed=seed)
        return package.as_payload()

    @classmethod
    def decode_text(cls, encoded_text: str, seed: str) -> bytes:
        """使用给定种子重建字母表，并解码对应的文本内容。"""
        codec = cls.from_seed(seed)
        return codec.decode(encoded_text)

    @classmethod
    def decode_payload(cls, payload_text: str) -> bytes:
        """解析序列化后的载荷格式，并恢复出原始字节内容。"""
        if len(payload_text) <= SEED_LENGTH:
            raise ValueError("密文格式无效，缺少编码内容。")
        # 分隔符长度可变，因此校验和切片都必须使用完整长度。
        separator_end = SEED_LENGTH + len(PACKAGE_SEPARATOR)
        if payload_text[SEED_LENGTH:separator_end] != PACKAGE_SEPARATOR:
            raise ValueError("密文格式无效，缺少分隔符。")

        seed = payload_text[:SEED_LENGTH]
        encoded_text = payload_text[separator_end:]
        return cls.decode_text(encoded_text, seed)


@dataclass(frozen=True)
class HiddenFileChunk:
    """表示从图片中解析出的单个隐藏文件条目。"""
    file_name: str
    payload: bytes


class FileConcealService:
    """负责文件隐藏、提取以及图片清洗的核心服务。"""
    @staticmethod
    def detect_image_suffix(file_path: str):
        """通过文件头判断真实图片类型，并返回标准化后的后缀名。"""
        with open(file_path, "rb") as image_file:
            head = image_file.read(16)

        if head.startswith(PNG_SIGNATURE):
            return ".png"
        if head.startswith(JPEG_SOI):
            return ".jpg"
        if head.startswith(GIF87A_SIGNATURE) or head.startswith(GIF89A_SIGNATURE):
            return ".gif"
        if head.startswith(BMP_SIGNATURE):
            return ".bmp"
        if head.startswith(RIFF_SIGNATURE) and head[8:12] == WEBP_SIGNATURE:
            return ".webp"
        return None

    def validate_prototype_image(self, prototype_file: str) -> str:
        """校验载体图片是否合法，并返回从文件内容识别出的真实后缀。"""
        detected_suffix = self.detect_image_suffix(prototype_file)
        if detected_suffix is None:
            raise ValueError("不支持的原图格式。")

        file_suffix = os.path.splitext(prototype_file)[1].lower()
        if file_suffix and file_suffix not in SUPPORTED_IMAGE_SUFFIXES:
            raise ValueError("原图扩展名不在支持范围内。")

        return detected_suffix

    @staticmethod
    def iter_target_paths(target_files: str) -> Iterable[str]:
        """从单个文件或单层目录中产出需要隐藏的文件路径。"""
        if os.path.isdir(target_files):
            for entry in os.scandir(target_files):
                if entry.is_file():
                    yield entry.path
            return

        if os.path.isfile(target_files):
            yield target_files
            return

        raise FileNotFoundError(f"目标路径不存在: {target_files}")

    @staticmethod
    def safe_output_name(raw_name: bytes) -> str:
        """在写入磁盘前解码并清洗隐藏文件名，避免非法路径。"""
        decoded = MagicBase64.decode_payload(raw_name.decode("utf-8", errors="strict")).decode("utf-8")
        safe_name = os.path.basename(decoded)
        if not safe_name or safe_name in {".", ".."}:
            raise ValueError("隐藏文件名无效。")
        return safe_name

    @staticmethod
    def ensure_output_path_available(output_path: str, allow_same_path_replace: bool = False):
        """除非明确允许替换，否则阻止覆盖已有文件。"""
        if os.path.exists(output_path) and not allow_same_path_replace:
            raise FileExistsError(f"输出文件已存在: {output_path}")

    def suggest_encrypt_output_name(self, prototype_file: str, out_file_name: str) -> Tuple[str, str]:
        """为隐藏输出生成可用文件名，重名时自动追加 _1、_2 等后缀。"""
        prototype_suffix = self.validate_prototype_image(prototype_file)
        output_dir = os.path.dirname(prototype_file)
        output_path = os.path.join(output_dir, f"{out_file_name}{prototype_suffix}")

        if not os.path.exists(output_path):
            return out_file_name, output_path

        index = 1
        while True:
            candidate_name = f"{out_file_name}_{index}"
            candidate_path = os.path.join(output_dir, f"{candidate_name}{prototype_suffix}")
            if not os.path.exists(candidate_path):
                return candidate_name, candidate_path
            index += 1

    def build_encrypt_output_path(self, prototype_file: str, out_file_name: str) -> str:
        """根据图片真实格式构建隐藏输出路径。"""
        prototype_suffix = self.validate_prototype_image(prototype_file)
        return os.path.join(os.path.dirname(prototype_file), f"{out_file_name}{prototype_suffix}")

    @staticmethod
    def build_encoded_chunk(file_path: str) -> bytes:
        """读取一个源文件，并封装成追加到图片末尾的二进制分块。"""
        file_name = MagicBase64.encode_payload(os.path.basename(file_path).encode("utf-8")).encode("utf-8")
        with open(file_path, "rb") as source:
            payload = source.read()

        encoded_payload = MagicBase64.encode_payload(payload).encode("utf-8")
        return b"".join(
            (
                MAGIC,
                struct.pack(">I", len(file_name)),
                struct.pack(">Q", len(encoded_payload)),
                file_name,
                encoded_payload,
            )
        )

    @staticmethod
    def iter_chunks(blob: bytes):
        """遍历图片字节流中所有可识别的隐藏数据分块。"""
        cursor = 0
        blob_length = len(blob)

        while True:
            marker_index = blob.find(MAGIC, cursor)
            if marker_index < 0:
                return

            if marker_index + HEADER_SIZE > blob_length:
                return

            header_start = marker_index + len(MAGIC)
            name_length = struct.unpack(">I", blob[header_start:header_start + NAME_SIZE])[0]
            data_length_start = header_start + NAME_SIZE
            data_length = struct.unpack(">Q", blob[data_length_start:data_length_start + DATA_SIZE])[0]

            name_start = data_length_start + DATA_SIZE
            name_end = name_start + name_length
            data_end = name_end + data_length
            if data_end > blob_length:
                return

            raw_name = blob[name_start:name_end]
            payload = blob[name_end:data_end]
            yield marker_index, data_end, raw_name, payload
            cursor = data_end

    def parse_hidden_files(self, blob: bytes) -> List[HiddenFileChunk]:
        """解析字节流中的所有有效隐藏分块，得到文件名和内容对象。"""
        hidden_files = []
        for _, _, raw_name, encoded_payload in self.iter_chunks(blob):
            file_name = self.safe_output_name(raw_name)
            payload = MagicBase64.decode_payload(encoded_payload.decode("utf-8"))
            hidden_files.append(HiddenFileChunk(file_name=file_name, payload=payload))
        return hidden_files

    def encrypt(self, prototype_file: str, target_files: str, out_file_name: str = "result", is_remove: bool = False):
        """将编码后的文件追加到载体图片中，并按需删除源文件。"""
        prototype_suffix = self.validate_prototype_image(prototype_file)
        output_path = os.path.join(os.path.dirname(prototype_file), f"{out_file_name}{prototype_suffix}")
        same_as_prototype = os.path.abspath(output_path) == os.path.abspath(prototype_file)
        if same_as_prototype and not is_remove:
            raise ValueError("输出文件不能与原图同名，请修改输出文件名。")

        self.ensure_output_path_available(output_path, allow_same_path_replace=same_as_prototype and is_remove)
        embedded_paths = list(self.iter_target_paths(target_files))

        temp_output_path = None
        actual_output_path = output_path
        if same_as_prototype:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=prototype_suffix, dir=os.path.dirname(prototype_file))
            temp_output_path = temp_file.name
            temp_file.close()
            actual_output_path = temp_output_path

        try:
            with open(actual_output_path, "wb") as output_file, open(prototype_file, "rb") as prototype:
                output_file.write(prototype.read())
                for file_path in embedded_paths:
                    output_file.write(self.build_encoded_chunk(file_path))

            if same_as_prototype:
                os.remove(prototype_file)
                os.replace(actual_output_path, output_path)
        except Exception:
            if temp_output_path and os.path.exists(temp_output_path):
                os.remove(temp_output_path)
            raise

        if is_remove:
            for file_path in embedded_paths:
                os.remove(file_path)

    def decrypt(self, target_file: str, is_all: int = 0) -> bool:
        """从图片中提取隐藏文件，并输出到同级的 result 目录。"""
        self.validate_prototype_image(target_file)
        out_path = os.path.join(os.path.dirname(target_file), "my_result")

        with open(target_file, "rb") as target:
            hidden_files = self.parse_hidden_files(target.read())

        if not hidden_files:
            return False

        if is_all <= 0 or is_all > len(hidden_files):
            is_all = len(hidden_files)

        os.makedirs(out_path, exist_ok=True)
        for hidden_file in hidden_files[:is_all]:
            output_file = os.path.join(out_path, hidden_file.file_name)
            self.ensure_output_path_available(output_file)
            with open(output_file, "wb") as file_obj:
                file_obj.write(hidden_file.payload)
        return True

    def wash(self, target_file: str) -> bool:
        """移除图片中的隐藏分块，同时保留原始可见图片数据。"""
        self.validate_prototype_image(target_file)
        with open(target_file, "rb") as target:
            blob = target.read()

        chunks = list(self.iter_chunks(blob))
        if not chunks:
            return False

        first_marker = chunks[0][0]
        with open(target_file, "wb") as target:
            target.write(blob[:first_marker])
        return True


service = FileConcealService()


def encrypt_main(prototype_file, target_files, out_file_name="result", is_remove=False):
    """为界面层提供简化的文件隐藏入口。"""
    service.encrypt(prototype_file, target_files, out_file_name=out_file_name, is_remove=is_remove)


def suggest_encrypt_output_name(prototype_file, out_file_name="result"):
    """为界面层提供隐藏输出文件名去重建议。"""
    return service.suggest_encrypt_output_name(prototype_file, out_file_name)


def build_encrypt_output_path(prototype_file, out_file_name="result"):
    """为界面层提供基于真实图片格式的隐藏输出路径。"""
    return service.build_encrypt_output_path(prototype_file, out_file_name)


def decrypt_main(target_file, is_all=0):
    """为界面层提供简化的文件提取入口。"""
    return service.decrypt(target_file, is_all=is_all)


def img_wash(target_file):
    """为界面层提供简化的图片清洗入口。"""
    return service.wash(target_file)


if __name__ == "__main__":
    img_wash("default.png")
