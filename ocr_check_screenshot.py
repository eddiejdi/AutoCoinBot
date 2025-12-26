from PIL import Image
import pytesseract

# Caminho da imagem decodificada
img_path = 'decoded_screenshot.png'

# Extrair texto da imagem
image = Image.open(img_path)
text = pytesseract.image_to_string(image, lang='por+eng')

print('Texto extraído da imagem:')
print(text)

# Heurística simples para detectar mensagens de erro comuns
erros = []
for linha in text.splitlines():
    if any(palavra in linha.lower() for palavra in ['erro', 'error', 'fail', 'exceção', 'exception', 'traceback', 'invalid', 'não foi possível', 'not found', 'crash', 'fatal']):
        erros.append(linha)

if erros:
    print('\nPossíveis mensagens de erro detectadas:')
    for e in erros:
        print('-', e)
else:
    print('\nNenhuma mensagem de erro detectada na tela.')
