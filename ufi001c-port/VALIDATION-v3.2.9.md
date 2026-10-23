# Проверка v3.2.9 Clean

Дополнительно к проверкам v3.2.8: упрощена упаковка USB-комплекта
(двойной клик вместо ручных команд, плоский ZIP, инструкция в TXT).

## Что проверено

- `stock_install.bundle()` собирает плоский ZIP: файлы в корне архива,
  без подпапки `UFI001C-{VERSION}/`. Распаковал — запустил INSTALL.cmd.
  Покрыто тестами `test_stock_install.py` (проверка `INSTALL.cmd`,
  `UPDATE.cmd`, `RESTORE.cmd` в корне) и `test_release.py`
  (`PREFIX = ''`, проверка `INSTALL-RU.txt` в комплекте).
- `UPDATE.cmd` добавлен в `PACKAGE_FILES` — попадает в ZIP.
  Двойной клик вызывает `RUN.cmd update`, дальше `stock_install.main()`
  с action `update`: бэкап находится автоматически
  (`UFI001C-backups/backup-*/emmc.bin`, самый свежий), путь вводить
  не нужно. Без бэкапа — понятная ошибка с подсказкой про INSTALL.cmd.
- `INSTALL-RU.txt` — plain-text инструкция: два сценария
  (INSTALL.cmd для стока, UPDATE.cmd для обновления), без ручных
  команд в cmd. Workflow копирует именно .txt в комплект.
- Версии согласованы: `clean/ufi001c-release`,
  `package_release.py` (VERSION, PROFILE), `stock_install.py` (VERSION),
  workflow — все `3.2.9`. Профиль `UFI001C v3.2.9 Clean / OpenWrt 25.12.5`
  сверяется `check_reports()` с `routing-rootfs-check.json`.
- RELEASE-NOTES-v3.2.9.md написан заново (не копия 3.2.8):
  реальный список изменений комплекта.

## Аппаратная приёмка

- [ ] Прошивка стокового модема через INSTALL.cmd (двойной клик)
- [ ] Обновление прошитого модема через UPDATE.cmd (двойной клик)
- [ ] Wi-Fi пароль из ACCESS.txt, интернет через Podkop
