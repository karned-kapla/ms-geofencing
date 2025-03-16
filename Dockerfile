FROM balenalib/raspberrypi3-debian:latest

RUN apt-get update && apt-get install -y \
    libwebp-dev libatlas-base-dev python3 python3-pip libopencv-dev python3-opencv

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY main.py main.py
COPY config.json .

CMD ["python3", "main.py"]
