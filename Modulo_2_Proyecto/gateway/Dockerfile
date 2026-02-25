FROM nginx:1.29-alpine

# envsubst for template rendering
RUN apk add --no-cache gettext

# Template-based config so we can bind to Railway's $PORT
COPY nginx.railway.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh

CMD ["/docker-entrypoint.sh"]


