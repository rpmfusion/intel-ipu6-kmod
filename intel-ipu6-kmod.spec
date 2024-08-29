%if 0%{?fedora}
%global buildforkernels akmod
%global debug_package %{nil}
%endif

%global ipu6_commit aecec2aaef069fea56aa921cf5d7e449bb7a0b82
%global ipu6_commitdate 20240624
%global ipu6_shortcommit %(c=%{ipu6_commit}; echo ${c:0:7})

%global ivsc_commit a6dccbbf5a955489d20d996234b6ebb481183ed7
%global ivsc_commitdate 20240416
%global ivsc_shortcommit %(c=%{ivsc_commit}; echo ${c:0:7})

%global prjname intel-ipu6

Name:           %{prjname}-kmod
Summary:        Kernel module (kmod) for %{prjname}
Version:        0.0
Release:        16.%{ipu6_commitdate}git%{ipu6_shortcommit}%{?dist}
License:        GPLv2+
URL:            https://github.com/intel/ipu6-drivers

Source0:        %{url}/ivsc-driver/archive/%{ivsc_commit}/ivsc-driver-%{ivsc_shortcommit}.tar.gz
Source1:        %{url}/ipu6-drivers/archive/%{ipu6_commit}/ipu6-drivers-%{ipu6_shortcommit}.tar.gz

# Patches
# https://github.com/intel/ipu6-drivers/pull/239
Patch1:         0001-gc5035-Fix-compilation-with-kernels-6.8.patch
# https://github.com/intel/ipu6-drivers/pull/242
Patch2:         0002-media-ipu6-Fix-compilation-with-kernels-6.10.patch
# https://github.com/intel/ipu6-drivers/pull/243
Patch3:         0003-Makefile-prefix-ipu6-modules-with-icamera-instead-of.patch
# https://github.com/intel/ipu6-drivers/pull/261
Patch4:         0004-fix-6.11-kernel.patch

# Downstream / Fedora specific patches
Patch101:       0101-Makefile-Adjust-which-modules-to-build-for-which-ker.patch

BuildRequires:  gcc
BuildRequires:  elfutils-libelf-devel
BuildRequires:  kmodtool
%{!?kernels:BuildRequires: buildsys-build-rpmfusion-kerneldevpkgs-%{?buildforkernels:%{buildforkernels}}%{!?buildforkernels:current}-%{_target_cpu} }

