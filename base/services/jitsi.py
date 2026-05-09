import uuid


def generar_enlace_jitsi(
    iglesia_id,
    miembro_id
):

    sala = f"""

    iglesia-
    {iglesia_id}-
    miembro-
    {miembro_id}-
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