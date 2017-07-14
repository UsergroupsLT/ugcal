FROM ubuntu:16.10

RUN groupadd -r ugcal && useradd -r -g ugcal ugcal
RUN apt-get -y update \
    && apt-get install -y git python2.7 python-pip cron python-gflags


ADD . /ugcal/
ADD cron.d/crontab /etc/cron.d/ugcal-cron
RUN set -x \
    && chmod 0644 /etc/cron.d/ugcal-cron \
    && touch /var/log/cron.log \
    && ln -s /ugcal/secrets/.credentials /root/.credentials \
    && cd /ugcal \
    && make bootstrap

CMD cron && tail -f /var/log/cron.log
