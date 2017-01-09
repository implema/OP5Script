# smsdsender
This script sends SMS messages created by OP5 monitor using Pixie SMS Service.
Useful if no SMS modem is available on the OP5 server.

Copy this folder to /opt/plugins/custom/ and add the followig to your crontab:
* * * * * root python /opt/plugins/custom/smsd/smsd_sender.py /var/spool/sms/ >> /var/log/smsd.log
