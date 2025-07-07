import subprocess
import tempfile
import os
import json
import logging
import requests
import re
import urllib.parse
from typing import Dict, List, Optional, Tuple
from lib import extract_decode_script_simple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JavaScriptExecutor:
    """Helper class to execute JavaScript code using Node.js"""
    
    def __init__(self):
        self.node_available = self._check_node_available()
    
    def _check_node_available(self) -> bool:
        """Check if Node.js is available"""
        try:
            subprocess.run(['node', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def execute_js(self, js_code: str, timeout: int = 30) -> str:
        """Execute JavaScript code and return the result"""
        if not self.node_available:
            raise RuntimeError("Node.js is not available. Please install Node.js to execute JavaScript.")
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(js_code)
                temp_file = f.name
            
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            os.unlink(temp_file)
            
            if result.returncode != 0:
                raise RuntimeError(f"JavaScript execution failed: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"JavaScript execution timed out after {timeout} seconds")
        except Exception as e:
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass
            raise
    
    def decrypt_signature(self, decrypt_script: str, signature: str) -> str:
        """Decrypt a signature using the provided script"""
        js_code = f"""
        {decrypt_script}
        
        try {{
            const result = DisTubeDecipherFunc('{signature}');
            console.log(result);
        }} catch (error) {{
            console.error('Error:', error.message);
            process.exit(1);
        }}
        """
        
        return self.execute_js(js_code)
    
    def decrypt_n_parameter(self, decrypt_script: str, n_param: str) -> str:
        """Decrypt n parameter using the provided script"""
        js_code = f"""
        {decrypt_script}
        
        try {{
            const result = DisTubeNTransformFunc('{n_param}');
            console.log(result);
        }} catch (error) {{
            console.error('Error:', error.message);
            process.exit(1);
        }}
        """
        
        return self.execute_js(js_code)

class YouTubeDecryptor:
    """Complete YouTube decryptor with JavaScript execution"""
    
    def __init__(self):
        self.player_url = None
        self.player_code = None
        self.decrypt_script = None
        self.js_executor = JavaScriptExecutor()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_video_info(self, video_id: str) -> Dict:
        """Get video information from YouTube"""
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            response = self.session.get(video_url)
            response.raise_for_status()
            
            # Extract player URL
            player_url_match = re.search(r'"jsUrl":"([^"]+)"', response.text)
            if not player_url_match:
                raise ValueError("Could not find player URL")
            
            player_url = player_url_match.group(1).replace('\\/', '/')
            if player_url.startswith('//'):
                player_url = 'https:' + player_url
            elif player_url.startswith('/'):
                player_url = 'https://www.youtube.com' + player_url
            
            self.player_url = player_url
            logger.info(f"Found player URL: {player_url}")
            
            # Extract video data
            ytInitialPlayerResponse_match = re.search(
                r'var ytInitialPlayerResponse = ({.+?});', response.text
            )
            if not ytInitialPlayerResponse_match:
                raise ValueError("Could not find ytInitialPlayerResponse")
            
            video_data = json.loads(ytInitialPlayerResponse_match.group(1))
            return video_data
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise
    
    def get_player_code(self) -> str:
        """Download and cache the player code"""
        if self.player_code and self.player_url:
            return self.player_code
        
        if not self.player_url:
            raise ValueError("Player URL not found. Call get_video_info first.")
        
        try:
            logger.info(f"Downloading player code from: {self.player_url}")
            response = self.session.get(self.player_url)
            response.raise_for_status()
            
            self.player_code = response.text
            logger.info(f"Downloaded player code ({len(self.player_code)} characters)")
            return self.player_code
            
        except Exception as e:
            logger.error(f"Error downloading player code: {e}")
            raise
    
    def extract_decrypt_functions(self) -> str:
        """Extract decipher and n-transform functions from player code"""
        if not self.player_code:
            self.get_player_code()
        
        try:
            logger.info("Extracting decrypt functions...")
            decrypt_script = extract_decode_script_simple(self.player_code)
            self.decrypt_script = decrypt_script
            logger.info("Successfully extracted decrypt functions")
            return decrypt_script
            
        except Exception as e:
            logger.error(f"Error extracting decrypt functions: {e}")
            raise
    
    def decrypt_signature(self, signature: str) -> str:
        """Decrypt a signature using actual JavaScript execution"""
        if not self.decrypt_script:
            raise ValueError("Decrypt functions not setup. Call extract_decrypt_functions first.")
        
        try:
            decrypted = self.js_executor.decrypt_signature(self.decrypt_script, signature)
            logger.info(f"Successfully decrypted signature: {signature[:10]}... -> {decrypted[:10]}...")
            return decrypted
            
        except Exception as e:
            logger.error(f"Error decrypting signature: {e}")
            raise
    
    def decrypt_n_parameter(self, n_param: str) -> str:
        """Decrypt n parameter using actual JavaScript execution"""
        if not self.decrypt_script:
            raise ValueError("Decrypt functions not setup. Call extract_decrypt_functions first.")
        
        try:
            decrypted = self.js_executor.decrypt_n_parameter(self.decrypt_script, n_param)
            logger.info(f"Successfully decrypted n parameter: {n_param[:10]}... -> {decrypted[:10]}...")
            return decrypted
            
        except Exception as e:
            logger.error(f"Error decrypting n parameter: {e}")
            raise
    
    def get_video_formats(self, video_id: str) -> List[Dict]:
        """Get and decrypt video formats"""
        try:
            # Get video info and setup decryption
            video_data = self.get_video_info(video_id)
            self.get_player_code()
            self.extract_decrypt_functions()
            
            # Extract streaming data
            streaming_data = video_data.get('streamingData', {})
            formats = streaming_data.get('formats', []) + streaming_data.get('adaptiveFormats', [])
            
            decrypted_formats = []
            
            for fmt in formats:
                try:
                    # Check if URL needs decryption
                    if 'url' in fmt:
                        decrypted_url = fmt['url']
                    elif 'signatureCipher' in fmt:
                        # Parse signature cipher
                        cipher_data = urllib.parse.parse_qs(fmt['signatureCipher'])
                        
                        url = cipher_data.get('url', [''])[0]
                        signature = cipher_data.get('s', [''])[0]
                        sp = cipher_data.get('sp', ['sig'])[0]
                        
                        if signature:
                            # Decrypt signature
                            decrypted_sig = self.decrypt_signature(signature)
                            decrypted_url = f"{url}&{sp}={decrypted_sig}"
                        else:
                            decrypted_url = url
                    else:
                        logger.warning(f"Unknown format structure: {fmt}")
                        continue
                    
                    # Handle n parameter if present
                    if 'n=' in decrypted_url:
                        n_match = re.search(r'[?&]n=([^&]*)', decrypted_url)
                        if n_match:
                            n_param = n_match.group(1)
                            decrypted_n = self.decrypt_n_parameter(n_param)
                            decrypted_url = decrypted_url.replace(f'n={n_param}', f'n={decrypted_n}')
                    
                    # Add format info
                    format_info = {
                        'itag': fmt.get('itag'),
                        'url': decrypted_url,
                        'quality': fmt.get('quality'),
                        'qualityLabel': fmt.get('qualityLabel'),
                        'mimeType': fmt.get('mimeType'),
                        'filesize': fmt.get('contentLength'),
                        'fps': fmt.get('fps'),
                        'bitrate': fmt.get('bitrate'),
                        'width': fmt.get('width'),
                        'height': fmt.get('height'),
                        'audioQuality': fmt.get('audioQuality'),
                        'audioSampleRate': fmt.get('audioSampleRate'),
                    }
                    
                    decrypted_formats.append(format_info)
                    
                except Exception as e:
                    logger.error(f"Error processing format {fmt.get('itag')}: {e}")
                    continue
            
            return decrypted_formats
            
        except Exception as e:
            logger.error(f"Error getting video formats: {e}")
            raise
    
    def save_urls_to_file(self, formats: List[Dict], filename: str = "video_urls.txt"):
        """Save all video URLs to a file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"YouTube Video URLs - Generated on {json.dumps({}.__class__.__name__)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, fmt in enumerate(formats):
                    f.write(f"Format {i+1}:\n")
                    f.write(f"  Quality: {fmt.get('qualityLabel') or fmt.get('quality', 'Unknown')}\n")
                    f.write(f"  Type: {fmt.get('mimeType', 'Unknown')}\n")
                    f.write(f"  Bitrate: {fmt.get('bitrate', 'Unknown')}\n")
                    f.write(f"  Filesize: {fmt.get('filesize', 'Unknown')}\n")
                    f.write(f"  URL: {fmt['url']}\n")
                    f.write("\n" + "-" * 80 + "\n\n")
            
            logger.info(f"URLs saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving URLs: {e}")
            raise

def main():
    """Main function"""
    decryptor = YouTubeDecryptor()
    
    # Example video ID
    video_id = "dQw4w9WgXcQ"
    
    try:
        print(f"Processing video with enhanced decryptor: {video_id}")
        print("=" * 80)
        
        # Get video formats with actual decryption
        formats = decryptor.get_video_formats(video_id)
        
        print(f"\nFound {len(formats)} formats:")
        print("-" * 50)
        
        for i, fmt in enumerate(formats):
            print(f"{i+1:2d}. Quality: {fmt.get('qualityLabel') or fmt.get('quality', 'Unknown'):>10} | "
                  f"Type: {fmt.get('mimeType', 'Unknown')[:30]:30} | "
                  f"Bitrate: {fmt.get('bitrate', 'Unknown')}")
        
        # Save all URLs to file
        decryptor.save_urls_to_file(formats, "video_urls.txt")
        print(f"\n✓ All URLs saved to video_urls.txt")
        
        # Display full URL for first format
        if formats:
            print("\n" + "=" * 80)
            print("FULL URL EXAMPLE (Format 1):")
            print("=" * 80)
            print(formats[0]['url'])
            print("=" * 80)
            
            # Test URL accessibility
            print("\nTesting URL accessibility...")
            try:
                response = decryptor.session.head(formats[0]['url'], timeout=10)
                print(f"✓ URL Status: {response.status_code}")
                if response.status_code == 200:
                    print("✓ URL is valid and accessible")
                    # Get content length if available
                    content_length = response.headers.get('content-length')
                    if content_length:
                        print(f"✓ Content length: {int(content_length):,} bytes")
                else:
                    print(f"✗ URL returned status {response.status_code}")
            except Exception as e:
                print(f"✗ URL test failed: {e}")
        
        # Save decrypt script
        if decryptor.decrypt_script:
            with open("decrypt_script.js", 'w', encoding='utf-8') as f:
                f.write(decryptor.decrypt_script)
            print("\n✓ Decrypt script saved to decrypt_script.js")
        
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print(f"  Video ID: {video_id}")
        print(f"  Total formats: {len(formats)}")
        print(f"  Files created: video_urls.txt, decrypt_script.js")
        print("=" * 80)
    
    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Full error details:")

def detailed_format_info(video_id: str):
    """Show detailed format information"""
    decryptor = YouTubeDecryptor()
    
    try:
        print(f"Detailed analysis for video: {video_id}")
        print("=" * 100)
        
        formats = decryptor.get_video_formats(video_id)
        
        for i, fmt in enumerate(formats):
            print(f"\nFORMAT {i+1}:")
            print("-" * 50)
            print(f"  ITAG: {fmt.get('itag')}")
            print(f"  Quality: {fmt.get('qualityLabel') or fmt.get('quality', 'Unknown')}")
            print(f"  MIME Type: {fmt.get('mimeType', 'Unknown')}")
            print(f"  Bitrate: {fmt.get('bitrate', 'Unknown')}")
            print(f"  FPS: {fmt.get('fps', 'Unknown')}")
            print(f"  Dimensions: {fmt.get('width', 'Unknown')}x{fmt.get('height', 'Unknown')}")
            print(f"  Audio Quality: {fmt.get('audioQuality', 'Unknown')}")
            print(f"  Audio Sample Rate: {fmt.get('audioSampleRate', 'Unknown')}")
            print(f"  Filesize: {fmt.get('filesize', 'Unknown')}")
            print(f"  URL: {fmt['url']}")
            print("-" * 50)
        
        # Save detailed info to JSON
        with open(f"detailed_formats_{video_id}.json", 'w', encoding='utf-8') as f:
            json.dump(formats, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Detailed format info saved to detailed_formats_{video_id}.json")
        
    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Full error details:")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
        if len(sys.argv) > 2 and sys.argv[2] == "--detailed":
            detailed_format_info(video_id)
        else:
            decryptor = YouTubeDecryptor()
            try:
                formats = decryptor.get_video_formats(video_id)
                print(f"Found {len(formats)} formats for video {video_id}")
                print("=" * 60)
                
                for i, fmt in enumerate(formats):
                    print(f"{i+1:2d}. {fmt.get('qualityLabel', 'Unknown'):>10} | "
                          f"{fmt.get('mimeType', 'Unknown')[:40]:40}")
                
                # Save URLs to file
                decryptor.save_urls_to_file(formats, f"urls_{video_id}.txt")
                print(f"\n✓ Full URLs saved to urls_{video_id}.txt")
                
            except Exception as e:
                print(f"Error: {e}")
    else:
        main()