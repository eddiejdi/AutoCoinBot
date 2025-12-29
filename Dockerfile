FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt


# Copy the rest of the code
COPY . .

# Expose the Streamlit port
EXPOSE 8501


# Run the Streamlit app (headless)
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.headless=true"]
#
