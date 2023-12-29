FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip --no-cache-dir install -r requirements.txt
# Copy main script
COPY flaredns.py .
# Copy examples so they can be used directly
COPY examples/CopyDNS.py .
CMD ["python", "flaredns.py"]
