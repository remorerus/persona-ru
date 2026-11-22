#!/usr/bin/env python3
import json,re,sys,time,urllib.parse,urllib.request
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else "decoded")
files={
"face":root/"smali_classes2/com/rokid/gwansang/gwansang/FaceReadingAnalyzer.smali",
"palm":root/"smali_classes2/com/rokid/gwansang/palmistry/PalmReadingAnalyzer.smali",
"rule":root/"smali_classes2/com/rokid/gwansang/gwansang/RuleEngine.smali",
"overlay":root/"smali_classes2/com/rokid/gwansang/hud/ArOverlayView.smali",
"main":root/"smali_classes2/com/rokid/gwansang/MainActivity.smali"}
rx=re.compile(r'const-string(?:/jumbo)?\s+(\w+),\s+"((?:\\.|[^"\\])*)"')
def dec(s): return bytes(s,"utf-8").decode("unicode_escape")
def enc(s): return json.dumps(s,ensure_ascii=True)[1:-1]
ui={
"Save Result":"Сохранение результата","Face Analysis":"Анализ лица","Don't Save":"Не сохранять",
"Auto Save":"Автосохранение","Palm":"Ладонь","Saved to DCIM/Camera folder.":"Результат сохранён в папку DCIM/Camera.",
"Save failed.":"Не удалось сохранить результат.","View Detail":"Подробнее","Saving...":"Сохранение…",
"Would you like to save the analysis result as an image?":"Сохранить результат анализа в виде изображения?",
"Save":"Сохранить","Face":"Лицо","Permission required":"Требуется разрешение",
"Diamond":"Ромбовидная","Round":"Круглая","Triangle":"Треугольная","Square":"Квадратная",
"Oval":"Овальная","Mouth":"Рот","Face Shape":"Форма лица","Jaw":"Челюсть","Nose":"Нос","Eyes":"Глаза","Forehead":"Лоб"}
skip={"KO","EN","JP","CN","landmarks","lang","language","context","canvas","value","mode",
"this as java.lang.String).toUpperCase(Locale.ROOT)","StringBuilder().apply(builderAction).toString()",
"binding","event","getChildAt(...)","getRoot(...)","createBitmap(...)","createScaledBitmap(...)"}
glossary=[
(r"(?i)\bCheiro\b","Хейро"),(r"(?i)\bMount of Jupiter\b","холм Юпитера"),
(r"(?i)\bJupiter Mount\b","холм Юпитера"),(r"(?i)\bMount of Saturn\b","холм Сатурна"),
(r"(?i)\bMount of the Sun\b","холм Солнца"),(r"(?i)\bMount of Venus\b","холм Венеры"),
(r"(?i)\bMount of Mercury\b","холм Меркурия"),(r"(?i)\bMount of the Moon\b","холм Луны"),
(r"(?i)\bMount of Mars\b","холм Марса"),(r"(?i)\bLife Line\b","линия жизни"),
(r"(?i)\bHead Line\b","линия головы"),(r"(?i)\bHeart Line\b","линия сердца"),
(r"(?i)\bFate Line\b","линия судьбы"),(r"(?i)\bSun Line\b","линия Солнца"),
(r"(?i)\bHealth Line\b","линия здоровья"),(r"(?i)\bFive Elements\b","Пять стихий"),
(r"(?i)\bWood Type\b","тип Дерева"),(r"(?i)\bFire Type\b","тип Огня"),
(r"(?i)\bEarth Type\b","тип Земли"),(r"(?i)\bMetal Type\b","тип Металла"),
(r"(?i)\bWater Type\b","тип Воды"),(r"(?i)\bHeaven Zone\b","зона Неба"),
(r"(?i)\bHuman Zone\b","зона Человека"),(r"(?i)\bphiltrum\b","желобок верхней губы"),
(r"(?i)\bJing\b","Цзин"),(r"(?i)\bHollow Hand\b","впалая ладонь"),
(r"(?i)\bPalm Center\b","центр ладони"),(r"(?i)\bWill Phalange\b","фаланга воли"),
(r"(?i)\bLogic Phalange\b","логическая фаланга"),(r"(?i)\bWide Finger Spacing\b","широко расставленные пальцы"),
(r"(?i)\bRight-Angle Thumb\b","большой палец, раскрытый под прямым углом"),
(r"(?i)\bOverall\b","общая характеристика")]
cachepath=Path("translations-ru.json")
cache=json.loads(cachepath.read_text(encoding="utf-8")) if cachepath.exists() else {}
candidates={}
for key in ("face","palm"):
 for line in files[key].read_text(encoding="utf-8").splitlines():
  m=rx.search(line)
  if m:
   v=dec(m.group(2))
   if re.search("[A-Za-z]",v) and not re.search(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7a3]",v) and v not in skip and len(v.strip())>1: candidates[v]="en"
