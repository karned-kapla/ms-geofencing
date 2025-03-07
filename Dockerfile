FROM balenalib/raspberrypi3-debian:latest

RUN apt-get update && apt-get install -y \
    python3 python3-pip libopencv-dev python3-opencv

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY intrusion_detection_service.py .
COPY config.json .

CMD ["python3", "intrusion_detection_service.py"]
