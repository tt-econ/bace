FROM public.ecr.aws/lambda/python:3.9

COPY app.py requirements.txt ./
COPY bace ./bace
COPY database ./database
COPY templates ./templates
COPY static ./static
COPY utils ./utils
# If you add additional folders, make sure to save them to the Docker image.

RUN python3.9 -m pip install --upgrade pip
RUN python3.9 -m pip install -r requirements.txt

CMD ["app.app"]

