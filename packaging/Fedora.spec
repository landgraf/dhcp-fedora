# SystemTap support is disabled by default
%{!?sdt:%global sdt 0}

#http://lists.fedoraproject.org/pipermail/devel/2011-August/155358.html
%global _hardened_build 1

# Where dhcp configuration files are stored
%global dhcpconfdir %{_sysconfdir}/dhcp


#global prever b1
#global patchver P1
%global DHCPVERSION %{version}%{?prever}%{?patchver:-%{patchver}}


Summary:  Dynamic host configuration protocol software
Name:     dhcp
Version:  4.4.1
Release:  1%{?dist}
# NEVER CHANGE THE EPOCH on this package.  The previous maintainer (prior to
# dcantrell maintaining the package) made incorrect use of the epoch and
# that's why it is at 12 now.  It should have never been used, but it was.
# So we are stuck with it.
Epoch:    12
License:  ISC
Url:      http://isc.org/products/DHCP/
Source0:  ftp://ftp.isc.org/isc/dhcp/%{DHCPVERSION}/dhcp-%{DHCPVERSION}.tar.gz
Source1:  dhclient-script
Source2:  README.dhclient.d
Source3:  11-dhclient
Source4:  12-dhcpd
Source5:  56dhclient
Source6:  dhcpd.service
Source7:  dhcpd6.service
Source8:  dhcrelay.service


BuildRequires: autoconf
BuildRequires: automake
BuildRequires: libtool
BuildRequires: openldap-devel
# --with-ldap-gssapi
BuildRequires: krb5-devel
BuildRequires: libcap-ng-devel
# https://fedorahosted.org/fpc/ticket/502#comment:3
BuildRequires: bind-export-devel
BuildRequires: systemd systemd-devel
# dhcp-sd_notify.patch
BuildRequires: pkgconfig(libsystemd)
%if ! 0%{?_module_build}
BuildRequires: doxygen
%endif
%if %{sdt}
BuildRequires: systemtap-sdt-devel
%global tapsetdir    /usr/share/systemtap/tapset
%endif

# In _docdir we ship some perl scripts and module from contrib subdirectory.
# Because nothing under _docdir is allowed to "require" anything,
# prevent _docdir from being scanned. (#674058)
%filter_requires_in %{_docdir}
%{filter_setup}

%description
DHCP (Dynamic Host Configuration Protocol)

%package server
Summary: Provides the ISC DHCP server
Requires: %{name}-common = %{epoch}:%{version}-%{release}
Requires: %{name}-libs%{?_isa} = %{epoch}:%{version}-%{release}
Requires(pre): shadow-utils
Requires(post): coreutils grep sed
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description server
DHCP (Dynamic Host Configuration Protocol) is a protocol which allows
individual devices on an IP network to get their own network
configuration information (IP address, subnetmask, broadcast address,
etc.) from a DHCP server. The overall purpose of DHCP is to make it
easier to administer a large network.

This package provides the ISC DHCP server.

%package relay
Summary: Provides the ISC DHCP relay agent
Requires: %{name}-common = %{epoch}:%{version}-%{release}
Requires: %{name}-libs%{?_isa} = %{epoch}:%{version}-%{release}
Requires(post): grep sed
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description relay
DHCP (Dynamic Host Configuration Protocol) is a protocol which allows
individual devices on an IP network to get their own network
configuration information (IP address, subnetmask, broadcast address,
etc.) from a DHCP server. The overall purpose of DHCP is to make it
easier to administer a large network.

This package provides the ISC DHCP relay agent.

%package compat
Summary: Utility package to help transition
Provides:  dhcp = %{epoch}:%{version}-%{release}
Obsoletes: dhcp < %{epoch}:%{version}-%{release}
Requires:  %{name}-server = %{epoch}:%{version}-%{release}
Requires:  %{name}-relay = %{epoch}:%{version}-%{release}

%description compat
This package only exists to help transition dhcp users to the new
package split (dhcp -> dhcp & dhcrelay).
It will be removed after one distribution release cycle, please
do not reference it or depend on it in any way.

