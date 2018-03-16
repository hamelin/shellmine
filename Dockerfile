FROM postgres:10.3
COPY setup.sh /docker-entrypoint-initdb.d/setup.sh 
RUN chmod 755 /docker-entrypoint-initdb.d/*