# kmodtool does its magic here
%{expand:%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{prjname} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
This enables intel IPU6 image processor. The package includes Intel IPU6
and iVSC drivers.


%prep
# error out if there was something wrong with kmodtool
%{?kmodtool_check}

# print kmodtool output for debugging purposes:
kmodtool  --target %{_target_cpu} --repo rpmfusion --kmodname %{prjname} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null

%setup -q -c -a 1
(cd ipu6-drivers-%{ipu6_commit}
%patch 1 -p1
%patch 2 -p1
%patch 3 -p1
%patch 4 -p1
%patch 101 -p1
)


cp -Rp ivsc-driver-%{ivsc_commit}/backport-include ipu6-drivers-%{ipu6_commit}/
cp -Rp ivsc-driver-%{ivsc_commit}/drivers ipu6-drivers-%{ipu6_commit}/
cp -Rp ivsc-driver-%{ivsc_commit}/include ipu6-drivers-%{ipu6_commit}/

for kernel_version in %{?kernel_versions} ; do
  cp -a ipu6-drivers-%{ipu6_commit}/ _kmod_build_${kernel_version%%___*}
done


%build
for kernel_version in %{?kernel_versions} ; do
  make -C ${kernel_version##*___} M=${PWD}/_kmod_build_${kernel_version%%___*} modules
done

%install
for kernel_version in %{?kernel_versions}; do
  mkdir -p %{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/drivers/media/i2c/
  mkdir -p %{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/drivers/media/pci/intel/ipu6/
  install -m 755 _kmod_build_${kernel_version%%___*}/drivers/media/i2c/*.ko %{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/drivers/media/i2c/
  install -m 755 _kmod_build_${kernel_version%%___*}/drivers/media/pci/intel/ipu6/*.ko %{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/drivers/media/pci/intel/ipu6/
  if [ -f _kmod_build_${kernel_version%%___*}/intel_vsc.ko* ]; then
    install -m 755 _kmod_build_${kernel_version%%___*}/*.ko %{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}
  fi
done
%{?akmod_install}


%changelog
* Thu Aug 29 2024 Hans de Goede <hdegoede@redhat.com> - 0.0-16.20240624gitaecec2a
- Fix building against 6.11 kernels

* Fri Aug 02 2024 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 0.0-15.20240624gitaecec2a
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Thu Jun 27 2024 Hans de Goede <hdegoede@redhat.com> - 0.0-14.20240624gitaecec2a
- Updated ipu6-driver to commit aecec2aaef069fea56aa921cf5d7e449bb7a0b82
- Adjust which modules are build to not conflict with upstreamed ivsc,
  ov01a10, ov2740 and hi556 drivers
- Fix building against 6.10 kernels

* Fri Apr 19 2024 Kate Hsuan <hpa@redhat.cpm> - 0.0-13.20240226gitfb4c170
- Update ivsc to commit a6dccbbf5a955489d20d996234b6ebb481183ed7
- ivsc: Update mei_dev.h for kernel >= 6.8

* Thu Mar 07 2024 Kate Hsuan <hpa@redhat.com> - 0.0-12.20240226gitfb4c170
- Fix for kernel >= 6.7
- Fix and improve ipu6_isys probe()
- Skip ljca driver when the system runs the kernel >= 6.7

* Sun Feb 04 2024 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 0.0-11.20230622git8e41080
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sat Nov  4 2023 Hans de Goede <hdegoede@redhat.com> - 0.0-10.20230622git8e41080
- Add "spi_vsc: Call acpi_dev_clear_dependencies()" patch to fix laptops
  with iVSC chip no longer working with 6.6 kernels

* Tue Oct 10 2023 Hans de Goede <hdegoede@redhat.com> - 0.0-9.20230622git8e41080
- Updated ivsc-driver to commit e8ea8b825217091fa91c9b3cb68cee4101d416e2
- This fixes the camera not working on some Dell laptops
- Update patch to fix building against 6.6 kernels

* Thu Aug 31 2023 Kate Hsuan <hpa@redhat.com> - 0.0-8.20230622git8e41080
- Support for 6.6 kernel

* Tue Aug 29 2023 Kate Hsuan <hpa@redhat.com> - 0.0-7.20230622git8e41080
- Support for 6.5 kernel

* Mon Aug 7 2023 Kate Hsuan <hpa@redhat.com> - 0.0-6.20230622git8e41080
- Updated ipu6-driver to commit 8e410803b5d31c2c5bf32961f786d205ba6acc5d
- Updated ivsc-driver to commit cce4377f1539f3e7e8d8b45fbe23e87828ed1deb

* Thu Aug 03 2023 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 0.0-5.20230220gitdfedab0
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Wed May 10 2023 Kate Hsuan <hpa@redhat.com> - 0.0-4.20230220gitdfedab0
- Updated ipu6-driver commit to dfedab03f3856010d37968cb384696038c73c984
- Updated ivsc-driver commit to c8db12b907e2e455d4d5586e5812d1ae0eebd571

* Tue Mar 28 2023 Kate Hsuan <hpa@redhat.com> - 0.0-3.20230117gitf83b074
- Fix typo

* Mon Feb 6 2023 Kate Hsuan <hpa@redhat.com> - 0.0-2.20230117gitf83b074
- Update ipu6 and ivsc driver

* Wed Oct 26 2022 Kate Hsuan <hpa@redhat.com> - 0.0.1
- First release
