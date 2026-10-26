# SUT — البائع السوري

برنامج بسيط لإدارة مبيعات محل سوري، يعمل دون إنترنت. Python + Tkinter + SQLite.

## تشغيل من الشفرة

```bash
python3 -m sut
```

## الاختبارات

```bash
python -m unittest discover -s tests -v
```

## بناء حزمة DEB

```bash
bash packaging/build_deb.sh
```

## التثبيت

```bash
sudo dpkg -i dist/sut_*_all.deb
```
