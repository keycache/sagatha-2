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


def get_files_with_prefix(folder_path, prefix):
    all_files = os.listdir(folder_path)
    matching_files = [os.path.join(folder_path, file) for file in all_files if file.startswith(prefix)]
    return matching_files


def get_filename(file_path):
    return os.path.basename(file_path)


if __name__ == "__main__":
    print(get_files_with_prefix(".data/stories/the-littlest-seed-of-kindness/assets/chapter-1", "narration"))
