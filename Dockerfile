FROM python:3.12-slim

WORKDIR /app

# Instalar nginx para proxy reverso
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Tornar start.sh executável
RUN chmod +x start.sh

# Expor porta 8080 (nginx proxy) e 8501 (fallback direto Streamlit)
EXPOSE 8080 8501

# Usar start.sh para iniciar todos os serviços
CMD ["./start.sh"]
