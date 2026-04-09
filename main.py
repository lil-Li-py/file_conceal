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
PACKAGE_SEPARATOR = ":"


@dataclass(frozen=True)
class MagicBase64Package:
    seed: str
    alphabet: str
    encoded_text: str

    def as_tuple(self) -> Tuple[str, str]:
        return self.seed, self.encoded_text

    def as_payload(self) -> str:
        return f"{self.seed}{PACKAGE_SEPARATOR}{self.encoded_text}"


class MagicBase64:
    def __init__(self, seed: Optional[str] = None):
        self.seed = seed or self.generate_seed()
        self.alphabet = self.build_alphabet(self.seed)
        self._encode_table, self._decode_table = self._build_translate_tables(self.alphabet)

    @staticmethod
    def generate_seed(length: int = SEED_LENGTH) -> str:
        secure_random = random.SystemRandom()
        return "".join(secure_random.choice(BASE64_ALPHABET) for _ in range(length))

    @staticmethod
    def build_alphabet(seed: str) -> str:
        rng = random.Random()
        rng.seed(seed)
        chars = list(BASE64_ALPHABET)
        rng.shuffle(chars)
        return "".join(chars)

    @staticmethod
    def _build_translate_tables(custom_alphabet: str):
        if len(custom_alphabet) != len(BASE64_ALPHABET):
            raise ValueError("自定义字符表长度必须为 64。")
        if len(set(custom_alphabet)) != len(custom_alphabet):
            raise ValueError("自定义字符表中存在重复字符。")

        encode_table = str.maketrans(BASE64_ALPHABET, custom_alphabet)
        decode_table = str.maketrans(custom_alphabet, BASE64_ALPHABET)
        return encode_table, decode_table

    def encode(self, data: bytes) -> str:
        standard_text = base64.b64encode(data).decode("ascii")
        return standard_text.translate(self._encode_table)

    def decode(self, encoded_text: str) -> bytes:
        standard_text = encoded_text.translate(self._decode_table)
        return base64.b64decode(standard_text.encode("ascii"))

    def pack(self, data: bytes) -> MagicBase64Package:
        return MagicBase64Package(
            seed=self.seed,
            alphabet=self.alphabet,
            encoded_text=self.encode(data),
        )

    @classmethod
    def from_seed(cls, seed: str) -> "MagicBase64":
        return cls(seed=seed)

    @classmethod
    def encode_bytes(cls, data: bytes, seed: Optional[str] = None) -> MagicBase64Package:
        codec = cls(seed=seed)
        return codec.pack(data)

    @classmethod
    def encode_parts(cls, data: bytes, seed: Optional[str] = None) -> Tuple[str, str]:
        package = cls.encode_bytes(data, seed=seed)
        return package.as_tuple()

    @classmethod
    def encode_payload(cls, data: bytes, seed: Optional[str] = None) -> str:
        package = cls.encode_bytes(data, seed=seed)
        return package.as_payload()

    @classmethod
    def decode_text(cls, encoded_text: str, seed: str) -> bytes:
        codec = cls.from_seed(seed)
        return codec.decode(encoded_text)

    @classmethod
    def decode_payload(cls, payload_text: str) -> bytes:
        if len(payload_text) <= SEED_LENGTH:
            raise ValueError("密文格式无效，缺少编码内容。")
        if payload_text[SEED_LENGTH:SEED_LENGTH + 1] != PACKAGE_SEPARATOR:
            raise ValueError("密文格式无效，缺少分隔符。")

        seed = payload_text[:SEED_LENGTH]
        encoded_text = payload_text[SEED_LENGTH + 1:]
        return cls.decode_text(encoded_text, seed)


@dataclass(frozen=True)
class HiddenFileChunk:
    file_name: str
    payload: bytes


class FileConcealService:
    @staticmethod
    def detect_image_suffix(file_path: str):
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
        detected_suffix = self.detect_image_suffix(prototype_file)
        if detected_suffix is None:
            raise ValueError("不支持的原图格式。")

        file_suffix = os.path.splitext(prototype_file)[1].lower()
        if file_suffix and file_suffix not in SUPPORTED_IMAGE_SUFFIXES:
            raise ValueError("原图扩展名不在支持范围内。")

        return detected_suffix

    @staticmethod
    def iter_target_paths(target_files: str) -> Iterable[str]:
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
        decoded = raw_name.decode("utf-8", errors="strict")
        safe_name = os.path.basename(decoded)
        if not safe_name or safe_name in {".", ".."}:
            raise ValueError("隐藏文件名无效。")
        return safe_name

    @staticmethod
    def ensure_output_path_available(output_path: str, allow_same_path_replace: bool = False):
        if os.path.exists(output_path) and not allow_same_path_replace:
            raise FileExistsError(f"输出文件已存在: {output_path}")

    @staticmethod
    def build_encoded_chunk(file_path: str) -> bytes:
        file_name = os.path.basename(file_path).encode("utf-8")
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
        hidden_files = []
        for _, _, raw_name, encoded_payload in self.iter_chunks(blob):
            file_name = self.safe_output_name(raw_name)
            payload = MagicBase64.decode_payload(encoded_payload.decode("utf-8"))
            hidden_files.append(HiddenFileChunk(file_name=file_name, payload=payload))
        return hidden_files

    def encrypt(self, prototype_file: str, target_files: str, out_file_name: str = "result", is_remove: bool = False):
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
        self.validate_prototype_image(target_file)
        out_path = os.path.join(os.path.dirname(target_file), "result")

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
    service.encrypt(prototype_file, target_files, out_file_name=out_file_name, is_remove=is_remove)


def decrypt_main(target_file, is_all=0):
    return service.decrypt(target_file, is_all=is_all)


def img_wash(target_file):
    return service.wash(target_file)


if __name__ == "__main__":
    img_wash("default.png")
