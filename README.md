
# Zaggregator

Zaggregator - is a non-envasive per-process data collector for Zabbix.

It consists of two parts:
 - zaggregator (daemon) which fetches and caches process table each zaggregator.daemon.delay (30) seconds, groups processes and stores statistics into sqlite database.
 - zcheck script for integrating with zabbix-agent fetches data from sqlite database

There is systemd service file for zaggregator-daemon, but for security reasons pip cannot install files into /etc, so you will need to do it manually. See [Install](#install) section for details.


# Install

Recommended:

```bash
pip install zaggregator
cp /usr/share/zaggregator/zaggregator.service /etc/systemd/system/
systemctl enable zaggregator
systemctl start zaggregator
cp /usr/share/zaggregator/zaggregator.conf /etc/zabbix/zabbix_agentd.d/
service zabbix-agent restart
```
