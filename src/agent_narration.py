import subprocess


def generate_narration(
    text: str, output_path: str, voice: str = "af_sarah", speed: float = 1.2, lang: str = "en-us"
) -> None:
    NARRATION_EXECUTION_PATH = "/Users/akashpatki/Documents/kash/code/moon/tts/kokoro/.venv/bin/python"
    NARRATION_SCRIPT_PATH = "/Users/akashpatki/Documents/kash/code/moon/tts/kokoro/main.py"
    command = [
        NARRATION_EXECUTION_PATH,
        NARRATION_SCRIPT_PATH,
        "--sentence",
        text,
        "--voice",
        voice,
        "--speed",
        str(speed),
        "--lang",
        lang,
        "--target-path",
        output_path,
    ]

    # Run the command
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        print(f"Error generating narration: {result.stderr}")
    else:
        print(f"Narration generated successfully: {output_path}")
        return output_path
    return None


if __name__ == "__main__":
    text = "This is a test narration."
    output_path = ".data/narration/test_output.wav"
    generate_narration(text, output_path)