%package client
Summary: Provides the ISC DHCP client daemon and dhclient-script
Provides: dhclient = %{epoch}:%{version}-%{release}
Obsoletes: dhclient < %{epoch}:%{version}-%{release}
# dhclient-script requires:
Requires: coreutils gawk grep ipcalc iproute iputils sed systemd
Requires: %{name}-common = %{epoch}:%{version}-%{release}
Requires: %{name}-libs%{?_isa} = %{epoch}:%{version}-%{release}

%description client
DHCP (Dynamic Host Configuration Protocol) is a protocol which allows
individual devices on an IP network to get their own network
configuration information (IP address, subnetmask, broadcast address,
etc.) from a DHCP server. The overall purpose of DHCP is to make it
easier to administer a large network.

This package provides the ISC DHCP client.

%package common
Summary: Common files used by ISC dhcp client, server and relay agent
BuildArch: noarch

%description common
DHCP (Dynamic Host Configuration Protocol) is a protocol which allows
individual devices on an IP network to get their own network
configuration information (IP address, subnetmask, broadcast address,
etc.) from a DHCP server. The overall purpose of DHCP is to make it
easier to administer a large network.

This package provides common files used by dhcp and dhclient package.

%package libs
Summary: Shared libraries used by ISC dhcp client and server

%description libs
This package contains shared libraries used by ISC dhcp client and server


%package devel
Summary: Development headers and libraries for interfacing to the DHCP server
Requires: %{name}-libs%{?_isa} = %{epoch}:%{version}-%{release}

%description devel
Header files and API documentation for using the ISC DHCP libraries.  The
libdhcpctl and libomapi static libraries are also included in this package.

%if ! 0%{?_module_build}
%package devel-doc
Summary: Developer's Guide for ISC DHCP
Requires: %{name}-libs = %{epoch}:%{version}-%{release}
BuildArch: noarch

%description devel-doc
This documentation is intended for developers, contributors and other
programmers that are interested in internal operation of the code.
This package contains doxygen-generated documentation.
%endif

%prep
%autosetup -p1 -n dhcp-%{DHCPVERSION}

# DHCLIENT_DEFAULT_PREFIX_LEN  64 -> 128
# https://bugzilla.gnome.org/show_bug.cgi?id=656610
sed -i -e 's|DHCLIENT_DEFAULT_PREFIX_LEN 64|DHCLIENT_DEFAULT_PREFIX_LEN 128|g' includes/site.h

# Update paths in all man pages
for page in client/dhclient.conf.5 client/dhclient.leases.5 \
            client/dhclient-script.8 client/dhclient.8 ; do
    sed -i -e 's|CLIENTBINDIR|%{_sbindir}|g' \
                -e 's|RUNDIR|%{_localstatedir}/run|g' \
                -e 's|DBDIR|%{_localstatedir}/lib/dhclient|g' \
                -e 's|ETCDIR|%{dhcpconfdir}|g' $page
done

for page in server/dhcpd.conf.5 server/dhcpd.leases.5 server/dhcpd.8 ; do
    sed -i -e 's|CLIENTBINDIR|%{_sbindir}|g' \
                -e 's|RUNDIR|%{_localstatedir}/run|g' \
                -e 's|DBDIR|%{_localstatedir}/lib/dhcpd|g' \
                -e 's|ETCDIR|%{dhcpconfdir}|g' $page
done

sed -i -e 's|/var/db/|%{_localstatedir}/lib/dhcpd/|g' contrib/dhcp-lease-list.pl

%build
#libtoolize --copy --force
autoreconf --verbose --force --install

CFLAGS="%{optflags} -fno-strict-aliasing" \
%configure \
    --with-srv-lease-file=%{_localstatedir}/lib/dhcpd/dhcpd.leases \
    --with-srv6-lease-file=%{_localstatedir}/lib/dhcpd/dhcpd6.leases \
    --with-cli-lease-file=%{_localstatedir}/lib/dhclient/dhclient.leases \
    --with-cli6-lease-file=%{_localstatedir}/lib/dhclient/dhclient6.leases \
    --with-srv-pid-file=%{_localstatedir}/run/dhcpd.pid \
    --with-srv6-pid-file=%{_localstatedir}/run/dhcpd6.pid \
    --with-cli-pid-file=%{_localstatedir}/run/dhclient.pid \
    --with-cli6-pid-file=%{_localstatedir}/run/dhclient6.pid \
    --with-relay-pid-file=%{_localstatedir}/run/dhcrelay.pid \
    --with-libbind=/usr/bin/isc-export-config.sh \
    --with-ldap \
    --with-ldapcrypto \
    --with-ldap-gssapi \
    --disable-static \
    --enable-log-pid \
