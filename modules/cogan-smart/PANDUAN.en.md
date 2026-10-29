# 📖 Cogan Smart Kernel guide

[Bahasa Indonesia](PANDUAN.md) · [Module README](README.md)

Cogan Smart Kernel keeps the phone cool and records its temperature. This guide explains every tab and button in plain words.

## 🚀 Quick start

1. Choose a mode in the **Power** tab: 🌿 Power saver, 🧠 Kernel Default or 🎮 Performance.
2. Check the **Summary** in Manager: the controller and recorder should be *active* / *recording*.
3. Phone feels hot? Open the **Temperature** tab: the cause is recorded there.

## 🛠️ Manager: the control centre

- **Summary**: phone body, battery and processor temperature, controller and recorder status, a 1-hour temperature chart, the heat cause and the last module scan (scan in the Modules tab).
- **📱 Apps**: how many apps are dangerous and the APK block status, from the Apps tab.
- **Power mode**: shows the mode chosen in the Power tab. Manager only watches it; change the mode in the Power tab.
- **Processor**: how the CPU sets its speed (governor). Kernel Default suits everyday use.
- **RAM**: ZRAM compression. LZ4 is faster, ZSTD saves more RAM. Tick *Apply CPU/RAM at boot*, tap **Save**, then restart the phone.
- **Power controls** and **Temperature controls**: every button that applies the settings of the Power and Temperature tabs.

## 🔘 What the buttons do

- **💾 Save**: stores the settings. They take effect at the next check.
- **⚡ Force / Apply** and **Apply now**: saves, starts and applies at once.
- **↺ Reset defaults / Follow kernel**: back to the default settings. Temperature history is kept.
- **⏹ Stop / ▶ Start**: turns the controller or recorder off or on.
- **🗑 Clear history**: deletes the temperature records. Logs already saved in Download stay.

## ⚡ Power

- **🌿 Power saver**: big CPU capped at 60%, phone body kept ≤ 39 °C.
- **🧠 Kernel Default**: phone body kept ≤ 41 °C. The everyday choice.
- **🎮 Performance**: full power, held back only at a 44 °C phone body.
- **🔌 Charging**: stops at 95% and resumes at 90% (adjustable). *Detect charging switch* once, with the charger plugged in.
- **⚙️ Mode settings**: change each mode's temperature. Save from Manager.
- **📝 Activity**: a record of what the module did.

## 🌡️ Temperature

- **Now**: the phone body and other parts right now.
- **📊 Summary**: chart, how long the phone was hot, the heat causes, and temperature per app and per mode.
- **💾 Save logs**: saves the summary (.txt) and all data (.csv) to the *Download/CoganThermal* folder.
- **⚙️ Settings**: when the phone counts as hot (default 41 °C), how long history is kept (7 days) and notifications (off by default).

## 🧩 Modules

- Checks other root modules: ✅ safe, ⚠️ needs a look, ⛔ dangerous. These are guesses; read the *Evidence* before acting.
- **🛡️ Trust**: the module is no longer flagged and is protected from accidental removal.
- **⏸ Disable / ▶ Enable**: takes effect after a reboot.
- **🗑 Remove completely**: removes the module with its boot scripts and processes. Can be undone before rebooting.
- **📜 Boot scripts outside modules**: scripts that run at boot but are not in the module list.

## 📱 Apps

- Checks every app you installed: ✅ safe, ⚠️ needs a look, ⛔ dangerous. The marks come from where the app came from and what it may do; this is not an antivirus.
- **Source**: an app store, an APK file sent through chat or social apps, or an APK file from a browser or file manager. APKs sent through WhatsApp or social apps are the most common scam.
- **Dangerous rights**: reads SMS (OTP codes), accessibility (can read and tap the screen), device admin (hard to remove), reads notifications, draws over other apps, hidden icon.
- **👁️ Activity**: when the app last used the camera, microphone, location, SMS, contacts, phone or clipboard, its internet use in 7 days and battery since the last full charge.
- **⚠️ Needs a look / All / 💤 Rarely used**: choose which list to show. Rarely used means not opened for 7 days or more.
- **🛡️ Trust**: the app is no longer flagged and cannot be removed by accident.
- **🗑 Remove completely**: releases its device admin, stops and removes the app for every user (Dual apps and Second space too), then deletes leftover data and identical APK files in storage. This cannot be undone. System apps and the root manager cannot be removed here.
- **🛡️ Block APKs from chat & social apps**: on by default. WhatsApp, Telegram, Instagram, Facebook, TikTok and similar apps cannot install apps. If the right is turned on again in Settings, the module takes it back within seconds and shows a notification. Browsers and file managers still can.

## ℹ️ About

- Choose the **language** (ID/EN), the **theme** (Auto, Warm light, OLED dark) and **Dev mode**.

## 🛠️ Dev mode

- Off by default: a short view for everyday use.
- On: shows technical detail such as kernel nodes, readback, ZRAM boot hooks, every sensor and raw module data.

## ❓ FAQ

- **Cannot install an APK from WhatsApp or Telegram?** That is the APK block in the Apps tab. If you are sure the APK is safe, turn the block off first or open the file from a file manager.
- **Already installed a scam APK?** Tap Remove completely in the Apps tab, then change your passwords and bank PIN, and call your bank if you see strange transactions. Removing the app does not undo data that was already stolen.
- **Processor at 50–60 °C while idle, normal?** Yes. Heat is measured from the phone body, which is what you feel.
- **GPU column empty in the log?** The GPU is asleep (screen off or unused), so its sensor cannot be read. Normal.
- **Charging current up to 10–16 A?** That is 120 W HyperCharge fast charging. Normal.
- **ZRAM still LZ4 after a restart?** Tick *Apply CPU/RAM at boot*, tap Save, then restart. Needs module v2.10.8 or newer.
- **Phone fails to boot?** KernelSU safe mode turns every module off for a while. Turn them back on in the root manager → Modules, then reboot.

The same page is in the module: **ℹ️ About → 📖 Guide**.
