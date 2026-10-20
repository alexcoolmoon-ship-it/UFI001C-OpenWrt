# SPDX-License-Identifier: GPL-2.0-only
include $(TOPDIR)/rules.mk
PKG_NAME:=ufi-modem-watchdog
PKG_VERSION:=1.0.0
PKG_RELEASE:=1
PKG_LICENSE:=GPL-2.0-only
include $(INCLUDE_DIR)/package.mk
define Package/ufi-modem-watchdog
  SECTION:=net
  CATEGORY:=Network
  TITLE:=UFI001C ModemManager wedge recovery watchdog
  DEPENDS:=+modemmanager +ubus +uci +jq
  PKGARCH:=all
endef
define Package/ufi-modem-watchdog/conffiles
/etc/config/ufi-modem-watchdog
endef
define Build/Compile
endef
define Package/ufi-modem-watchdog/install
	$(INSTALL_DIR) $(1)/usr/sbin $(1)/etc/init.d $(1)/etc/config
	$(INSTALL_BIN) ./files/ufi-modem-watchdog $(1)/usr/sbin/ufi-modem-watchdog
	$(INSTALL_BIN) ./files/init $(1)/etc/init.d/ufi-modem-watchdog
	$(INSTALL_CONF) ./files/config $(1)/etc/config/ufi-modem-watchdog
endef
$(eval $(call BuildPackage,ufi-modem-watchdog))