%if %{sdt}
    --enable-systemtap \
    --with-tapset-install-dir=%{tapsetdir} \
%endif
    --enable-paranoia --enable-early-chroot \
    --enable-binary-leases \
    --with-systemd
make %{?_smp_mflags}
%if ! 0%{?_module_build}
pushd doc
make %{?_smp_mflags} devel
popd
%endif

%install
make DESTDIR=%{buildroot} install %{?_smp_mflags}

# We don't want example conf files in /etc
rm -f %{buildroot}%{_sysconfdir}/dhclient.conf.example
rm -f %{buildroot}%{_sysconfdir}/dhcpd.conf.example

# dhclient-script
install -D -p -m 0755 %{SOURCE1} %{buildroot}%{_sbindir}/dhclient-script

# README.dhclient.d
install -p -m 0644 %{SOURCE2} .

# Empty directory for dhclient.d scripts
mkdir -p %{buildroot}%{dhcpconfdir}/dhclient.d

# NetworkManager dispatcher script
mkdir -p %{buildroot}%{_sysconfdir}/NetworkManager/dispatcher.d
install -p -m 0755 %{SOURCE3} %{buildroot}%{_sysconfdir}/NetworkManager/dispatcher.d
install -p -m 0755 %{SOURCE4} %{buildroot}%{_sysconfdir}/NetworkManager/dispatcher.d

# pm-utils script to handle suspend/resume and dhclient leases
install -D -p -m 0755 %{SOURCE5} %{buildroot}%{_libdir}/pm-utils/sleep.d/56dhclient

# systemd unit files
mkdir -p %{buildroot}%{_unitdir}
install -m 644 %{SOURCE6} %{buildroot}%{_unitdir}
install -m 644 %{SOURCE7} %{buildroot}%{_unitdir}
install -m 644 %{SOURCE8} %{buildroot}%{_unitdir}

# Start empty lease databases
mkdir -p %{buildroot}%{_localstatedir}/lib/dhcpd/
touch %{buildroot}%{_localstatedir}/lib/dhcpd/dhcpd.leases
touch %{buildroot}%{_localstatedir}/lib/dhcpd/dhcpd6.leases
mkdir -p %{buildroot}%{_localstatedir}/lib/dhclient/

# default sysconfig file for dhcpd
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
cat <<EOF > %{buildroot}%{_sysconfdir}/sysconfig/dhcpd
# WARNING: This file is NOT used anymore.

# If you are here to restrict what interfaces should dhcpd listen on,
# be aware that dhcpd listens *only* on interfaces for which it finds subnet
# declaration in dhcpd.conf. It means that explicitly enumerating interfaces
# also on command line should not be required in most cases.

# If you still insist on adding some command line options,
# copy dhcpd.service from /lib/systemd/system to /etc/systemd/system and modify
# it there.
# https://fedoraproject.org/wiki/Systemd#How_do_I_customize_a_unit_file.2F_add_a_custom_unit_file.3F

# example:
# $ cp /usr/lib/systemd/system/dhcpd.service /etc/systemd/system/
# $ vi /etc/systemd/system/dhcpd.service
# $ ExecStart=/usr/sbin/dhcpd -f -cf /etc/dhcp/dhcpd.conf -user dhcpd -group dhcpd --no-pid <your_interface_name(s)>
# $ systemctl --system daemon-reload
# $ systemctl restart dhcpd.service
EOF

# Copy sample conf files into position (called by doc macro)
cp -p doc/examples/dhclient-dhcpv6.conf client/dhclient6.conf.example
cp -p doc/examples/dhcpd-dhcpv6.conf server/dhcpd6.conf.example

cat << EOF > client/dhclient-enter-hooks
#!/bin/bash

# For dhclient/dhclient-script debugging.
# Copy this into /etc/dhcp/ and make it executable.
# Run 'dhclient -d <interface>' to see info passed from dhclient to dhclient-script.
# See also HOOKS section in dhclient-script(8) man page.

echo "interface: ${interface}"
echo "reason: ${reason}"

