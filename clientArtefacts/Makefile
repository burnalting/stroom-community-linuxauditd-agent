# Makefile for Stroom Auditd Collection agent
#
# Changelog
# - Update 20231206, BurnAlting burn.alting@gmail.com
#   - Include the configuration file stroom_auditd_feeder.config.base deployment
#   - Make configuration changes in configuration file, not the script
# - Initial release
#
# Destination directory
DESTDIR=/
AUDIT_ROOT=/opt/stroom/auditd

# Correct for configuration
# DEST - destination to post events to (if present)
# SEC_ZONE - security zone to set (if present)
# 

all:
ifeq ($(DEST),)
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd_feeder.sh.base > stroom_auditd_feeder.sh
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd.crontab.base > stroom_auditd.crontab
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd_shutdown.init.d.base > stroom_auditd_shutdown.init.d
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd_shutdown.service.base > stroom_auditd_shutdown.service
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd_feeder.config.base > stroom_auditd_feeder.config
else
ifeq ($(SEC_ZONE),)
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd_feeder.sh.base > stroom_auditd_feeder.sh
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd.crontab.base > stroom_auditd.crontab
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd_shutdown.init.d.base > stroom_auditd_shutdown.init.d
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd_shutdown.service.base > stroom_auditd_shutdown.service
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" -e "/https:\/\/stroom-proxy00.somedomain.org\/stroom\/datafeed,https:\/\//a URL=$(DEST)" stroom_auditd_feeder.config.base > stroom_auditd_feeder.config
else
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd_feeder.sh.base > stroom_auditd_feeder.sh
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd.crontab.base > stroom_auditd.crontab
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd_shutdown.init.d.base > stroom_auditd_shutdown.init.d
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" stroom_auditd_shutdown.service.base > stroom_auditd_shutdown.service
	sed -e "s+_AUDIT_ROOT_+$(AUDIT_ROOT)+" -e "/https:\/\/stroom-proxy00.somedomain.org\/stroom\/datafeed,https:\/\//a URL=$(DEST)" -e "/mySecZone=/a mySecZone=\"$(SEC_ZONE)\"" stroom_auditd_feeder.config.base > stroom_auditd_feeder.config
endif
endif

clean:
	rm -f stroom_auditd_feeder.sh stroom_auditd.crontab stroom_auditd_shutdown.init.d stroom_auditd_shutdown.service stroom_auditd_feeder.config

install:
	install -m 0750 -d ${DESTDIR}${AUDIT_ROOT}
	install -m 0750 -d ${DESTDIR}${AUDIT_ROOT}/bin
	install -m 0750 -d ${DESTDIR}${AUDIT_ROOT}/queue
	install -m 0750 -d ${DESTDIR}${AUDIT_ROOT}/locks
	install -m 0750 stroom_auditd_feeder.sh ${DESTDIR}${AUDIT_ROOT}/bin
	install -m 0644 stroom_auditd_feeder.config ${DESTDIR}${AUDIT_ROOT}/config
	install -m 0755 -d ${DESTDIR}/etc/logrotate.d
	install -m 0644 audit_logs.rotate ${DESTDIR}/etc/logrotate.d/stroom_auditing
	install -m 0700 -d ${DESTDIR}/etc/cron.d
	install -m 0600 stroom_auditd.crontab ${DESTDIR}/etc/cron.d/stroom_auditd
	install -m 0755 -d ${DESTDIR}/etc/systemd/system
	install -m 0644 stroom_auditd_shutdown.service ${DESTDIR}/etc/systemd/system/stroom_auditd_shutdown.service

