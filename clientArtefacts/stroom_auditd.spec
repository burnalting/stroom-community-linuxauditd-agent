# Release 2.0 20231206 Burn Alting, burn.alting@gmail.com
#   - Uplift to recent release 3.1.4
# Release 1.0 20170520 Burn Alting
#   - Initial Release (2.0.0-0)

#
# This spec file should be called with given you are in a standard rpmbuild
# area
#   rpmbuild -ba --define 'dist .el6' SPECS/stroom_auditd.spec
#   rpmbuild -ba --define 'dist .el7' SPECS/stroom_auditd.spec
#   rpmbuild -ba --define 'dist .el8' SPECS/stroom_auditd.spec
#   rpmbuild -ba --define 'dist .el9' SPECS/stroom_auditd.spec
#
# To build for a domain, eg 
#   rpmbuild -ba --define 'dist .el6' --define '_sz .dom2' --define '_dst stroomnode.mysub.myorg' --define '_sz_verbose "Domain #2"' SPECS/stroom_auditd.spec
#   rpmbuild -ba --define 'dist .el7' --define '_sz .dom2' --define '_dst stroomnode.mysub.myorg' --define '_sz_verbose "Domain #2"' SPECS/stroom_auditd.spec
#   rpmbuild -ba --define 'dist .el8' --define '_sz .dom2' --define '_dst stroomnode.mysub.myorg' --define '_sz_verbose "Domain #2"' SPECS/stroom_auditd.spec
#   rpmbuild -ba --define 'dist .el9' --define '_sz .dom2' --define '_dst stroomnode.mysub.myorg' --define '_sz_verbose "Domain #2"' SPECS/stroom_auditd.spec

%define dist6 %(test 0"%{dist}" = 0.el6 && echo 1 || echo 0)
%define dist7 %(test 0"%{dist}" = 0.el7 && echo 1 || echo 0)
%define dist8 %(test 0"%{dist}" = 0.el8 && echo 1 || echo 0)
%define dist9 %(test 0"%{dist}" = 0.el9 && echo 1 || echo 0)

Name: stroom_auditd_agent
Version: 3.1.4
# Note we concatenate the domain and distribution
Release: 0%{?_sz}%{?dist}
Summary: This is the Stroom auditd collection agent
License: GPL
Group: System Environment/Daemons
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildArch: noarch
ExclusiveOS: Linux

Requires: audit-libs > 2.4.0 audit > 2.4.0 curl bind-utils gzip net-tools sed gawk coreutils

%description
The stroom_auditd_agent package contains a processing script designed to process and send Linux
operating system audit to an Stroom audit server. The processing uses the standard ausearch
utility to enrich the raw audit. If the aushape utility is available, it will use this to
further format the ausearch output.

%prep
%setup -q

%build
make %{?_smp_mflags} ARCH=%{arch_p} DIST=%{dist} DEST=%{_dst} SEC_ZONE=%{_sz_verbose} all

%install
AUDIT_ROOT=/opt/stroom/auditd
rm -rf $RPM_BUILD_ROOT
cd ${RPM_BUILD_DIR}/%{name}-%{version}
install -m 0750 -d %{buildroot}${AUDIT_ROOT}
install -m 0750 -d %{buildroot}${AUDIT_ROOT}/bin
install -m 0750 -d %{buildroot}${AUDIT_ROOT}/queue
install -m 0750 -d %{buildroot}${AUDIT_ROOT}/locks
install -m 0750 stroom_auditd_feeder.sh %{buildroot}${AUDIT_ROOT}/bin
install -m 0644 stroom_auditd_feeder.config %{buildroot}${AUDIT_ROOT}/config
install -m 0755 -d %{buildroot}/etc/logrotate.d
install -m 0644 audit_logs.rotate %{buildroot}/etc/logrotate.d/stroom_auditd
install -m 0700 -d %{buildroot}/etc/cron.d
install -m 0644 stroom_auditd.crontab %{buildroot}/etc/cron.d/stroom_auditd
%if %{?dist6}
install -m 0755 -d %{buildroot}/etc/init.d
install -m 0755 stroom_auditd_shutdown.init.d %{buildroot}/etc/init.d/stroom_auditd_shutdown
%else
install -m 0755 -d %{buildroot}/etc/systemd/system
install -m 0644 stroom_auditd_shutdown.service %{buildroot}/etc/systemd/system/stroom_auditd_shutdown.service
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%pre
# Pre INSTALL
# Note:
#  If this is a clean install then $1 == 1
#  If this is an upgrade then $1 == 2
#
# If we are an upgrade, then we need to ensure the we are not executing the
# script that gathers the audit data for it normally sleeps for a random period