( set -o posix ; set ) | grep "old_"
( set -o posix ; set ) | grep "new_"
( set -o posix ; set ) | grep "alias_"
( set -o posix ; set ) | grep "requested_"
EOF

# Install default (empty) dhcpd.conf:
mkdir -p %{buildroot}%{dhcpconfdir}
cat << EOF > %{buildroot}%{dhcpconfdir}/dhcpd.conf
#
# DHCP Server Configuration file.
#   see /usr/share/doc/dhcp-server/dhcpd.conf.example
#   see dhcpd.conf(5) man page
#
EOF

# Install default (empty) dhcpd6.conf:
cat << EOF > %{buildroot}%{dhcpconfdir}/dhcpd6.conf
#
# DHCPv6 Server Configuration file.
#   see /usr/share/doc/dhcp-server/dhcpd6.conf.example
#   see dhcpd.conf(5) man page
#
EOF

# Install dhcp.schema for LDAP configuration
install -D -p -m 0644 contrib/ldap/dhcp.schema %{buildroot}%{_sysconfdir}/openldap/schema/dhcp.schema

# Don't package libtool *.la files
find %{buildroot} -type f -name "*.la" -delete -print

rm %{buildroot}%{_includedir}/isc-dhcp/dst.h

%pre server
# /usr/share/doc/setup/uidgid
%global gid_uid 177
getent group dhcpd >/dev/null || groupadd --force --gid %{gid_uid} --system dhcpd
if ! getent passwd dhcpd >/dev/null ; then
    if ! getent passwd %{gid_uid} >/dev/null ; then
      useradd --system --uid %{gid_uid} --gid dhcpd --home / --shell /sbin/nologin --comment "DHCP server" dhcpd
    else
      useradd --system --gid dhcpd --home / --shell /sbin/nologin --comment "DHCP server" dhcpd
    fi
fi
exit 0

%post server
# Initial installation
%systemd_post dhcpd.service dhcpd6.service


for servicename in dhcpd dhcpd6; do
  etcservicefile=%{_sysconfdir}/systemd/system/${servicename}.service
  if [ -f ${etcservicefile} ]; then
    grep -q Type= ${etcservicefile} || sed -i '/\[Service\]/a Type=notify' ${etcservicefile}
    sed -i 's/After=network.target/Wants=network-online.target\nAfter=network-online.target/' ${etcservicefile}
  fi
done
exit 0

%post relay
# Initial installation
%systemd_post dhcrelay.service

for servicename in dhcrelay; do
  etcservicefile=%{_sysconfdir}/systemd/system/${servicename}.service
  if [ -f ${etcservicefile} ]; then
    grep -q Type= ${etcservicefile} || sed -i '/\[Service\]/a Type=notify' ${etcservicefile}
    sed -i 's/After=network.target/Wants=network-online.target\nAfter=network-online.target/' ${etcservicefile}
  fi
done
exit 0

%preun server
# Package removal, not upgrade
%systemd_preun dhcpd.service dhcpd6.service

%preun relay
# Package removal, not upgrade
%systemd_preun dhcrelay.service


%postun server
# Package upgrade, not uninstall
%systemd_postun_with_restart dhcpd.service dhcpd6.service

%postun relay
# Package upgrade, not uninstall
%systemd_postun_with_restart dhcrelay.service

%ldconfig_scriptlets libs

%triggerun -- dhcp
# convert DHC*ARGS from /etc/sysconfig/dhc* to /etc/systemd/system/dhc*.service
for servicename in dhcpd dhcpd6 dhcrelay; do
  if [ -f %{_sysconfdir}/sysconfig/${servicename} ]; then
    # get DHCPDARGS/DHCRELAYARGS value from /etc/sysconfig/${servicename}
    source %{_sysconfdir}/sysconfig/${servicename}
    if [ "${servicename}" == "dhcrelay" ]; then
        args=$DHCRELAYARGS
    else
        args=$DHCPDARGS
    fi
    # value is non-empty (i.e. user modified) and there isn't a service unit yet
    if [ -n "${args}" -a ! -f %{_sysconfdir}/systemd/system/${servicename}.service ]; then
      # in $args replace / with \/ otherwise the next sed won't take it
      args=$(echo $args | sed 's/\//\\\//'g)
      # add $args to the end of ExecStart line
      sed -r -e "/ExecStart=/ s/$/ ${args}/" \
                < %{_unitdir}/${servicename}.service \
                > %{_sysconfdir}/systemd/system/${servicename}.service
    fi
  fi
