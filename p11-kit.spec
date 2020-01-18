Name:           p11-kit
Version:        0.23.5
Release:        3%{?dist}
Summary:        Library for loading and sharing PKCS#11 modules

License:        BSD
URL:            http://p11-glue.freedesktop.org/p11-kit.html
Source0:        http://p11-glue.freedesktop.org/releases/p11-kit-%{version}.tar.gz
Source1:        trust-extract-compat
Patch0:		p11-kit-modifiable.patch
Patch1:		p11-kit-strerror.patch
Patch2:		p11-kit-oaep.patch
Patch3:		p11-kit-doc.patch

BuildRequires:  libtasn1-devel >= 2.3
BuildRequires:  nss-softokn-freebl
BuildRequires:	libffi-devel
BuildRequires:	gtk-doc

%description
p11-kit provides a way to load and enumerate PKCS#11 modules, as well
as a standard configuration setup for installing PKCS#11 modules in
such a way that they're discoverable.

%package devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

%package doc
Summary:        Documentation files for %{name}
BuildArch:	noarch

%description doc
The %{name}-doc package contains additional documentation for p11-kit
and developing applications to take advantage of it.

%package trust
Summary:        System trust module from %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires(post):   %{_sbindir}/update-alternatives
Requires(postun): %{_sbindir}/update-alternatives
Conflicts:        nss < 3.14.3-9

%description trust
The %{name}-trust package contains a system trust PKCS#11 module which
contains certificate anchors and black lists.


# solution taken from icedtea-web.spec
%define multilib_arches ppc64 sparc64 x86_64 s390x
%ifarch %{multilib_arches}
%define alt_ckbi  libnssckbi.so.%{_arch}
%else
%define alt_ckbi  libnssckbi.so
%endif


%prep
%autosetup -p1

%build
# These paths are the source paths that  come from the plan here:
# https://fedoraproject.org/wiki/Features/SharedSystemCertificates:SubTasks
%configure --disable-static --enable-doc --with-trust-paths=%{_sysconfdir}/pki/ca-trust/source:%{_datadir}/pki/ca-trust-source --with-hash-impl=freebl --disable-silent-rules
make %{?_smp_mflags} V=1

