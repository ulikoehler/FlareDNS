FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip --no-cache-dir install -r requirements.txt
COPY update-dyndns.py .
CMD ["python", "update-dyndns.py"]