from .models import *

def obtener_siguiente_curso(miembro, iglesia, periodo):

    # 🔹 cursos ordenados por nivel
    cursos = Curso.objects.filter(
        iglesia=iglesia
    ).select_related("nivel").order_by("nivel__orden")

    if not cursos.exists():
        return None

    # 🔹 historial aprobado
    aprobados = Inscripcion.objects.filter(
        estudiante=miembro,
        estado="aprobado"
    ).values_list("curso_periodo__curso_id", flat=True)

    # 🔹 buscar siguiente
    for curso in cursos:
        if curso.id not in aprobados:
            return curso

    return None  # ya completó todo


def obtener_curso_periodo_disponible(curso, iglesia, periodo):

    return CursoPeriodo.objects.filter(
        iglesia=iglesia,
        curso=curso,
        periodo=periodo,
        activo=True
    ).first()