%install
make install DESTDIR=$RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/pkcs11/modules
rm -f $RPM_BUILD_ROOT%{_libdir}/*.la
rm -f $RPM_BUILD_ROOT%{_libdir}/pkcs11/*.la
install -p -m 755 %{SOURCE1} $RPM_BUILD_ROOT%{_libexecdir}/p11-kit/
# Install the example conf with %%doc instead
rm $RPM_BUILD_ROOT%{_sysconfdir}/pkcs11/pkcs11.conf.example
# We don't support PKCS#11 forwarding in RHEL-7 yet
rm -f $RPM_BUILD_ROOT%{_libexecdir}/p11-kit/p11-kit-server
rm -f $RPM_BUILD_ROOT%{_libdir}/pkcs11/p11-kit-client.so

%check
make check


%post -p /sbin/ldconfig

%post trust
%{_sbindir}/update-alternatives --install %{_libdir}/libnssckbi.so \
	%{alt_ckbi} %{_libdir}/pkcs11/p11-kit-trust.so 30

# Fix bad links from earlier p11-kit packages which didn't include s390x
%posttrans trust
%ifarch s390x
if %{_sbindir}/update-alternatives --display libnssckbi.so | grep -q lib64; then
    %{_sbindir}/update-alternatives --remove libnssckbi.so %{_libdir}/pkcs11/p11-kit-trust.so
    if test -e /usr/lib/nss/libnssckbi.so; then
        %{_sbindir}/update-alternatives --install /usr/lib/libnssckbi.so libnssckbi.so /usr/lib/nss/libnssckbi.so 10
    fi
fi
%endif

%postun -p /sbin/ldconfig

%postun trust
if [ $1 -eq 0 ] ; then
	# package removal
	%{_sbindir}/update-alternatives --remove %{alt_ckbi} %{_libdir}/pkcs11/p11-kit-trust.so
fi


%files
%doc AUTHORS COPYING NEWS README
%doc p11-kit/pkcs11.conf.example
%dir %{_sysconfdir}/pkcs11
%dir %{_sysconfdir}/pkcs11/modules
%dir %{_datadir}/p11-kit
%dir %{_datadir}/p11-kit/modules
%dir %{_libexecdir}/p11-kit
%{_bindir}/p11-kit
%{_libdir}/libp11-kit.so.*
%{_libdir}/p11-kit-proxy.so
%{_libexecdir}/p11-kit/p11-kit-remote
%{_mandir}/man8/p11-kit.8.gz
%{_mandir}/man5/pkcs11.conf.5.gz

%files devel
%{_includedir}/p11-kit-1/
%{_libdir}/libp11-kit.so
%{_libdir}/pkgconfig/p11-kit-1.pc

%files doc
%doc %{_datadir}/gtk-doc/

%files trust
%{_bindir}/trust
%{_mandir}/man1/trust.1.gz
%{_libdir}/pkcs11/p11-kit-trust.so
%{_datadir}/p11-kit/modules/p11-kit-trust.module
%{_libexecdir}/p11-kit/trust-extract-compat


%changelog
* Mon Jun 12 2017 Daiki Ueno <dueno@redhat.com> - 0.23.5-3
- Avoid reference to thread-unsafe strerror rhbz#1378947
- Fix PKCS#11 OAEP interface rhbz#1191209
- Update documentation to follow RFC7512 rhbz#1165977

* Thu May 18 2017 Daiki Ueno <dueno@redhat.com> - 0.23.5-2
- Make "trust anchor --remove" work again

* Mon Mar  6 2017 Daiki Ueno <dueno@redhat.com> - 0.23.5-1
- Rebase to upstream version 0.23.5

* Wed Feb 22 2017 Daiki Ueno <dueno@redhat.com> - 0.23.4-1
- Rebase to upstream version 0.23.4

* Thu Jan 08 2015 Stef Walter <stefw@redhat.com> - 0.20.7-3
- Fix incorrect alternative links for s390 and s390x rhbz#1174178

* Sun Oct 05 2014 Stef Walter <stefw@redhat.com> - 0.20.7-2
- Fix deadlock related to forking and pthread_atfork rhbz#1148774

* Thu Sep 18 2014 Stef Walter <stefw@redhat.com> - 0.20.7-1
- Update to upstream stable 0.20.7 release
- Expose pkcs11x.h header and defines for attached extensions rhbz#1142305

* Tue Sep 09 2014 Stef Walter <stefw@redhat.com> - 0.20.6-1
- Update to upstream stable 0.20.6 release
- Respect critical = no in p11-kit-proxy.so rhbz#1128615

* Fri Sep 05 2014 Stef Walter <stefw@redhat.com> - 0.20.5-1
- Update to upstream version 0.20.5
- Fixes several issues highlighted at rhbz#1128218

* Thu Aug 07 2014 Stef Walter <stefw@redhat.com> - 0.20.4-1
- Rebase to upstream version 0.20.x (#1122528)

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 0.18.7-4
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 0.18.7-3
- Mass rebuild 2013-12-27

* Mon Nov 04 2013 Stef Walter <stefw@redhat.com> - 0.18.7-2
- Move devel docs into subpackage due to gtk-doc multilib incompatibility (#983176)

* Thu Oct 10 2013 Stef Walter <stefw@redhat.com> - 0.18.7-1
- Update to new upstream point release for RHEL bug fixes

* Thu Jul 18 2013 Stef Walter <stefw@redhat.com> - 0.18.5-1
- Update to new upstream point release
- Use freebl for hash algorithms
- Don't load configs in home dir when setuid or setgid
- Use $TMPDIR instead of $TEMP while testing
- Open files and fds with O_CLOEXEC
- Abort initialization if critical module fails to load
- Don't use thread-unsafe: strerror, getpwuid
- Fix p11_kit_space_strlen() result when empty string

* Tue Jun 25 2013 Stef Walter <stefw@redhat.com> - 0.18.4-1
- Fix running the extract-trust external command

* Wed Jun 05 2013 Stef Walter <stefw@redhat.com> - 0.18.3-1
- Update to new upstream stable release
- Fix intermittent firefox cert validation issues (#960230)
- Include the manual pages in the package

* Tue May 14 2013 Stef Walter <stefw@redhat.com> - 0.18.2-1
- Update to new upstream stable release
- Reduce the libtasn1 dependency minimum version

* Thu May 02 2013 Stef Walter <stefw@redhat.com> - 0.18.1-1
- Update to new upstream stable release
- 'p11-kit extract-trust' lives in libdir

* Thu Apr 04 2013 Stef Walter <stefw@redhat.com> - 0.18.0-1
- Update to new upstream stable release
- Various logging tweaks (#928914, #928750)
- Make the 'p11-kit extract-trust' explicitly reject
  additional arguments

* Fri Mar 29 2013 Stef Walter <stefw@redhat.com> - 0.17.5-2
- Fix problem with empathy connecting to Google Talk (#928913)

* Thu Mar 28 2013 Stef Walter <stefw@redhat.com> - 0.17.5-1
- Make 'p11-kit extract-trust' call update-ca-trust
- Work around 32-bit oveflow of certificate dates
- Build fixes

* Tue Mar 26 2013 Stef Walter <stefw@redhat.com> - 0.17.4-2
- Pull in patch from upstream to fix build on ppc (#927394)

* Wed Mar 20 2013 Stef Walter <stefw@redhat.com> - 0.17.4-1
- Update to upstream version 0.17.4

* Mon Mar 18 2013 Stef Walter <stefw@redhat.com> - 0.17.3-1
- Update to upstream version 0.17.3
- Put the trust input paths in the right order

* Tue Mar 12 2013 Stef Walter <stefw@redhat.com> - 0.16.4-1
- Update to upstream version 0.16.4

* Fri Mar 08 2013 Stef Walter <stefw@redhat.com> - 0.16.3-1
- Update to upstream version 0.16.3
- Split out system trust module into its own package.
- p11-kit-trust provides an alternative to an nss module

* Tue Mar 05 2013 Stef Walter <stefw@redhat.com> - 0.16.1-1
- Update to upstream version 0.16.1
- Setup source directories as appropriate for Shared System Certificates feature

* Tue Mar 05 2013 Stef Walter <stefw@redhat.com> - 0.16.0-1
- Update to upstream version 0.16.0

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.14-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Mon Sep 17 2012 Kalev Lember <kalevlember@gmail.com> - 0.14-1
- Update to 0.14

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.13-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jul 16 2012 Kalev Lember <kalevlember@gmail.com> - 0.13-1
- Update to 0.13

* Tue Mar 27 2012 Kalev Lember <kalevlember@gmail.com> - 0.12-1
- Update to 0.12
- Run self tests in %%check

* Sat Feb 11 2012 Kalev Lember <kalevlember@gmail.com> - 0.11-1
- Update to 0.11

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Dec 20 2011 Matthias Clasen <mclasen@redhat.com> - 0.9-1
- Update to 0.9

* Wed Oct 26 2011 Kalev Lember <kalevlember@gmail.com> - 0.8-1
- Update to 0.8

* Mon Sep 19 2011 Matthias Clasen <mclasen@redhat.com> - 0.6-1
- Update to 0.6

* Sun Sep 04 2011 Kalev Lember <kalevlember@gmail.com> - 0.5-1
- Update to 0.5

* Sun Aug 21 2011 Kalev Lember <kalevlember@gmail.com> - 0.4-1
- Update to 0.4
- Install the example config file to documentation directory

* Wed Aug 17 2011 Kalev Lember <kalevlember@gmail.com> - 0.3-2
- Tighten -devel subpackage deps (#725905)

* Fri Jul 29 2011 Kalev Lember <kalevlember@gmail.com> - 0.3-1
- Update to 0.3
- Upstream rewrote the ASL 2.0 bits, which makes the whole package
  BSD-licensed

* Tue Jul 12 2011 Kalev Lember <kalevlember@gmail.com> - 0.2-1
- Initial RPM release
