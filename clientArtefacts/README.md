# Synopsis
The stroom_auditd_agent is a lightweight auditing deployment that periodically collects events from the Linux auditd sub-system and posts those events to an instance of Stroom. It is expected that
 - the system can resolve it's own hostname i.e the command "hostname --fqdn" returns the correct and expected value (localhost* is not acceptable)
 - the system has an appropriate ip address i.e. the command "hostname -I" returns the correct and expected value (127.0.0.1 is not acceptable)
 - the Linux auditd system has been set up appropriately and the resultant logging appears in /var/log/audit
 - the Stroom Audit System has been configured to accept streams of events into one of LINUX-AUDITD-AUSEARCH-V3-EVENTS or
   LINUX-AUDITD-AUSHAPE-V3-EVENTS feeds.
 - the audit authority has set up one or two destination web servers to post to. Change the string URL to identify multiple destinations
   to try

# Configuration items
Certain configuration items can be set on the script's command line and other items can be set in a configuration file.
Command line switches are

    stroom_auditd_feeder.sh [-fnP] [-F auditdlogfile] [-l LockFile] [-d delaysecs] [-c checkpointfile] [-R days] [-M blockcount] [-p disconectfilesdir]

Switch | Description
------ | -----------
-f | force the run.
-n | prevents the random sleep prior to processing
-P | form a 'disconnect package file' rather than post the data to a stroom proxy
-p | specify a directory to look for 'disconnect package files' and post them
-F fn | specify the raw audit log file to gain logs from
-l fn | specify a unique lock file name, so multiple invocations of this script can exist. If a path then this is the lock file
-d secs | specify the MAX_SLEEP value (default is 590)
-c fn | specify the checkpoint file
-R | set a different failed retention period
-M | set a different failed maximum size to be retained until age off

The file _AUDIT_ROOT_/config (usually /opt/stroom/auditd/config), if present, can change the default environment variables used by stroom_auditd_feeder.sh. Environment variables such as those following could be set in this file

Environment Variable | Description | Example
-------------------- | ----------- | -------
SYSTEM | The system the Linux host is deployed within or type of Linux host. | SYSTEM="Cross Domain Capability #1"
ENVIRONMENT | The system environment the host is deployed within. Can be one of "Production", "QualityAssurance", or "Development" | ENVIRONMENT="Development"
URL | A csv list of urls where the script is to post the audit log files to. The script will attempt to send to each url on the list until success or list exhaustion | URL=https://stroom-proxy00.somedomain.org/stroom/datafeed,https://stroom-proxy07.somedomain.org/stroom/datafeed
mySecZone | The 'security' zone of the capability. | mySecZone="Cross Domain Capability #1 High Side Zone"
FAILED_RETENTION | Number of days to hold log files that failed to post (120 here). | FAILED_RETENTION=120
FAILED_MAX | Specify a storage limit on logs that failed to transmit (512-byte blocks) (16GB here) | FAILED_MAX=33554432

See the sample configuration file, stroom_auditd_feeder.config.base, for more detail.

