docker build -f Dockerfile -t til-code-drill-builder .
docker run --rm -it -v %cd%:/app til-code-drill-builder