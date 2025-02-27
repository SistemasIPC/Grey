with open("datos.json", "rb") as f:
    contenido = f.read().decode("utf-16")  # Intenta decodificarlo como UTF-16

with open("archivo_corregido.json", "w", encoding="utf-8") as f:
    f.write(contenido)