for line in files["rule"].read_text(encoding="utf-8").splitlines():
 m=rx.search(line)
 if m:
  v=dec(m.group(2))
  if re.search(r"[\uac00-\ud7a3]",v): candidates[v]="ko"
for key in ("overlay","main"):
 for line in files[key].read_text(encoding="utf-8").splitlines():
  m=rx.search(line)
  if m:
   v=dec(m.group(2))
   if v in ui: candidates[v]="en"
for v in ui: candidates[v]="en"
ARGOS_TRANSLATOR=None
def offline_en_to_ru(s):
 global ARGOS_TRANSLATOR
 for pat,repl in glossary: s=re.sub(pat,repl,s)
 if ARGOS_TRANSLATOR is None:
  import argostranslate.translate as argos_translate
  try: argos_translate.get_installed_languages.cache_clear()
  except Exception: pass
  langs=argos_translate.get_installed_languages()
  print("Argos languages:",[(x.code,x.name) for x in langs],flush=True)
  routes=[(x.code,t.to_lang.code) for x in langs for t in x.translations_from]
  print("Argos routes:",routes,flush=True)
  ARGOS_TRANSLATOR=next((t for x in langs if x.code=="en" for t in x.translations_from if t.to_lang.code=="ru"),None)
  if ARGOS_TRANSLATOR is None:
   # Some Argos packages unpack metadata.json directly into package_data_dir.
   # Load that valid package directory directly if the registry scan misses it.
   import argostranslate.package as argos_package
   package_dirs=[argos_package.settings.package_data_dir]
   package_dirs += [p for p in argos_package.settings.package_data_dir.iterdir() if p.is_dir()]
   for package_dir in package_dirs:
    if (package_dir/"metadata.json").exists():
     pkg=argos_package.Package(package_dir)
     if pkg.from_code=="en" and pkg.to_code=="ru":
      source=argos_translate.Language(pkg.from_code,pkg.from_name)
      target=argos_translate.Language(pkg.to_code,pkg.to_name)
      ARGOS_TRANSLATOR=argos_translate.PackageTranslation(source,target,pkg)
      print("Loaded Argos model directly from:",package_dir,flush=True)
      break
  if ARGOS_TRANSLATOR is None:
   raise RuntimeError("Argos English-Russian model not registered; routes="+str(routes))
 out=ARGOS_TRANSLATOR.translate(s)
 for pat,repl in glossary: out=re.sub(pat,repl,out)
 return out

def trans(s,lang):
 for pat,repl in glossary: s=re.sub(pat,repl,s)
 if lang=="en": return offline_en_to_ru(s)
 if lang=="ko" and s in cache: return cache[s]
 raise RuntimeError("No approved translation for source language "+lang)
# Batch related phrases to reduce requests and keep each source phrase as a separate segment.
pending=[(s,lang) for s,lang in candidates.items() if not cache.get(s)]
batch_no=0
for lang in ("en","ko"):
 group=[s for s,source_lang in pending if source_lang==lang]
 batches=[]
 current=[]
 current_len=0
 for phrase in group:
  if current and (len(current)>=8 or current_len+len(phrase)>2600):
   batches.append(current); current=[]; current_len=0
  current.append(phrase); current_len+=len(phrase)
 if current: batches.append(current)
 for batch in batches:
  batch_no+=1
  marker=f"ZXQPERSONADELIM{batch_no}ZXQ"
  combined=("\n"+marker+"\n").join(batch)
  translated=None
  try:
   translated=trans(combined,lang)
  except Exception:
   translated=None
  parts=translated.split(marker) if translated else []
  if len(parts)!=len(batch):
   # If a provider changes separators, use the local model phrase-by-phrase.
   parts=[trans(phrase,lang) for phrase in batch]
  for phrase,result in zip(batch,parts):
   cache[phrase]=result.strip()
  cachepath.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding="utf-8")
  print(f"Translated batch {batch_no}: {len(cache)}/{len(candidates)} strings",flush=True)
  time.sleep(.5)
