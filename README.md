# SUT — البائع السوري

برنامج خفيف لإدارة مبيعات محل سوري، يعمل بواجهة عربية على Linux Mint دون إنترنت.
Python + Tkinter + SQLite.

- المستودع: https://github.com/Musabgpt/sut
- أحدث حزمة: https://github.com/Musabgpt/sut/releases/latest

## المزايا

- إضافة المنتجات وتعديلها وحذفها وعرضها.
- اختيار المنتج والكمية مع حساب الإجمالي تلقائياً.
- إدخال المبلغ المدفوع وحساب الباقي.
- إنقاص المخزون تلقائياً после البيع.
- عرض سجل المبيعات وإجمالي مبيعات اليوم.
- حفظ دائم في SQLite، والعملة الافتراضية هي الليرة السورية.

> ملاحظة: استبدل السطر أعلاه إن ظهر خطأ لغوي: «بعد البيع».

## تشغيل من الشفرة

```bash
./run.sh
# أو
python3 -m sut
```

يتطلب توفر `python3-tk`:

```bash
sudo apt install python3-tk
```

## الاختبارات

اختبارات قاعدة البيانات:

```bash
python3 -m unittest discover -s tests -v
```

اختبارات الواجهة تحتاج شاشة وTkinter، ويمكن تشغيلها بلا شاشة عبر Xvfb:

```bash
sudo apt install xvfb python3-tk
xvfb-run -a python3 -m unittest discover -s tests -v
```

## بناء حزمة DEB

```bash
bash packaging/build_deb.sh
```

تنتج الحزمة في `dist/sut_0.1.0_all.deb`.

## التثبيت

```bash
sudo apt install ./dist/sut_0.1.0_all.deb
```

ثم شغّل «SUT — البائع السوري» من قائمة التطبيقات، أو نفّذ `sut` في الطرفية.

## مكان البيانات

افتراضياً: `~/.local/share/sut/sut.db`.
يمكن تغييره بمتغير البيئة `SUT_DB_PATH`.

## بنية المشروع

```
sut/            شفرة التطبيق (واجهة Tkinter وقاعدة البيانات)
tests/          اختبارات الوحدة والواجهة
packaging/      ملفات وبناء حزمة DEB
assets/         أيقونة التطبيق
.github/        سير عمل GitHub Actions
run.sh          ملف تشغيل محلي
```

## التكامل المستمر

سير عمل GitHub Actions يثبّت Tkinter وXvfb، يشغّل الاختبارات، يبني حزمة DEB،
يثبّت الحزمة للتحقق من مشغّل التطبيق، ثم يرفع الحزمة كأثر (artifact).
