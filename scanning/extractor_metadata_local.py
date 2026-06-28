import json
import os

from pathlib import Path
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3 as MutagenMP3
from mutagen.flac import FLAC as MutagenFLAC
from mutagen.id3 import USLT, SYLT
from dotenv import load_dotenv

AUDIO_EXTENSIONS = {".mp3", ".flac", ".aac", ".m4a", ".m4b", ".mp4", ".ogg", ".oga",
                    ".opus", ".wav", ".wave", ".wma", ".aif", ".aiff", ".ape", ".wv",
                    ".tta", ".mpc",
                    }
STREAM_INFO_FIELDS = ("length", "bitrate", "sample_rate", "channels", "bits_per_sample", "codec", "codec_description",)

load_dotenv()

def get_env_path(variable_name: str) -> Path:
    value = os.getenv(variable_name)

    if value is None:
        raise ValueError(f"Не найдена переменная окружения: {variable_name}")

    return Path(value)

ROOT_DIRECTORY = get_env_path("AUDIO_ROOT_DIRECTORY")
PATH_OUTPUT = get_env_path("METADATA_OUTPUT_PATH")

def get_paths_audio(root_directory: Path) -> list[Path]:
    """Функция находит аудиофайлы внутри каталога и вложенных каталогов."""

    audio_files = [path for path in root_directory.rglob("*") if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS]
    return sorted(audio_files)

def get_audio_lyrics(file_path: Path):
    """Функция извлекает текст песни если он присутствует."""

    lyrics = None

    if file_path.suffix.lower().endswith('.mp3'):
        try:
            audio = MutagenMP3(file_path)

            for tag in audio.tags.values():
                if isinstance(tag, USLT):
                    lyrics = tag.text
                    print("Найден несинхронизированный текст (USLT).")
                    break
                elif isinstance(tag, SYLT):
                    lyrics = "\n".join([text for _, text in tag.text])
                    print("Найден синхронизированный текст (SYLT).")
                    break
        except FileNotFoundError as ffe:
            print("Ошибка при чтении MP3:", ffe)

    elif file_path.suffix.lower().endswith('.flac'):
        try:
            audio = MutagenFLAC(file_path)

            for tag in audio.keys():
                if tag == 'lyrics' and audio['lyrics']:
                    lyrics = audio["lyrics"][0]

        except FileNotFoundError as ffe:
            print("Ошибка при чтении FLAC:", ffe)

    return lyrics

def get_audio_tag_basic(file_paths: list[Path]) -> dict | None:
    """Функция извлекает из файла набор мета-данныз в зависимости от формата."""

    row_audio_metadata = {}

    for track in file_paths:
        try:
            audio = MutagenFile(track, easy=True)

            if audio.tags is None:
                return None

        except Exception as e:
            print(f"Не удалось прочитать файл {track}: {e}")
            continue

        audio_tags = {
            'title': audio.get('title', None),
            'album': audio.get('album', None),
            'artist': audio.get('artist', [None]),
            'albumartist': audio.get('albumartist', [None]),
            'genre': audio.get('genre', [None]),
            'date': audio.get('date', None),
            'lyrics': get_audio_lyrics(track),
            'path_local': str(track),
        }

        row_audio_metadata[str(track)] = audio_tags

    return row_audio_metadata

def save_file(path, file_tags):
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(file_tags, file, ensure_ascii=False, indent=2)


def main():
    files = get_paths_audio(ROOT_DIRECTORY)
    metadata = get_audio_tag_basic(files)
    save_file(PATH_OUTPUT, metadata)


if __name__ == "__main__":
    main()