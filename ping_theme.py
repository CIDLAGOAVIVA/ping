"""
PING Theme - Tema customizado para o PING - UFF ANALYTICS
Baseado em Soft theme com cores Purple e Blue
"""

import gradio as gr

# Tema profissional para PING - UFF ANALYTICS
# Usando gr.themes.Soft como base com Purple primário
ping_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.purple,
    secondary_hue=gr.themes.colors.blue,
).set(
    # Customizações adicionais
    body_background_fill="#ffffff",
    body_background_fill_dark="#1a1a1a",
    loader_color="*primary_400",
    loader_color_dark="*primary_600",
    button_primary_shadow="0 4px 12px rgba(102, 126, 234, 0.3)",
    button_primary_shadow_dark="0 4px 12px rgba(102, 126, 234, 0.5)",
)
