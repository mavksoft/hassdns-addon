ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache certbot openssl curl jq bash python3

COPY run.sh /
COPY hooks/ /hooks/
COPY panel/ /panel/
RUN chmod a+x /run.sh /hooks/*.sh

CMD [ "/run.sh" ]
