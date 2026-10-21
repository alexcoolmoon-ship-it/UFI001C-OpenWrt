# Проверка v3.2.6 Clean

Дополнительно к проверкам v3.2.5: исправлена интеграция Podkop с роутером
(файл `clean/package/openstick/podkop/files/usr/bin/podkop`, хэш обновлён
в `clean/podkop-upstream.json`, `verify_source` зелёный):

- `dnsmasq_configure` теперь идемпотентна и не зависит от флага
  `shutdown_correctly`: при каждом старте сверяет фактическое состояние
  dhcp (server 127.0.0.42, noresolv=1, cachesize=0) и приводит к нужному;
  бэкап оригинальных настроек (`podkop_server`/`podkop_noresolv`/
  `podkop_cachesize`) делается только один раз. Раньше после любого
  некорректного выключения (а дефолт флага — 0) настройка пропускалась
  навсегда: клиенты резолвили через DNS оператора мимо туннеля.
  Покрыто тестом `test_first_start_configures_dnsmasq_and_subsequent_start_
  does_not_duplicate_backup` (stateful-заглушка uci, три старта: одна
  настройка, один бэкап, один рестарт dnsmasq).
- Проверка policy routing в `check_fakeip` принимает имя таблицы
  (`lookup podkop`), а не только номер (`lookup 105`) — раньше статус был
  вечно красным при рабочем правиле. Покрыто регрессионным тестом
  `test_policy_route_check_accepts_table_name`.
- `route_table_rule_mark`: grep существования правила учитывает
  нормализацию hex (`0x100000`, а не `0x00100000`) — дубли правил при
  повторных стартах исключены; ошибки `ip route add`/`ip rule add`
  прерывают старт.
- `create_nft_rules`: таблица удаляется перед созданием (без дублей правил),
  в конце проверяется наличие цепочек mangle/mangle_output/proxy;
  `start_main` прерывается при ошибке policy routing или nft.
- `stop_main`: ошибка удаления nft-таблицы прерывает стоп (не молчаливый
  раскол); PID фонового `list_update` сверяется с `/proc/<pid>/cmdline`
  перед kill.
- Взаимное исключение lifecycle-операций (`podkop_acquire_lock`,
  `/var/run/ufi-podkop.lock`, реентерабельно для `restart` → `stop`+`start`,
  зависший лок снимается): параллельный старт/стоп больше не оставляет
  состояние «nft есть, роутинга нет, sing-box работает».
- `remove_cron_job` не затирает crontab при его отсутствии.
- Проверка DHCP (`check_dhcp_has_podkop_dns`) учитывает только основную
  секцию `@dnsmasq[0]` — гостевые сети не красят диагностику в красное.
- Удалена несуществующая команда `podkop main` (была в help и case).

Аппаратная приёмка на устройстве (прошивка v3.2.4, диагностика Podkop
21.10.2026 07:43–07:45 MSK): туннель XHTTP жив (outbound main 432 ms),
bootstrap 77.88.8.8 и DoH 1.1.1.1 через прокси отвечают, sing-box отдаёт
FakeIP — сломана была только интеграция с роутером (dnsmasq/policy
routing), что и чинит v3.2.6.

Остальной объём проверок — как в VALIDATION-v3.2.5.md: контрольные суммы
снимка Podkop и изменённых файлов, CI установщика, ARM64 podkop-engine под
QEMU (DoH через туннель, FakeIP, кнопка Cloudflare, устойчивость к SERVFAIL),
проверки конфигурации XHTTP, обязательные опции маршрутизации в ядре, хэши
образов и пара «архив + sha256» в релизе.
