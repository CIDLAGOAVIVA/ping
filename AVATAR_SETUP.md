# 🎨 Como Adicionar o Avatar do Agente

## Instruções

Para adicionar a foto do agente no chat, siga estes passos:

### 1. Salvar a Imagem

Salve a imagem do agente (o robô azul com headset) com o nome **`agent_avatar.png`** no diretório:

```
/home/marcus/projects/ping/assets/agent_avatar.png
```

### 2. Formatos Suportados

O Gradio aceita os seguintes formatos:
- PNG (recomendado)
- JPG/JPEG
- WebP
- GIF

### 3. Tamanho Recomendado

- **Dimensões:** 512x512 pixels ou 1024x1024 pixels (quadrado)
- **Peso:** Menos de 500KB para carregar rápido

### 4. Alternativa: Usar URL Online

Se preferir, você pode hospedar a imagem online e usar a URL diretamente:

```python
avatar_images=(None, "https://seu-servidor.com/agent_avatar.png")
```

### 5. Verificar se Funcionou

Após adicionar a imagem, reinicie a aplicação:

```bash
pkill -f "python app.py"
uv run python app.py
```

O avatar do agente deve aparecer ao lado das respostas no chat!

---

## Status Atual

✅ Código atualizado para usar: `assets/agent_avatar.png`  
⏳ Aguardando você adicionar a imagem do robô azul

## Alternativa Temporária

Se quiser testar antes de ter a imagem, você pode usar um emoji como avatar temporário:

```python
avatar_images=(None, "🤖")  # Emoji de robô
```

Ou usar um gerador de avatar online como:
- https://api.dicebear.com/7.x/bottts/png?seed=agent
- https://ui-avatars.com/api/?name=Agent&background=667eea&color=fff&size=512
