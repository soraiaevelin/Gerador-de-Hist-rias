import os
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Configuração
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

app = FastAPI()

templates = Jinja2Templates(directory="templates")
# Garante que a pasta static existe para evitar erros, mesmo que vazia
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


def listar_modelos_disponiveis():
    """
    Consulta a API para ver quais modelos suportam geração de texto (generateContent).
    """
    if not API_KEY:
        return []

    modelos_uteis = []
    try:
        # Lista todos os modelos disponíveis na sua conta
        for m in genai.list_models():
            # Filtra apenas os que geram conteúdo (texto)
            if 'generateContent' in m.supported_generation_methods:
                modelos_uteis.append(m.name)
        # Ordena para ficar bonito
        return sorted(modelos_uteis)
    except Exception as e:
        print(f"Erro ao listar modelos: {e}")
        return []


@app.get("/")
def home(request: Request):
    # Ao abrir o site, carregamos a lista de modelos
    modelos = listar_modelos_disponiveis()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "modelos": modelos,
        "erro_chave": not API_KEY  # Avisa se esqueceu a chave
    })


@app.post("/gerar")
def gerar_historia(
    request: Request,
    palavra1: str = Form(...),
    palavra2: str = Form(...),
    palavra3: str = Form(...),
    modelo_selecionado: str = Form(...)  # Recebe o modelo escolhido no HTML
):
    # Recarrega a lista para manter o menu preenchido
    modelos = listar_modelos_disponiveis()

    if not API_KEY:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "historia": "ERRO: Chave de API não configurada no arquivo .env",
            "modelos": modelos
        })

    prompt = f"""
    Crie uma história MUITO engraçada e maluca usando estas três palavras:
    1. {palavra1}
    2. {palavra2}
    3. {palavra3}

    A história deve ter:
    - Humor
    - Criatividade
    - No mínimo 4 parágrafos curtos
    """

    historia = ""
    erro = ""

    try:
        # Usa EXATAMENTE o modelo que o usuário selecionou na tela
        print(f"Tentando usar o modelo: {modelo_selecionado}")
        model = genai.GenerativeModel(modelo_selecionado)

        response = model.generate_content(prompt)
        historia = response.text

    except Exception as e:
        print(f"Erro: {e}")
        erro = f"Erro ao gerar com o modelo {modelo_selecionado}: {str(e)}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "historia": historia,
        "erro": erro,
        "palavra1": palavra1,
        "palavra2": palavra2,
        "palavra3": palavra3,
        "modelos": modelos,  # Devolve a lista para o menu não sumir
        "modelo_atual": modelo_selecionado  # Mantém o modelo selecionado
    })
