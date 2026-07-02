from PIL import Image
import io

def calculate_max_payload(img):
    """Calculate max bytes that can be hidden in image."""
    width, height = img.size
    total_pixels = width * height
    total_bits = total_pixels * 3  # 3 channels (RGB)
    max_bytes = total_bits // 8  # Convert bits to bytes
    return max_bytes

def _bytes_to_bits(data: bytes):
    for b in data:
        for i in range(7, -1, -1):
            yield (b >> i) & 1

def _bits_to_bytes(bits):
    out = bytearray()
    acc = 0
    cnt = 0
    for bit in bits:
        acc = (acc << 1) | bit
        cnt += 1
        if cnt == 8:
            out.append(acc)
            acc = 0
            cnt = 0
    return bytes(out)

def embed_bytes_into_image(image_file, data: bytes, out_path: str):
    img = Image.open(image_file)
    img = img.convert('RGB')
    pixels = list(img.getdata())
    total_channels = len(pixels) * 3
    required_bits = (len(data) + 4) * 8
    if required_bits > total_channels:
        raise ValueError(f'image too small for payload. Requires {required_bits} bits, but image only has {total_channels} usable bits ({(total_channels // 8) / 1024:.2f} KB max capacity).')
    length_prefix = len(data).to_bytes(4, 'big')
    payload = length_prefix + data
    bits = list(_bytes_to_bits(payload))
    flat = []
    idx = 0
    for (r,g,b) in pixels:
        if idx < len(bits):
            r = (r & ~1) | bits[idx]; idx += 1
        if idx < len(bits):
            g = (g & ~1) | bits[idx]; idx += 1
        if idx < len(bits):
            b = (b & ~1) | bits[idx]; idx += 1
        flat.append((r,g,b))
    flat.extend(pixels[len(flat):])
    out = Image.new('RGB', img.size)
    out.putdata(flat)
    out.save(out_path, format='PNG')

def extract_bytes_from_image(image_file):
    img = Image.open(image_file)
    img = img.convert('RGB')
    pixels = list(img.getdata())
    bits = []
    for (r,g,b) in pixels:
        bits.append(r & 1)
        bits.append(g & 1)
        bits.append(b & 1)
    length_bits = bits[:32]
    length = int.from_bytes(_bits_to_bytes(length_bits), 'big')
    if length == 0:
        return b''
    data_bits = bits[32:32 + (length * 8)]
    return _bits_to_bytes(data_bits)
