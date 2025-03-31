FROM postgres:14

# All environment variables consolidated in a single ENV statement
ENV POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=Vall123@ \
    POSTGRES_DB=images \
    PG_MAJOR=14 \
    PG_VERSION=14.17-1.pgdg120+1 \
    PGDATA=/var/lib/postgresql/data \
    PUID=1026 \
    PGID=100 \
    LANG=en_US.utf8

# Copy initialization SQL scripts
COPY create_images_table.sql /docker-entrypoint-initdb.d/

# Expose the PostgreSQL port (standard PostgreSQL port)
EXPOSE 5432

# Note: In Synology, map local port 9000 to container port 5432

# Set custom port (if needed)
CMD ["postgres", "-c", "port=9001"] 