done

%files server
%doc server/dhcpd.conf.example server/dhcpd6.conf.example
%doc contrib/ldap/ contrib/dhcp-lease-list.pl
%attr(0750,root,root) %dir %{dhcpconfdir}
%attr(0755,dhcpd,dhcpd) %dir %{_localstatedir}/lib/dhcpd
%attr(0644,dhcpd,dhcpd) %verify(mode) %config(noreplace) %{_localstatedir}/lib/dhcpd/dhcpd.leases
%attr(0644,dhcpd,dhcpd) %verify(mode) %config(noreplace) %{_localstatedir}/lib/dhcpd/dhcpd6.leases
%config(noreplace) %{_sysconfdir}/sysconfig/dhcpd
%config(noreplace) %{dhcpconfdir}/dhcpd.conf
%config(noreplace) %{dhcpconfdir}/dhcpd6.conf
%dir %{_sysconfdir}/openldap/schema
%config(noreplace) %{_sysconfdir}/openldap/schema/dhcp.schema
%dir %{_sysconfdir}/NetworkManager
%dir %{_sysconfdir}/NetworkManager/dispatcher.d
%{_sysconfdir}/NetworkManager/dispatcher.d/12-dhcpd
%attr(0644,root,root)   %{_unitdir}/dhcpd.service
%attr(0644,root,root)   %{_unitdir}/dhcpd6.service
%{_sbindir}/dhcpd
%{_bindir}/omshell
%attr(0644,root,root) %{_mandir}/man1/omshell.1.gz
%attr(0644,root,root) %{_mandir}/man5/dhcpd.conf.5.gz
%attr(0644,root,root) %{_mandir}/man5/dhcpd.leases.5.gz
%attr(0644,root,root) %{_mandir}/man8/dhcpd.8.gz
%if %{sdt}
%{tapsetdir}/*.stp
%endif

%files relay
%{_sbindir}/dhcrelay
%attr(0644,root,root) %{_unitdir}/dhcrelay.service
%attr(0644,root,root) %{_mandir}/man8/dhcrelay.8.gz

%files compat

%files client
%doc README.dhclient.d
%doc client/dhclient.conf.example client/dhclient6.conf.example client/dhclient-enter-hooks
%attr(0750,root,root) %dir %{dhcpconfdir}
%dir %{dhcpconfdir}/dhclient.d
%dir %{_localstatedir}/lib/dhclient
%dir %{_sysconfdir}/NetworkManager
%dir %{_sysconfdir}/NetworkManager/dispatcher.d
%{_sysconfdir}/NetworkManager/dispatcher.d/11-dhclient
%{_sbindir}/dhclient
%{_sbindir}/dhclient-script
%attr(0755,root,root) %{_libdir}/pm-utils/sleep.d/56dhclient
%attr(0644,root,root) %{_mandir}/man5/dhclient.conf.5.gz
%attr(0644,root,root) %{_mandir}/man5/dhclient.leases.5.gz
%attr(0644,root,root) %{_mandir}/man8/dhclient.8.gz
%attr(0644,root,root) %{_mandir}/man8/dhclient-script.8.gz

%files common
%{!?_licensedir:%global license %%doc}
%{license} LICENSE
%doc README RELNOTES doc/References.txt
%attr(0644,root,root) %{_mandir}/man5/dhcp-options.5.gz
%attr(0644,root,root) %{_mandir}/man5/dhcp-eval.5.gz

%files libs
%{_libdir}/libdhcpctl.so.*
%{_libdir}/libomapi.so.*

%files devel
%doc doc/IANA-arp-parameters doc/api+protocol
%{_includedir}/dhcpctl
%{_includedir}/omapip
%{_libdir}/libdhcpctl.so
%{_libdir}/libomapi.so
%attr(0644,root,root) %{_mandir}/man3/dhcpctl.3.gz
%attr(0644,root,root) %{_mandir}/man3/omapi.3.gz

%if ! 0%{?_module_build}
%files devel-doc
%doc doc/html/
%endif

%changelog

