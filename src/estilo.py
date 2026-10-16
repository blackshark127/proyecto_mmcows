"""Paleta y estilo común a todas las figuras del proyecto.

Regla de color desde el Avance 1: gris = contexto, azul = lo normal,
naranja = solo lo que pide atención.
"""
import matplotlib.pyplot as plt

GRAY, LGRAY, BLUE, ORANGE, INK, MUTED = "#a3a3a3", "#d9d9d9", "#1f5fa8", "#e07b1a", "#222222", "#666666"
# Escala secuencial de un solo tono para el estrés calórico (ordinal):
# se lee también en blanco y negro.
ESTRES = {"sin estrés": "#f4f4f4", "leve": "#d9d9d9", "moderado": "#a8a8a8", "severo": "#5f5f5f"}


def aplicar_estilo():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#888888",
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 200})


def titulo(fig, t, sub):
    """Título como afirmación (qué debe ver el lector) + subtítulo con muestra y periodo."""
    fig.text(0.01, 0.985, t, ha="left", va="top", fontsize=13, fontweight="bold", color=INK)
    fig.text(0.01, 0.925, sub, ha="left", va="top", fontsize=9, color=MUTED)
