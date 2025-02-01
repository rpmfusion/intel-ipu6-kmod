%if 0%{?fedora}
%global buildforkernels akmod
%global debug_package %{nil}
%endif

%global ipu6_commit 13c466ebdaaa0578e82bf3039b63eb0b3f472b72
%global ipu6_commitdate 20250115
%global ipu6_shortcommit %(c=%{ipu6_commit}; echo ${c:0:7})

%global usbio_commit 450939ff5f8af733bc89c564603222a4d420acf3
%global usbio_commitdate 20241210
%global usbio_shortcommit %(c=%{usbio_commit}; echo ${c:0:7})

%global prjname intel-ipu6

Name:           %{prjname}-kmod
Summary:        Kernel module (kmod) for %{prjname}
Version:        0.0
Release:        19.%{ipu6_commitdate}git%{ipu6_shortcommit}%{?dist}
License:        GPL-2.0-or-later
URL:            https://github.com/intel/ipu6-drivers

Source0:        https://github.com/intel/ipu6-drivers/archive/%{ipu6_commit}/ipu6-drivers-%{ipu6_shortcommit}.tar.gz
Source1:        https://github.com/intel/usbio-drivers/archive/%{usbio_commit}/usbio-drivers-%{usbio_shortcommit}.tar.gz

# Patches
# https://github.com/intel/ipu6-drivers/pull/322
Patch1:         0001-Makefile-Switch-sensor-driver-symbols-from-CONFIG_VI.patch
Patch2:         0002-Makefile-Re-enable-gc5035-compilation-with-kernels-6.patch
Patch3:         0003-Makefile-Do-not-build-hi556-driver-with-kernels-6.10.patch
Patch4:         0004-Makefile-Do-not-build-ov01a10-driver-with-kernels-6..patch
# https://github.com/intel/ipu6-drivers/pull/321
Patch5:         0005-media-ipu6-Fix-out-of-tree-builds.patch
Patch6:         0006-media-ipu6-Fix-building-with-kernel-6.13.patch
Patch7:         0007-Modify-0001-v6.10-IPU6-headers-used-by-PSYS.patch-fo.patch
# https://github.com/intel/ipu6-drivers/pull/324
Patch8:         0008-ipu6-psys-Adjust-DMA-code-for-ipu6-bus-DMA-changes-i.patch
Patch9:         0009-Add-ipu6-dma.h-to-0001-v6.10-IPU6-headers-used-by-PS.patch

# https://github.com/intel/usbio-drivers/pull/33
Patch10:        0010-usbio-Fix-GPIO-and-I2C-driver-modaliases.patch
# https://github.com/intel/usbio-drivers/pull/34
Patch11:        0011-usbio-Fix-I2C-max-transfer-size.patch
Patch12:        0012-usbio-Use-MAX_PAYLOAD_BSIZE-in-usbio_bulk_write.patch

# Downstream / Fedora specific patches
Patch101:       0101-Fedora-local-mod-integrate-usbio-drivers-within-ipu6.patch

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
%patch 5 -p1
%patch 6 -p1
%patch 7 -p1
%patch 8 -p1
%patch 9 -p1
%patch 101 -p1
patch -p1 < patches/0001-v6.10-IPU6-headers-used-by-PSYS.patch
)
(cd usbio-drivers-%{usbio_commit}
%patch 10 -p1
%patch 11 -p1
%patch 12 -p1
)

cp -Rp usbio-drivers-%{usbio_commit}/drivers ipu6-drivers-%{ipu6_commit}/
cp -Rp usbio-drivers-%{usbio_commit}/include ipu6-drivers-%{ipu6_commit}/

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
  mkdir -p %{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/drivers/media/pci/intel/ipu6/psys/
  install -m 755 _kmod_build_${kernel_version%%___*}/drivers/media/i2c/*.ko %{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/drivers/media/i2c/
  install -m 755 _kmod_build_${kernel_version%%___*}/drivers/media/pci/intel/ipu6/psys/*.ko %{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/drivers/media/pci/intel/ipu6/psys/
  install -m 755 _kmod_build_${kernel_version%%___*}/*.ko %{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}
done
%{?akmod_install}


%changelog
* Thu Jan 30 2025 Hans de Goede <hdegoede@redhat.com> - 0.0-19.20250115git13c466e
- Update to latest upstream
- Drop iVSC drivers, these are part of the mainline kernel now
- Integrate USBIO drivers for IO chip used on Meteor Lake models
- Now only builds psys and always uses isys from mainline
- Fix building against 6.13 kernels

* Wed Jan 29 2025 RPM Fusion Release Engineering <sergiomb@rpmfusion.org> - 0.0-18.20240624gitaecec2a
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Tue Oct 15 2024 Hans de Goede <hdegoede@redhat.com> - 0.0-17.20240624gitaecec2a
- Fix building against 6.12 kernels

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
