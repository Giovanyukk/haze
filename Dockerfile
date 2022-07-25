FROM ubuntu:latest as builder
WORKDIR /build/
RUN apt-get update && apt-get install -y\
    python3 \
    python3-dev \
    python3-pip
COPY requirements.txt .
RUN python3 -m pip install -U pip setuptools wheel
RUN python3 -m pip install -r requirements.txt
COPY . .
RUN pyinstaller -i ./logo.ico --clean --onefile ./source/Haze.py --hidden-import=xlsxwriter

FROM ubuntu:latest
WORKDIR /app/
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y locales
RUN sed -i -e 's/# es_AR.UTF-8 UTF-8/es_AR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=es_AR.UTF-8
ENV LANG es_AR.UTF-8 
COPY --from=builder /build/dist/Haze .
RUN chmod +x ./Haze
CMD [ "./Haze" ]