# Keep the original non-Russian variants as a source corpus for audit.
corpus={}
for key in ("face","palm","rule"):
 vals=[]
 for line in files[key].read_text(encoding="utf-8").splitlines():
  m=rx.search(line)
  if m:
   try: v=dec(m.group(2))
   except: continue
   if re.search(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7a3]",v): vals.append(v)
 corpus[key]=list(dict.fromkeys(vals))
Path("multilingual-source-corpus.json").write_text(json.dumps(corpus,ensure_ascii=False,indent=2),encoding="utf-8")
changed=0
for p in files.values():
 src=p.read_text(encoding="utf-8")
 def sub(m):
  global changed
  v=dec(m.group(2))
  if v in cache:
   changed+=1
   return f'const-string {m.group(1)}, "{enc(cache[v])}"'
  return m.group(0)
 p.write_text(rx.sub(sub,src),encoding="utf-8")
main=files["main"]
s=main.read_text(encoding="utf-8")
pat=re.compile(r'(\.method private final loadSettings\(\)V.*?const-string v1, "language"\s+const-string v2, "KO"\s+invoke-interface \{v0, v1, v2\}, Landroid/content/SharedPreferences;->getString\(Ljava/lang/String;Ljava/lang/String;\)Ljava/lang/String;\s+move-result-object v1).*?(iput-object v2, p0, Lcom/rokid/gwansang/MainActivity;->currentLanguage:Ljava/lang/String;)',re.S)
def force(m):
 pre=m.group(1).replace('const-string v2, "KO"','const-string v2, "EN"')
 pre=re.sub(r'move-result-object v1\s+if-nez v1, :cond_0\s+goto :goto_0\s+:cond_0\s+move-object v2, v1\s+:goto_0','move-result-object v1\n\n    const-string v2, "EN"',pre)
 return pre+"\n\n    "+m.group(2)
s,n=pat.subn(force,s,count=1)
if n!=1: raise RuntimeError("Could not force EN source branch")
s=s.replace('const-string v0, "KO"\n\n    iput-object v0, p0, Lcom/rokid/gwansang/MainActivity;->currentLanguage:Ljava/lang/String;','const-string v0, "EN"\n\n    iput-object v0, p0, Lcom/rokid/gwansang/MainActivity;->currentLanguage:Ljava/lang/String;',1)
# Hardware focus navigation now cycles only between Face (0) and Palm (1).
s=s.replace(".field private static final MAX_FOCUS_INDEX:I = 0x7", ".field private static final MAX_FOCUS_INDEX:I = 0x2")
s=s.replace("rem-int/lit8 p1, p1, 0x7", "rem-int/lit8 p1, p1, 0x2")
s=s.replace("add-int/lit8 p1, p1, 0x6", "add-int/lit8 p1, p1, 0x1")
main.write_text(s,encoding="utf-8")
layout=root/"res/layout/activity_main.xml"
s=layout.read_text(encoding="utf-8")
s=re.sub(r'(<LinearLayout[^>]*android:id="@id/languageSelectorBar"[^>]*)(>)',r'\1 android:visibility="gone"\2',s,count=1)
s=s.replace('android:text="Auto Save"','android:text="Автосохранение"').replace('android:text="관상"','android:text="Лицо"')
s=s.replace('android:text="손금"','android:text="Ладонь"').replace('android:text="상세 보기 (터치)"','android:text="Подробнее (коснитесь)"')
layout.write_text(s,encoding="utf-8")
audit={"source_strings":len(candidates),"translated_strings":len(cache),"patched_smali_occurrences":changed,"analysis_algorithms_changed":False,"navigation":"face/palm only",
"source_languages":{"English":sum(x=="en" for x in candidates.values()),"Korean":sum(x=="ko" for x in candidates.values())}}
Path("translation-audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(audit,ensure_ascii=False,indent=2))
