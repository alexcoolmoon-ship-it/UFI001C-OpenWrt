# Проверка v3.2.5 Clean

Дополнительно к проверкам v3.2.4: службы восстановления ufi-lte-health и
ufi-modem-watchdog удалены из clean-профиля и покрыты запретом на всех
трёх воротах:

- `clean/ufi001c.config`: обе опции — `is not set`, пакеты не собираются.
- `check_config.py` (шаг CI перед компиляцией): `PACKAGE_ufi-lte-health`
  и `PACKAGE_ufi-modem-watchdog` в списке запрещённых — сборка упадёт,
  если их вернут в конфиг.
- `check_rootfs.py` (шаг CI после сборки rootfs): файлы
  `usr/sbin/ufi-lte-health`, `etc/init.d/ufi-lte-health`,
  `usr/share/ufi-lte-health/session.jq`, `usr/sbin/ufi-modem-watchdog`,
  `etc/init.d/ufi-modem-watchdog` в списке FORBIDDEN — сборка упадёт,
  если они окажутся в rootfs.
- `migration/stock_install.py`: установщик со стока отклоняет обе службы
  как неожиданные пакеты.

Юнит-тесты самих служб (tests/test_modem_watchdog.py,
tests/test_lte_recovery.py, tests/test_dns_health.py,
tests/test_apply_profile.py) оставлены: они проверяют код в overlay
в изоляции и зелёные, на состав прошивки не влияют.

Важно из аппаратного журнала v3.2.4 (21.10.2026, 07:13 MSK): сброс
подсистемы модема MSS (sys_m.c:603 THIS IS INTENTIONAL RESET) происходит
при первом включении модема при КАЖДОЙ загрузке — перенос rmtfs на
START=65 его не предотвратил. ModemManager при этом восстанавливается
сам: modem1 → registered → connected за ~50 секунд от включения питания,
без участия каких-либо сторожей. В том же журнале обе службы v3.2.4
не сделали ни одного действия — текущее отсутствие интернета находится
на уровне Podkop/прокси (bootstrap-DNS не резолвит имя прокси,
проверка GitHub не проходит), а не в модемной подсистеме.

Остальной объём проверок — как в VALIDATION-v3.2.4.md: контрольные суммы
снимка Podkop и изменённых файлов, CI установщика, ARM64 podkop-engine под
QEMU (DoH через туннель, FakeIP, кнопка Cloudflare, устойчивость к SERVFAIL),
проверки конфигурации XHTTP, обязательные опции маршрутизации в ядре, хэши
образов и пара «архив + sha256» в релизе.
