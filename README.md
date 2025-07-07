# yt-decrypt

A Python project that dynamically decrypts YouTube's signatureCipher by parsing the player JavaScript file.

## Features

- Dynamically fetches and parses YouTube's player JavaScript file
- Decrypts signatureCipher to retrieve direct video URLs
- Extracts and decrypts n-parameter for URL validation
- Uses actual JavaScript execution via Node.js for reliable decryption
- Designed to adapt to YouTube player changes
- Saves decrypted URLs and JavaScript decrypt functions to files

## Installation

```bash
git clone https://github.com/reddevil212/yt-decrypt.git
cd yt-decrypt
pip install -r requirements.txt
```

## Requirements

- Python 3.7+
- Node.js (required for JavaScript execution)
- requests library (see requirements.txt)

## Usage

### Basic Usage

```python
from standalone_decryptor import YouTubeDecryptor

# Create decryptor instance
decryptor = YouTubeDecryptor()

# Get video formats with decrypted URLs
video_id = "dQw4w9WgXcQ"
formats = decryptor.get_video_formats(video_id)

# Print available formats
for i, fmt in enumerate(formats):
    print(f"{i+1}. Quality: {fmt.get('qualityLabel')} | "
          f"Type: {fmt.get('mimeType')} | "
          f"URL: {fmt['url']}")
```

### Save URLs to File

```python
# Save all URLs to a text file
decryptor.save_urls_to_file(formats, "video_urls.txt")
```

### Manual Signature Decryption

```python
# For manual signature decryption
decrypted_signature = decryptor.decrypt_signature(signature)
decrypted_n_param = decryptor.decrypt_n_parameter(n_parameter)
```

### Command Line Usage

Run the standalone decryptor directly:

```bash
python standalone_decryptor.py
```

This will process a default video and save the results to `video_urls.txt` and `decrypt_script.js`.

## Project Structure

- `standalone_decryptor.py` - Main decryptor class with full YouTube decryption functionality
- `sig.py` - Signature extraction functions and JavaScript parsing
- `lib.py` - Library functions for extracting decode scripts
- `requirements.txt` - Python dependencies
- `LICENSE` - MIT License

## How It Works

1. **Fetch Player Code**: Downloads the latest YouTube player JavaScript file
2. **Extract Functions**: Parses the JavaScript to extract signature decryption and n-parameter transformation functions
3. **JavaScript Execution**: Uses Node.js to execute the extracted JavaScript functions
4. **URL Decryption**: Applies the decryption to signatureCipher parameters to get direct video URLs
5. **Format Processing**: Processes all available video formats and qualities

## Disclaimer

This project is for educational purposes only. Use responsibly and respect YouTube's Terms of Service. The authors are not responsible for any misuse of this software.

## License

[MIT](LICENSE)