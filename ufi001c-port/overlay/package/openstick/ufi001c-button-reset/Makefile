# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk

PKG_NAME:=ufi001c-button-reset
PKG_VERSION:=1
PKG_RELEASE:=1

include $(INCLUDE_DIR)/package.mk

define Package/ufi001c-button-reset
  SECTION:=utils
  CATEGORY:=Utilities
  TITLE:=Button-hold factory reset for OpenStick UFI001C
  DEPENDS:=+kmod-button-hotplug
  PKGARCH:=all
endef

define Build/Compile
endef

define Package/ufi001c-button-reset/install
	$(INSTALL_DIR) $(1)/etc/hotplug.d/button
	$(INSTALL_BIN) ./files/etc/hotplug.d/button/10-ufi001c-reset $(1)/etc/hotplug.d/button/
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) ./files/usr/sbin/ufi001c-factory-reset $(1)/usr/sbin/
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/etc/uci-defaults/99-ufi001c-factory-snapshot $(1)/etc/uci-defaults/
endef

$(eval $(call BuildPackage,ufi001c-button-reset))
