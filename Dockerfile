FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip --no-cache-dir install -r requirements.txt
# Copy main script
COPY update-dyndns.py .
# Copy examples so they can be used directly
COPY examples/CopyDNS.py .
CMD ["python", "update-dyndns.py"]