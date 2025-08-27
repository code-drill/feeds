docker build -f Dockerfile -t feeds-code-drill-builder .
docker run --rm -it -v %cd%:/app feeds-code-drill-builder /bin/bash -c %*