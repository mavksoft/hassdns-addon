ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache certbot openssl curl jq bash

COPY run.sh /
COPY hooks/ /hooks/
RUN chmod a+x /run.sh /hooks/*.sh

CMD [ "/run.sh" ]
