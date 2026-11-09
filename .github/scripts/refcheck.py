"""배포물(_site) 안 글 파일이, 원본(src)엔 있지만 배포물에서 빠진 파일을 가리키는지 센다.
사용: python3 refcheck.py <src> <site>"""
import os, re, sys, collections
src, site = sys.argv[1:3]
def files(root):
    out = set()
    for d, _, fs in os.walk(root):
        if '/.git' in d or d.endswith('/.git'):
            continue
        for f in fs:
            out.add(os.path.relpath(os.path.join(d, f), root))
    return out
S, D = files(src), files(site)
gone = S - D
TEXT = ('.html', '.htm', '.xml', '.txt', '.json', '.js', '.css', '.webmanifest', '.svg')
# 따옴표·괄호·= 바로 뒤에서 시작해 따옴표·괄호에서 끝나는 값 하나만 센다(본문 속 파일 이름 언급은 제외)
tok = re.compile(r'''(?<=["'(=])((?:https?://blog\.pebblous\.ai)?[^\s"'()<>,]+?\.[A-Za-z0-9]{1,10})(?:[?#][^\s"'()<>]*)?(?=["')])''')
hits = collections.Counter(); where = collections.defaultdict(set)
for rel in D:
    if not rel.endswith(TEXT):
        continue
    try:
        txt = open(os.path.join(site, rel), encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    base = os.path.dirname(rel)
    for m in tok.finditer(txt):
        r = m.group(1)
        # 슬래시 없는 낱말(예: 태그 목록의 "CLAUDE.md")은 href=·src=·url(·함수 인자 자리일 때만 링크로 본다
        if '/' not in r and not re.search(r'''(?:(?:href|src|poster|data-src)\s*=\s*["']?|url\(\s*["']?|\(\s*["'])$''', txt[max(0, m.start() - 12):m.start()]):
            continue
        if r.startswith(('http://', 'https://')):
            if not r.startswith('https://blog.pebblous.ai'):
                continue
            r = r[len('https://blog.pebblous.ai'):]
        if r.startswith('//') or ':' in r.split('/')[0]:
            continue
        cands = [os.path.normpath(r.lstrip('/'))] if r.startswith('/') else [os.path.normpath(os.path.join(base, r)), os.path.normpath(r)]
        for c in cands:
            if c in gone:
                hits[c] += 1; where[c].add(rel); break
print(f'원본 {len(S)} · 배포물 {len(D)} · 뺀 파일 {len(gone)}')
print(f'뺀 파일을 가리키는 참조: 서로 다른 대상 {len(hits)}개 · 참조 {sum(hits.values())}회')
for c, n in hits.most_common(40):
    ex = sorted(where[c])[:3]
    print(f'- {c} ×{n}  (예: {", ".join(ex)})')
if hits and '--gate' in sys.argv:
    print('::error::배포물에서 뺀 파일을 가리키는 참조가 있어 배포를 멈춥니다')
    sys.exit(1)
