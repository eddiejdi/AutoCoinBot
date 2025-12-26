import base64
from PIL import Image
from io import BytesIO

# Caminho do arquivo base64
b64_path = 'bot_ui_screenshot.png.b64'

# Ler o base64
def decode_base64_to_image(b64_path, output_path='decoded_screenshot.png'):
    with open(b64_path, 'r') as f:
        b64_data = f.read().replace('\n', '')
    img_data = base64.b64decode(b64_data)
    image = Image.open(BytesIO(img_data))
    image.save(output_path)
    print(f'Imagem salva em: {output_path}')

if __name__ == '__main__':
    decode_base64_to_image(b64_path)
