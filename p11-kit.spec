Name:           p11-kit
Version:        0.18.5
Release:        2%{?dist}.2
Summary:        Library for loading and sharing PKCS#11 modules

License:        BSD
URL:            http://p11-glue.freedesktop.org/p11-kit.html
Source0:        http://p11-glue.freedesktop.org/releases/p11-kit-%{version}.tar.gz
Source1:        p11-kit-extract-trust.in
Source2:        p11-kit-redhat-setup-trust.in
Patch10:        0001-doc-Add-identifiers-to-doc-sections-so-gtk-doc-doesn.patch
BuildRequires:  libtasn1-devel >= 2.3
BuildRequires:  nss-softokn-freebl
BuildRequires:  gtk-doc

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


%package trust
Summary:        System trust module from %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       %{_sbindir}/update-alternatives
Requires(post):   %{_sbindir}/update-alternatives
Requires(post):   /bin/grep
Requires(postun): %{_sbindir}/update-alternatives
Conflicts:      nss < 3.14.3-33

%description trust
The %{name}-trust package contains a system trust PKCS#11 module which
contains certificate anchors and black lists.


# solution taken from icedtea-web.spec
%define multilib_arches ppc64 sparc64 x86_64 s390x
%ifarch %{multilib_arches}
%define arch_suffix  .%{_arch}
%else
%define arch_suffix  %{nil}
%endif

# for building scripts (grumble, rpm multiline-macro broken)
%define sed_script sed -e 's,@bindir@,%{_bindir},g' -e 's,@sbindir@,%{_sbindir},g' -e 's,@libdir@,%{_libdir},g' -e 's,@arch_suffix@,%{arch_suffix},g'

%prep
%setup -q
%patch10 -p1 -b .add-ids

%build
# These paths are the source paths that  come from the plan here:
# https://fedoraproject.org/wiki/Features/SharedSystemCertificates:SubTasks
%configure --disable-static --enable-doc --with-trust-paths=%{_sysconfdir}/pki/ca-trust/source:%{_datadir}/pki/ca-trust-source --with-hash-impl=freebl --with-user-config='~/.config/pkcs11'
make %{?_smp_mflags} V=1
%{sed_script} %{SOURCE1} > p11-kit-extract-trust
%{sed_script} %{SOURCE2} > p11-kit-redhat-setup-trust

%install
make install DESTDIR=$RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/pkcs11/modules
rm -f $RPM_BUILD_ROOT%{_libdir}/*.la
rm -f $RPM_BUILD_ROOT%{_libdir}/pkcs11/*.la
install -p -m 755 p11-kit-extract-trust $RPM_BUILD_ROOT%{_libdir}/p11-kit/
install -p -m 755 p11-kit-redhat-setup-trust $RPM_BUILD_ROOT%{_libdir}/p11-kit/
# Install the example conf with %%doc instead
rm $RPM_BUILD_ROOT%{_sysconfdir}/pkcs11/pkcs11.conf.example

%check
make check


%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%post trust
# On multilib systems packages of different p11-kit-trust can be installed
# independently from each other. After installing a p11-kit-trust.rpm package
# we'll check if the paired multilib package is currently enabled, and enable
# this one if so.
%{_libdir}/p11-kit/p11-kit-redhat-setup-trust status | grep -q "for other arch"
if test $? -eq 0; then
	%{_libdir}/p11-kit/p11-kit-redhat-setup-trust enable
fi	

%postun trust
# We cannot rely on the $1 parameter, because it's a summary of all packages
# in a multilib scenario. So double check if our package is installed.
if ! test -e %{_libdir}/pkcs11/p11-kit-trust.so; then
	%{_sbindir}/update-alternatives --remove libnssckbi.so%{arch_suffix} %{_libdir}/pkcs11/p11-kit-trust.so
fi

%files
%doc AUTHORS COPYING NEWS README
%doc p11-kit/pkcs11.conf.example
%dir %{_sysconfdir}/pkcs11
%dir %{_sysconfdir}/pkcs11/modules
%dir %{_datadir}/p11-kit
%dir %{_datadir}/p11-kit/modules
%dir %{_libdir}/p11-kit
%{_bindir}/p11-kit
%{_libdir}/libp11-kit.so.*
%{_libdir}/p11-kit-proxy.so
%{_mandir}/man8/p11-kit.8.gz
%{_mandir}/man5/pkcs11.conf.5.gz

%files devel
%{_includedir}/p11-kit-1/
%{_libdir}/libp11-kit.so
%{_libdir}/pkgconfig/p11-kit-1.pc
%doc %{_datadir}/gtk-doc/

%files trust
%{_libdir}/pkcs11/p11-kit-trust.so
%{_datadir}/p11-kit/modules/p11-kit-trust.module
%{_libdir}/p11-kit/p11-kit-extract-trust
%{_libdir}/p11-kit/p11-kit-redhat-setup-trust

%changelog
* Thu Jan 16 2014 Stef Walter <stefw@redhat.com> - 0.18.5-2.2
- Fix path for grep (#1039930)

* Tue Jan 07 2014 Stef Walter <stefw@redhat.com> - 0.18.5-2.1
- Add missing dependency on grep (#1039930)

* Thu Jul 18 2013 Stef Walter <stefw@redhat.com> - 0.18.5-2
- Fix problem with multilib conflicts (generated docbook ids)

* Thu Jul 18 2013 Stef Walter <stefw@redhat.com> - 0.18.5-1
- Update to new upstream point release
- Use freebl for hash algorithms (#983384)
- Don't load configs in home dir when setuid or setgid (#985816)
- Use $TMPDIR instead of $TEMP while testing (#985017)
- Use $XDG_DATA_HOME for user pkcs11 module configuration
- Open files and fds with O_CLOEXEC (#984986)
- Abort initialization if critical module fails to load (#985023)
- Don't use thread-unsafe: strerror, getpwuid (#985481)
- Fix p11_kit_space_strlen() result when empty string (#985416)

* Tue Jul 02 2013 Stef Walter <stefw@redhat.com> - 0.18.4-2
- Fix inconsistency issues when multilib packages are installed
- Add 'p11-kit redhat-setup-trust status' command

* Tue Jun 25 2013 Stef Walter <stefw@redhat.com> - 0.18.4-1
- Remove alternative on package removal
- Update to 0.18.4 with minor p11-kit command fixes
- Fix arguments to extract-trust p11-kit command

* Fri Jun 14 2013 Stef Walter <stefw@redhat.com> - 0.18.3-3
- Don't depend on wrong bash location
- Install script to enable alternative libnssckbi.so

* Wed Jun 12 2013 Stef Walter <stefw@redhat.com> - 0.18.3-2
- Don't install libnssckbi.so alternatives in the package.
  On RHEL 6 this is done by the update-ca-trust script.

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
