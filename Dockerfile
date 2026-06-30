FROM python:3.11-slim

WORKDIR /code

# Thiết lập biến môi trường không sinh file .pyc và không buffer log
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Cài đặt các thư viện hệ thống cần thiết (nếu có)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && apt-get clean

# Copy requirements và cài đặt python packages
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy toàn bộ code vào container
COPY . /code/

# Lệnh khởi chạy uvicorn bên trong docker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
