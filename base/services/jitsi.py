import uuid


def generar_enlace_jitsi(
    iglesia_id,
    miembro_id,
    miembro_nombre
):

    nombre = "".join(
        palabra.capitalize()
        for palabra in miembro_nombre.split()
    )

    sala = f"""
    {uuid.uuid4().hex[:8]}-{nombre}-
    {uuid.uuid4().hex[:8]}
    """

    sala = sala.replace(
        "\n",
        ""
    ).replace(
        " ",
        ""
    )

    return f"https://meet.jit.si/{sala}"