# Local centralisation (syslog server)
One can optionally specify a single file to collect audit from. This may be the case if one is sending auditd events via say a syslog plugin (hopefully tcp) to a central host which holds auditd files for multiple hosts (as well as it's own).

Given you are not sending this central host's audit to itself one could deploy the complete package and then add additional cron entries to collect audit from the aggregating locations. Such scripting is beyond the scope of this release but fundamentally, given you have a structure like

    repository/
    repository/year/
    repository/year/month
    repository/year/month/day
    repository/year/month/day/hosta/auditd.log
    repository/year/month/day/hostb/auditd.log
    repository/year/month/day/hostc/auditd.log
    ...
    repository/year/month/day/hostN/auditd.log
  
one could run the main script with say

    stroom_auditd_feeder.sh -l repository/year/month/day/hosta/chkpt.txt -F repository/year/month/day/hosta/auditd.log -c repository/year/month/day/hosta/chkpt.txt
    stroom_auditd_feeder.sh -l repository/year/month/day/hostb/chkpt.txt -F repository/year/month/day/hostb/auditd.log -c repository/year/month/day/hostb/chkpt.txt
    stroom_auditd_feeder.sh -l repository/year/month/day/hostc/chkpt.txt -F repository/year/month/day/hostc/auditd.log -c repository/year/month/day/hostc/chkpt.txt
    ...
    stroom_auditd_feeder.sh -l repository/year/month/day/hostN/chkpt.txt -F repository/year/month/day/hostN/auditd.log -c repository/year/month/day/hostN/chkpt.txt

To orchestrate this a script would need to run through the repository, perhaps using the existence of the chkpt.txt file given you keep it in the data directory. Use its existence (ie if not there, we have not processed data) and of the three times of the data file, checkpoint file and the current time to see if we need to still run the command for that repository directory

# Disconnected Transmission
In certain circumstances, a destination Stroom proxy will not be available. To facilitate this, the concept of a 'disconnect package file' has been introduced. In essence, the primary script, stroom_auditd_feeder.sh, can create a 'disconnect package file' which is then moved to a host which can post to a Stroom proxy and that host can post the file, whilst retaining all the metadata the script (stroom_auditd_feeder.sh) normally gathers and transmits.  This 'disconnect package file' holds both the original compress auditd processed output with a file suffix of .data and a file containing metadata from the host forming the file. This metadata provides details such as the host's ip addresses, name server, storage detail, etc. The disconnect package file has the nomenclature

    E_auditProcessed.<randomvalue>.<creationtimestamp>.tar

and holds the files

    auditProcessed.<randomvalue>.<creationtimestamp>.gz.meta
    auditProcessed.<randomvalue>.<creationtimestamp>.gz.data

So, on the disconnected host, the steps would be

  - deploy as per normal, except change the cron entries within /etc/cron.d/stroom_auditd to have the additional argument, -P, to indicate that rather than post to a Stroom proxy, a disconnect package file is created in the outbound queue directory $STROOM_ROOT/queue.
  - collect the generated disconnected files from the outbound queue directory and transport them to the host that can post to a Stroom proxy

On, the connected host, the steps would be
  - deploy as per normal
  - create the disconnected inbound directory $STROOM_ROOT/disconnected. This CANNOT be the same as $STROOM_ROOT/queue
  - implement a process to deliver the disconnected files to $STROOM_ROOT/disconnected
  - modify the existing script execution in /etc/cron.d/stroom_auditd to change the max sleep to 5 minutes (300 seconds). i.e. add

       -d 300
to the script execution so it looks like (assuming $STROOM_ROOT is /opt/stroom/auditd)

        */10 * * * * root /opt/stroom/auditd/bin/stroom_auditd_feeder.sh -d 300 >> /var/log/stroom_auditd_auditing.log 2>&1

  - add an additional cron entry within stroom_auditd.crontab to have the additional arguments,

        -n -p $STROOM_ROOT/disconnected

    and offset it's execution by 6 minutes from the normal execution as per

        6-59/10 * * * * root /opt/stroom/auditd/bin/stroom_auditd_feeder.sh -n -p /opt/stroom/auditd/disconnected >> /var/log/stroom_auditd_auditing.log 2>&1

# Storage Imposts
  - Deployment size of approx 40K - `$STROOM_ROOT`
  - Temporary storage of up to 8.00GB for a period of 90 days (given failure of web service) within `$STROOM_ROOT`. This is the default if you need to change this, then edit `$STROOM_ROOT/bin/stroom_auditd_feeder.sh` and change one or both of the FAILED_RETENTION and FAILED_MAX environment variables or use the -R or -M options to change these values

# Prerequisites
  - requires recent audit and audit-lib packages (more recent that release 2.4.0)
  - requires the bind-utils, coreutils, gawk, curl, net-tools, gzip and sed packages
  - optionally can use the aushape capability if installed. This utility can format auditd logs into XML. Details can be found in https://github.com/Scribery/aushape. The use of this utility will mean for more efficient processing by the central Stroom repository as it will not have to transform the line orientated ausearch -i output into XML

# Capability Workflow
The workflow is such that, every 10 minutes cron starts a script which
  - delays randomly between 7 and 590 seconds before collecting audit data in order to balance network load. One does want many Linux systems 'pulsing' the network every 10 minutes. Note the 10 minute period is configurable. Just change the cron entry times as well as the max_sleep (-d argument). See stroom_auditd.crontab for more information
  - runs the ausearch command, using checkpoints, to collect all audit since ausearch's last invocation.
  - optionally run the aushape command to convert the ausearch output into XML
  - the resultant collected audit is gzip'd and saved in a file within a queue directory
  - all files in the queue directory are posted to the Stroom web service.

# Standard Manual Deployment
As there is a plethora of deployment mechanisms in available to Linux, this guide only provides the foundations of elements needed to deploy. This is in the form of a bash script. Using the following one could copy the following to a file in /tmp then execute the file. Clearly, one should ensure the script should be reviewed before doing so!

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
    
    # Check auditd version
    if command -v rpm > /dev/null 2>&1; then
      aversion=$(rpm -q --queryformat='%{VERSION}' audit 2>/dev/null | tr -d . | cut -c1-2)
    elif command -v dpkg-query > /dev/null 2>&1; then
      aversion=$(dpkg-query --show --showformat='${source:Upstream-Version}' auditd 2>/dev/null | tr -d . | cut -c1-2)
    else
      aversion=0
    fi

    if [ ${aversion:0} -le 24 ]; then
      echo "Auditd version ${aversion} too low. Upgrade via"
      echo "  yum upgrade audit audit-libs or dnf upgrade audit audit-libs or apt-get install auditd"
      errs=1
    fi
    
    # Consider the following changes for auditd configuration file /etc/audit/auditd.conf
    # - name_format = fqd (default NONE) ... can leave as default, but recommend setting to fqd, especially if audit.log
    #   files are aggregated on a central host before the stroom_auditd_agent.sh script is run
    # - num_logs = 9 (default 5) ... should set to 9 so have we have sufficient log files to accept an increase in audit
    #   events
    # - max_log_file = 32 (default 8) ... should set to 32 so have we have sufficient log file size (32MB) to accept an increase
    #   in audit events (combined with num_logs=9 means /var/log/audit will consume up to 288MB (9 x 32) of disk space
    # - max_log_file_action = ROTATE (default ROTATE) ... should already be ROTATE but make sure. We want the log files
    #   to rotate (to a max of 9 x 32MB)
    # - space_left_action = SYSLOG (default SYSLOG) ... should already be SYSLOG but make sure. We want to see warnings in
    #   syslog
    # - log_format = ENRICHED (default ENRICHED) ... should already be ENRICHED but make sure. We want to see enriched audit
    #   events in /var/log/audit.log.
    # - q_depth = 2000 (default 1200) ... should already be 2000 but make sure. We want to ensure we have a sufficiently large
    #   enough queue to handle a flood of events.
    # - end_of_event_timeout = 64 (default 2) ... should set to 64 based on empirical evidence (have seen event records emitted
    #   from the kernel almost 50 seconds after the first record!). Note this is not in RHEL7.
    echo "Changing recommended settings in /etc/audit/auditd.conf - backup to /etc/audit/auditd.conf.ORIG"
    cp -an /etc/audit/auditd.conf /etc/audit/auditd.conf.ORIG
    # We only need this one if you are forwarding logs to a syslog server, the stroom_auditd_feeder.sh script, inserts
    # the fqdn if not present in event log records
    # sed -i -e 's/^name_format = .*/name_format = fqd/g' /etc/audit/auditd.conf
    sed -i -e 's/^num_logs = .*/num_logs = 9/g' /etc/audit/auditd.conf
    sed -i -e 's/^max_log_file = .*/max_log_file = 32/g' /etc/audit/auditd.conf
    sed -i -e 's/^max_log_file_action = .*/max_log_file_action = ROTATE/g' /etc/audit/auditd.conf
    sed -i -e 's/^space_left_action = .*/space_left_action = SYSLOG/g' /etc/audit/auditd.conf
    sed -i -e 's/^log_format = .*/log_format = ENRICHED/g' /etc/audit/auditd.conf
    sed -i -e 's/^q_depth = .*/q_depth = 2000/g' /etc/audit/auditd.conf
    sed -i -e 's/^end_of_event_timeout = .*/end_of_event_timeout = 64/g' /etc/audit/auditd.conf
    
    #
    echo "Changes to auditd config"
    diff /etc/audit/auditd.conf /etc/audit/auditd.conf.ORIG

    # Auditd restart
    echo "Restarting auditd"
    service auditd restart

    # Check config of local file
    
    cp stroom_auditd_feeder.sh.base stroom_auditd_feeder.sh
    echo "Change URL variable in stroom_auditd_feeder.sh before proceeding"
    echo "Consider also changing SYSTEM and mySecZone variables"
    echo "All three variables URL, SYSTEM, mySecZone (and others) can be set in the configuration file - AUDIT_ROOT/config"
    
    # Double check
    egrep 'URL=https://stroom-proxy00.somedomain.org/stroom/datafeed' stroom_auditd_feeder.sh > /dev/null
    if [ $? -eq 0 ]; then
      echo "Change URL in stroom_auditd_feeder.sh before proceeding"
      echo "Consult local Audit team to gain appropriate URL and change 'stroom-proxy00.somedomain.org' to your Stroom Proxy's FQDN"
      errs=1
    fi
    
    if [ $errs -ne 0 ]; then
      echo Fix issues then return and restart tests
      exit 1
    else
      echo Proceed with installation or orchestration
    fi
    
    # We now install
    # NOTE that this is for a fresh installation, not an update.
    
    yum -y install curl bind-utils gzip net-tools sed gawk coreutils policycoreutils-python-utils cronie
    or 
    dnf -y install curl bind-utils gzip net-tools sed gawk coreutils policycoreutils-python-utils cronie
    
    # Optionally
    yum -y install facter
    or
    dnf -y install facter
    
    AUDIT_ROOT=/opt/stroom/auditd
    mkdir --mode=0750 --parents ${AUDIT_ROOT}
    mkdir --mode=0750 --parents ${AUDIT_ROOT}/bin
    mkdir --mode=0750 --parents ${AUDIT_ROOT}/queue
    mkdir --mode=0750 --parents ${AUDIT_ROOT}/locks
    sed -e "s+_AUDIT_ROOT_+${AUDIT_ROOT}+" stroom_auditd_feeder.sh > ${AUDIT_ROOT}/bin/stroom_auditd_feeder.sh
    chmod 750 ${AUDIT_ROOT}/bin/stroom_auditd_feeder.sh
    sed -e "s+_AUDIT_ROOT_+${AUDIT_ROOT}+" stroom_auditd_feeder.config.base > ${AUDIT_ROOT}/config
    chmod 640 ${AUDIT_ROOT}/config
    cp audit_logs.rotate /etc/logrotate.d/stroom_auditd
    chmod 644 /etc/logrotate.d/stroom_auditd
    sed -e "s+_AUDIT_ROOT_+${AUDIT_ROOT}+" stroom_auditd.crontab.base > /etc/cron.d/stroom_auditd
    chmod 644 /etc/cron.d/stroom_auditd
    
    # Note that lsb_release is not part of a minimal install, so since we only need this utility
    # for the following install steps, consider setting the R variable manually to either 6 or higher
    # depending on your release
    # R=$(lsb_release --release | sed -e 's/Release:[[:space:]]*//' | cut -f1 -d\.)
    # An alternate is available based on /etc/redhat-release for RHEL based systems

    R=$(sed -e 's/^.* release //' /etc/redhat-release | cut -f1 -d\.)
    if [ $R -eq 6 ]; then
      sed -e "s+_AUDIT_ROOT_+${AUDIT_ROOT}+" stroom_auditd_shutdown.init.d.base > /etc/init.d/stroom_auditd_shutdown
      chkconfig --add stroom_auditd_shutdown
      chkconfig stroom_auditd_shutdown on
      service stroom_auditd_shutdown start # This is done to get a lockfile so a shutdown can occur
    elif [ $R -ge 7 ]; then
      sed -e "s+_AUDIT_ROOT_+${AUDIT_ROOT}+" stroom_auditd_shutdown.service.base > /etc/systemd/system/stroom_auditd_shutdown.service
      chmod 644 /etc/systemd/system/stroom_auditd_shutdown.service
      systemctl enable stroom_auditd_shutdown.service --now
      chcon --reference /etc/systemd/system/default.target /etc/systemd/system/stroom_auditd_shutdown.service
      semanage fcontext -a -t tmpfs_t ${AUDIT_ROOT}/queue
      semanage fcontext -a -t bin_t "${AUDIT_ROOT}/bin.*"
      restorecon -Rv ${AUDIT_ROOT}
      systemctl daemon-reload
    fi
    
    # Initial test
    ${AUDIT_ROOT}/bin/stroom_auditd_feeder.sh -fn | tee --append /var/log/stroom_auditd_auditing.log
    
    echo System should be operational. Check /var/log/stroom_auditd_auditing.log

# RPM Deployment:

See the file README.rpmbuild on how to build a deployment rpm for el6 or el7 deployments. It has not be tested in a long time, so some work may be needed.

