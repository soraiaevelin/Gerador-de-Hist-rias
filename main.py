# Importa o módulo os para lidar com variáveis de ambiente e diretórios
import os

# Importa classes principais do FastAPI
from fastapi import FastAPI, Request, Form

# Permite renderizar templates HTML usando Jinja2
from fastapi.templating import Jinja2Templates

# Permite servir arquivos estáticos (CSS, JS, imagens)
from fastapi.staticfiles import StaticFiles

# Carrega variáveis do arquivo .env
from dotenv import load_dotenv

# Biblioteca da Google para usar a API Gemini (IA generativa)
import google.generativeai as genai

# 1. CONFIGURAÇÃO INICIAL

# Carrega as variáveis do arquivo .env
load_dotenv()

# Obtém a chave da API Gemini do ambiente
API_KEY = os.getenv("GEMINI_API_KEY")

# Se a chave existir, configura a biblioteca do Gemini
if API_KEY:
    genai.configure(api_key=API_KEY)

# Cria a aplicação FastAPI
app = FastAPI()

# Define o diretório onde ficam os templates HTML
templates = Jinja2Templates(directory="templates")

# Garante que a pasta "static" exista, mesmo que esteja vazia
# Isso evita erros ao iniciar a aplicação
os.makedirs("static", exist_ok=True)

# Monta a rota /static para servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# FUNÇÃO AUXILIAR

def listar_modelos_disponiveis():
    """
    Consulta a API do Gemini e retorna apenas os modelos
    que suportam geração de texto (generateContent).
    """
    # Se não houver chave de API, não tenta consultar
    if not API_KEY:
        return []

    modelos_uteis = []

    try:
        # Lista todos os modelos disponíveis na conta
        for m in genai.list_models():
            # Verifica se o modelo suporta geração de conteúdo
            if 'generateContent' in m.supported_generation_methods:
                modelos_uteis.append(m.name)

        # Retorna a lista ordenada alfabeticamente
        return sorted(modelos_uteis)

    except Exception as e:
        # Em caso de erro, exibe no terminal e retorna lista vazia
        print(f"Erro ao listar modelos: {e}")
        return []

# ROTA PRINCIPAL (GET)

@app.get("/")
def home(request: Request):
    """
    Exibe a página inicial com o formulário.
    """
    # Carrega a lista de modelos disponíveis
    modelos = listar_modelos_disponiveis()

    # Renderiza o template index.html
    return templates.TemplateResponse("index.html", {
        "request": request,
        "modelos": modelos,
        "erro_chave": not API_KEY  # Indica se a chave da API não foi configurada
    })
    
# ROTA DE GERAÇÃO (POST)

@app.post("/gerar")
def gerar_historia(
    request: Request,

    # Palavras recebidas do formulário HTML
    palavra1: str = Form(...),
    palavra2: str = Form(...),
    palavra3: str = Form(...),

    # Modelo selecionado pelo usuário no formulário
    modelo_selecionado: str = Form(...)
):
    """
    Gera uma história usando a API Gemini com base
    nas palavras fornecidas pelo usuário.
    """

    # Recarrega a lista de modelos para manter o menu preenchido
    modelos = listar_modelos_disponiveis()

    # Se a chave da API não estiver configurada, retorna erro
    if not API_KEY:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "historia": "ERRO: Chave de API não configurada no arquivo .env",
            "modelos": modelos
        })

    # Cria o prompt que será enviado para a IA
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

    # Variáveis para armazenar resultado ou erro
    historia = ""
    erro = ""

    try:
        # Exibe no terminal qual modelo está sendo usado
        print(f"Tentando usar o modelo: {modelo_selecionado}")

        # Cria o modelo com base na escolha do usuário
        model = genai.GenerativeModel(modelo_selecionado)

        # Envia o prompt para o Gemini
        response = model.generate_content(prompt)

        # Obtém o texto gerado
        historia = response.text

    except Exception as e:
        # Em caso de erro, registra e prepara a mensagem
        print(f"Erro: {e}")
        erro = f"Erro ao gerar com o modelo {modelo_selecionado}: {str(e)}"

    # Retorna o template com os dados preenchidos
    return templates.TemplateResponse("index.html", {
        "request": request,
        "historia": historia,
        "erro": erro,
        "palavra1": palavra1,
        "palavra2": palavra2,
        "palavra3": palavra3,
        "modelos": modelos,           # Mantém a lista de modelos
        "modelo_atual": modelo_selecionado  # Mantém o modelo selecionado
    })
