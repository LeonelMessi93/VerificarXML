# Verificar XML — Frontend + Backend

Projeto mínimo para **enviar um XML de NF-e**, **converter em Excel** e **baixar** o arquivo gerado.

## 🔧 Backend (Python / FastAPI)
Requisitos:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
O servidor ficará em `http://127.0.0.1:8000`.

## 🌐 Frontend (HTML)
Abra `frontend/index.html` no navegador.
> Se o backend estiver em outra porta/host, edite a constante `API_URL` no `index.html`.

## 📄 Saída
O download será feito como **Validador_XML.xlsx**, com a aba **XML** contendo os itens do documento.

## 📌 Notas
- O parser foi implementado no nível de item (`<det>`), cobrindo campos essenciais (chave, série, data, emitente, destinatário, NCM, CFOP, quantidade, valor unitário, valor produto, ICMS básico, total da NF).  
- Se quiser replicar *todos* os campos do seu script desktop, podemos expandir a função `xml_to_dataframe` facilmente.


# Deploy — Verificar XML (Frontend + Backend)

Este guia explica como publicar o **backend (FastAPI)** no **Render** (grátis) e o **frontend** na **Netlify** (ou **Vercel**), conectando os dois.

---

## 🔧 Backend (Render)

1. Faça login em https://render.com
2. Clique **New → Web Service** → **Public Git Repository** (ou conecte seu GitHub).
3. Se o repositório tiver esta estrutura na raiz, use:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Runtime**: Python 3.11
   - **Free plan**
4. Alternativa: use o arquivo **render.yaml** (Deploys → Blueprint).
5. Após o deploy, você terá uma URL, por ex.: `https://verificar-xml-backend.onrender.com`
6. Teste:
   - `GET /ping` → deve retornar `{"ok": true}`
   - `POST /upload_json` (com arquivo .xml) → retorna JSON de prévia

> Obs.: CORS já está liberado no `backend/main.py`.

---

## 🌐 Frontend (Netlify — recomendado para estático)

1. Acesse https://app.netlify.com → **Add new site** → **Deploy manually** (arraste a pasta `frontend`) ou conecte com GitHub.
2. Não há build (site estático), apenas publique a pasta `frontend`.
3. **Edite** no arquivo `frontend/index.html` as URLs do backend:
   ```js
   const API_JSON = "https://SEU_BACKEND/upload_json";
   const API_XLSX = "https://SEU_BACKEND/upload";
   ```
4. Abra a URL do site Netlify e teste o fluxo.

**Opcional**: o arquivo `netlify.toml` já está incluso para facilitar.

---

## 🚀 Frontend (Vercel — alternativa)

1. Acesse https://vercel.com → **New Project** → Import seu GitHub.
2. Nas configurações, não precisa de build (site estático).  
3. Certifique-se de que `frontend` está no repositório e que `vercel.json` roteia para a pasta `frontend`.
4. Edite as URLs do backend em `frontend/index.html` como no passo da Netlify.

---

## 🧪 Teste fim a fim

1. Abra seu site (Netlify ou Vercel).
2. Clique **“Ver prévia no site”**, selecione `.xml` → deve mostrar a tabela com as primeiras linhas.
3. Clique **“Baixar Excel”** → deve baixar `Validador_XML.xlsx`.

---

## 🧱 Estrutura do repositório

```
/
├─ backend/
│  ├─ main.py
│  └─ requirements.txt
├─ frontend/
│  └─ index.html
├─ netlify.toml
├─ vercel.json
├─ render.yaml
└─ README.md
```

Se quiser, posso criar um repositório GitHub público/privado com esses arquivos e te passar os comandos `git` para subir a primeira versão.
