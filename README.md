# yt-decrypt

A Python project that dynamically decrypts YouTube's `signatureCipher` by parsing the player JavaScript file.

---

## Features

- **Dynamic Decryption:** Automatically fetches and parses YouTube's player JavaScript to extract decryption logic.
- **No Hardcoding:** No need to manually update decryption algorithms when YouTube changes their player.
- **Pure Python:** No external dependencies other than standard Python libraries (unless specified below).
- **CLI Tool:** Easily decrypt YouTube video URLs or signatureCiphers directly from the command line.
- **Reusable Module:** Can be imported and used in other Python projects.

---

## Installation

```bash
git clone https://github.com/reddevil212/yt-decrypt.git
cd yt-decrypt
pip install -r requirements.txt
```

---

## Usage

### As a Command Line Tool

```bash
python standalone_decryptor.py <VIDEO_ID>
```

## Example

```bash
python yt_decrypt.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

---

## Requirements

- Python 3.7+
- `requests`
- (Other dependencies if specified in `requirements.txt`)

Install all requirements using:

```bash
pip install -r requirements.txt
```

---

## How It Works

1. Retrieves the JavaScript player file from YouTube.
2. Parses the file to extract the decryption algorithm.
3. Applies the decryption logic to the video signatureCipher or URL.

---

## Disclaimer

This project is for educational and research purposes only. Use responsibly and respect YouTube's Terms of Service.

---

## License

MIT License

---

## Contributing

Pull requests and suggestions are welcome! Please open an issue or submit a PR if you'd like to help.

---

## Author

- [reddevil212](https://github.com/reddevil212)

---

**Happy decrypting!**