if [ $1 -ne 1 ]; then
  PG=`ps -eo pgid,cmd | awk '$0 ~ /\/opt\/stroom\/auditd\/bin\/stroom_auditd_feeder.sh.*\/var\/log\/stroom_auditd_auditing.log/ {print $1; exit}'`
  if [ -n "$PG" ]; then
    kill -- -$PG
    sleep 3
  fi
  /opt/stroom/auditd/bin/stroom_auditd_feeder.sh -n >> /var/log/stroom_auditd_auditing.log
  # Now remove any lock files
  rm -f /opt/stroom/auditd/locks/*.lck
fi

# We now do a series of audit configuration checks to ensure audit is configured correctly
errs=0
# We check if the file /etc/sysconfig/auditd exists. If it does, we are still using service(8)
# so we need to check if USE_AUGENRULES is present and, if so, check it is set to yes
if [ -f /etc/sysconfig/auditd ]; then
  if egrep -q 'USE_AUGENRULES="no"' /etc/sysconfig/auditd; then
    echo "USE_AUGENRULES is set to 'no' in /etc/sysconfig/auditd. Fix by setting to yes"
    errs=1
  fi
fi


# We check to see if the system can resolve it's hostname.
# This is done as we require that /etc/auditd.conf has "name=fqd"
# If the system cannot resolve it's hostname, auditd cannot start with
# the name=fqd configuration setting
# We do this with a simple test to hostname(1)
hostname --fqdn > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Cannot resolve hostname (via hostname --fqdn). Fix via /etc/hosts entry or resolve host via other means"
  errs=1
fi

# We further check that hostname != localhost
hostname 2>/dev/null | egrep --quiet '^localhost$|^localhost\.'
if [ $? -eq 0 ]; then
  echo "Hostname cannot be localhost (via hostname). Ensure this host is identifiable. "
  errs=1
fi
# Also check that hostname -fqdn is not localhost
hostname --fqdn 2>/dev/null | egrep --quiet '^localhost$|^localhost\.' 
if [ $? -eq 0 ]; then
  echo "FQDN cannot be localhost (via hostname --fqdn). Ensure this host is identifiable"
  errs=1
fi

exit ${errs}

%post
# Post INSTALL
# Note:
#  If this is a clean install then $1 == 1
#  If this is an upgrade then $1 == 2
#
if [ $1 -eq 1 ]; then
am_install=1
else
am_install=0
fi

%if %{?dist6}
# An install on dist6 means a install then enablement of stroom_auditd_shutdown init.d service
if [ $am_install -eq 1 ]; then
  chkconfig --add stroom_auditd_shutdown
  chkconfig stroom_auditd_shutdown on
  service stroom_auditd_shutdown start # This is done to get a lockfile so a shutdown can occur
fi
%else
# An install on dist7 means a install then enablement of stroom_auditd_shutdown.service
if [ $am_install -eq 1 ]; then
  systemctl enable stroom_auditd_shutdown.service --now
  systemctl daemon-reload
fi
%endif

exit 0

%preun
# Pre UNINSTALL
#  If last version of package is erased then $1 == 0

# If we are in effect doing an erase, then we need to ensure we do one final collection
# of audit. We first delete any running instance, then run it manually.
if [ $1 -eq 0 ]; then
  PG=`ps -eo pgid,cmd | awk '$0 ~ /\/opt\/stroom\/auditd\/bin\/stroom_auditd_feeder.sh.*\/var\/log\/stroom_auditd_auditing.log/ {print $1; exit}'`
  if [ -n "$PG" ]; then
    kill -- -$PG
    sleep 3
  fi
  /opt/stroom/auditd/bin/stroom_auditd_feeder.sh -n >> /var/log/stroom_auditd_auditing.log
  sleep 3
  # Now remove any lock files and the checkpoint file
  rm -f /opt/stroom/auditd/locks/*.lck /opt/stroom/auditd/locks/auditd_checkpoint.txt

%if %{?dist6}
  chkconfig stroom_auditd_shutdown off
  chkconfig --del stroom_auditd_shutdown
  rm -f /var/lock/subsys/stroom_auditd_shutdown
%else
  systemctl disable stroom_auditd_shutdown.service
%endif
fi

exit 0

%postun
# Post UNINSTALL
# Note:
#  If an upgrade, then $1 == 1
#  If last version of package is erased then $1 == 0
#
exit 0

%files
%defattr(-,root,root)
%dir %attr(750,root,root) /opt/stroom/auditd
%dir %attr(750,root,root) /opt/stroom/auditd/bin
%attr(750,root,root) /opt/stroom/auditd/bin/stroom_auditd_feeder.sh
%attr(750,root,root) /opt/stroom/auditd/queue
%attr(750,root,root) /opt/stroom/auditd/locks
%attr(640,root,root) /opt/stroom/auditd/config
%attr(644,root,root) /etc/logrotate.d/stroom_auditd
%attr(640,root,root) /etc/cron.d/stroom_auditd
%if %{dist6}
%attr(755,root,root) /etc/init.d/stroom_auditd_shutdown
%else
%attr(644,root,root) /etc/systemd/system/stroom_auditd_shutdown.service
%endif

%changelog
* Wed Dec 06 2023 Burn Alting 3.1.4-0
- Refreshed
* Sat May 20 2017 Burn Alting 2.0.0-0
- First Release
