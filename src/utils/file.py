import base64
import os


def make_directory(directory):
    os.makedirs(directory, exist_ok=True)
    return directory


def save_file(file_path, content, mode="w", encoding="utf-8"):
    with open(file_path, mode, encoding=(None if "b" in mode else encoding)) as file:
        file.write(content)
    return file_path


def read_file(file_path, mode="r", encoding="utf-8") -> str:
    with open(file_path, mode, encoding=encoding) as file:
        return file.read()


def read_file_as_base64(file_path, mode="rb", encoding="utf-8") -> str:  # type: ignore
    with open(file_path, mode) as image_file:
        image_binary = image_file.read()
        return base64.b64encode(image_binary).decode(encoding)


def get_files_with_prefix(folder_path, prefix):
    if not os.path.exists(folder_path):
        return []
    all_files = os.listdir(folder_path)
    matching_files = [os.path.join(folder_path, file) for file in all_files if file.startswith(prefix)]
    return matching_files


def get_file_paths_with_text(folder_path, suffix):
    if not os.path.exists(folder_path):
        return []
    all_files = os.listdir(folder_path)
    matching_files = [os.path.join(folder_path, file) for file in all_files if suffix in file]
    return matching_files


def get_filename(file_path):
    return os.path.basename(file_path)


if __name__ == "__main__":
    print(get_files_with_prefix(".data/stories/the-littlest-seed-of-kindness/assets/chapter-1", "narration"))
