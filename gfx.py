# -*- coding: utf-8 -*-
# Graphics generator for Nina monthly news (1920x1080 RGBA overlays)
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1920, 1080
OUT = 'g'
os.makedirs(OUT, exist_ok=True)
JP = os.environ.get('JPF','f/jp.ttf')
EN = os.environ.get('ENF','/usr/share/fonts/truetype/higgsfield/Montserrat-ExtraBold.ttf')
NAVY = (15, 26, 48); NAVY2 = (26, 39, 68); CYAN = (0, 188, 212); WHITE = (255, 255, 255)
RED = (230, 0, 18); VIOLET = (124, 77, 255); GREEN = (76, 175, 80); GOLD = (212, 168, 67); OFF = (247, 245, 240)

def F(p, s): return ImageFont.truetype(p, s)
def new(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))
def tw(d, t, f): b = d.textbbox((0, 0), t, font=f); return b[2] - b[0], b[3] - b[1]

def wordmark(scale=1.0, band=True):
    """NissinPerTechtual: NISSIN red bold condensed caps + PerTechtual white bold italic on white band look."""
    f = F(EN, int(64 * scale))
    tmp = Image.new('RGBA', (int(1400 * scale), int(140 * scale)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    # NISSIN condensed: draw then squeeze horizontally
    w1, h1 = tw(d, 'NISSIN', f)
    a = Image.new('RGBA', (w1 + 20, int(110 * scale)), (0, 0, 0, 0))
    ImageDraw.Draw(a).text((0, 0), 'NISSIN', font=f, fill=RED)
    a = a.resize((int(a.width * 0.82), a.height))
    w2, h2 = tw(d, 'PerTechtual', f)
    b = Image.new('RGBA', (w2 + 60, int(110 * scale)), (0, 0, 0, 0))
    ImageDraw.Draw(b).text((10, 0), 'PerTechtual', font=f, fill=WHITE)
    b = b.transform(b.size, Image.AFFINE, (1, 0.22, -10, 0, 1, 0), resample=Image.BICUBIC)  # italic shear
    pad = int(26 * scale)
    wm = Image.new('RGBA', (a.width + b.width + pad * 2, int(110 * scale)), (0, 0, 0, 0))
    if band:
        ImageDraw.Draw(wm).rounded_rectangle([0, 0, wm.width, wm.height], radius=int(10 * scale), fill=(255, 255, 255, 255))
        # left white band behind NISSIN, navy behind PerTechtual so white italic reads
        ImageDraw.Draw(wm).rounded_rectangle([a.width + pad - 4, 0, wm.width, wm.height], radius=int(10 * scale), fill=NAVY + (255,))
    wm.alpha_composite(a, (pad, int(14 * scale)))
    wm.alpha_composite(b, (a.width + pad + 6, int(14 * scale)))
    return wm

def chip(text, fg=WHITE, bg=NAVY + (220,), size=30, padx=22, pady=12, font=JP):
    f = F(font, size); d = ImageDraw.Draw(new())
    w, h = tw(d, text, f)
    im = Image.new('RGBA', (w + padx * 2, h + pady * 2 + 6), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=10, fill=bg)
    ImageDraw.Draw(im).text((padx, pady - 2), text, font=f, fill=fg)
    return im

def shadowed(im, r=18, op=110):
    s = Image.new('RGBA', (im.width + r * 4, im.height + r * 4), (0, 0, 0, 0))
    mask = Image.new('L', im.size, 0); mask.paste(im.split()[3])
    sh = Image.new('RGBA', im.size, (0, 0, 0, op)); sh.putalpha(mask.point(lambda v: min(v, op)))
    s.alpha_composite(sh, (r * 2, r * 2 + 6)); s = s.filter(ImageFilter.GaussianBlur(r))
    s.alpha_composite(im, (r * 2, r * 2)); return s, r * 2

def place(canvas, im, x, y, shadow=True):
    if shadow:
        s, o = shadowed(im); canvas.alpha_composite(s, (max(0, x - o), max(0, y - o)))
    else:
        canvas.alpha_composite(im, (x, y))

def save(name, im): im.save(f'{OUT}/{name}.png')

# ---------- persistent chips ----------
c = new(); place(c, chip('AI GENERATED｜このNinaは生成AIで制作しています', size=24, bg=(0, 0, 0, 150)), 40, 36, False); save('ai_chip', c)
c = new(); place(c, chip('※映像はイメージ（AI生成）', size=24, bg=(0, 0, 0, 150)), 40, 36, False); save('img_chip', c)
c = new(); wm = wordmark(0.55); place(c, wm, W - wm.width - 44, 34, False); save('wm_small', c)

def source(name, text):
    c = new(); ch = chip(text, size=24, bg=(0, 0, 0, 165)); place(c, ch, W - ch.width - 40, 36, False); save(name, c)
source('src_openai', '出典：OpenAI 公式発表（2026.9.3／9.22）')
source('src_anthropic', '出典：Anthropic 公式発表（2026.9.22）')
source('src_google', '出典：Google 公式ブログ（2026.9.24）')
source('src_eleven', '出典：ElevenLabs 公式発表（2026.9.28）')
source('src_tesla', '出典：Tesla 発表・各社報道（2026.9）')
source('src_meta', '出典：Meta 公式発表（2026.9.8／9.29）')
source('src_spacex', '出典：SpaceX 発表・各社報道（2026.9.28）')

# ---------- lower third ----------
def lower_third(name, title, sub, accent=CYAN, right=False):
    c = new(); x, y = 90, 760
    f1 = F(JP, 54); f2 = F(JP, 30); d = ImageDraw.Draw(c)
    w = max(tw(d, title, f1)[0], tw(d, sub, f2)[0]) + 90
    box = Image.new('RGBA', (w, 150), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([0, 0, w, 150], radius=14, fill=NAVY + (235,)); bd.rectangle([0, 0, 12, 150], fill=accent)
    bd.text((40, 14), title, font=f1, fill=WHITE); bd.text((42, 92), sub, font=f2, fill=(200, 225, 235))
    if right: x = W - w - 90
    place(c, box, x, y); save(name, c)
lower_third('lt_nina', 'Nina（ニーナ）', 'ニッシン・パーテクチュアル 広報部｜公式AIアンバサダー')
lower_third('lt_ceo', '代表取締役 中村 稔', '通称「みのたん」｜金型・レーザー・生成AI・ロボティクス', GOLD, right=True)

# ---------- big callouts (right side) ----------
def callout(name, big, label, accent=CYAN, x=1120, y=300, bigsize=150):
    c = new(); fb = F(EN, bigsize); fl = F(JP, 44); d = ImageDraw.Draw(c)
    wb, hb = tw(d, big, fb); wl, hl = tw(d, label, fl); w = max(wb, wl) + 100
    box = Image.new('RGBA', (w, hb + hl + 130), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([0, 0, box.width, box.height], radius=18, fill=NAVY + (225,))
    bd.rectangle([0, box.height - 12, box.width, box.height], fill=accent)
    bd.text((50, 20), big, font=fb, fill=accent); bd.text((52, hb + 60), label, font=fl, fill=WHITE)
    place(c, box, min(x, W - box.width - 60), y); save(name, c)
callout('co_1973', '1973', '創業｜埼玉県春日部市')
callout('co_19', '19', '社員数（名）')
callout('co_14', '1.4', '平均ロット（個）｜超多品種少量', RED)
callout('co_1500', '1,500+', '生成AIセミナー 累計受講者', VIOLET, x=1060)
callout('co_98', '98%', 'セミナー満足度', VIOLET, x=1060, y=560)
callout('co_20', '+20%', '搬送ロボット導入で生産量アップ', GREEN, x=1100, y=340)
callout('co_f14', 'FLIGHT 14', '初の地球周回軌道に到達', CYAN, x=1000, y=260, bigsize=110)
callout('co_26', '×26', '新型Starlink衛星を軌道へ', CYAN, x=1100, y=300)

# ---------- bullet panels ----------
def panel(name, head, items, accent=CYAN, x=1060, y=230, width=800):
    c = new(); fh = F(JP, 40); fi = F(JP, 36)
    rows = len(items); h = 110 + rows * 78 + 30
    box = Image.new('RGBA', (width, h), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([0, 0, width, h], radius=18, fill=NAVY + (228,)); bd.rectangle([0, 0, width, 10], fill=accent)
    bd.text((40, 32), head, font=fh, fill=accent)
    for i, t in enumerate(items):
        yy = 110 + i * 78; bd.ellipse([44, yy + 14, 60, yy + 30], fill=accent); bd.text((80, yy), t, font=fi, fill=WHITE)
    place(c, box, x, y); save(name, c)
panel('p_gf', 'スイスGF社の設備群', ['ワイヤー放電加工機', '形彫り放電加工機', '5軸マシニングセンタ', 'フェムト秒レーザー加工機'])
panel('p_hnp', 'HNP処理（フェムト秒レーザー表面処理）', ['特許取得', '日本経済新聞に掲載', '「金型の寿命を最大3倍に」'], CYAN, x=80, y=200, width=860)
panel('p_biz', '4つの事業を少人数で', ['冷間圧造用 精密金型', 'フェムト秒レーザー（HNP）', '生成AI 活用支援・セミナー', 'ロボティクス（PUDU代理店）'], GOLD, x=1040)
panel('p_gpt', 'GPT-6 Astra のポイント', ['100万トークン超の長文脈', '長時間タスクを自律でやり抜く', '安全対策のため公開を延期', '9/22「Sol」「Luna」も公開'], VIOLET)
panel('p_claude', 'Claude Opus 5.5 のポイント', ['上位「Fable 5.1」級の性能', 'Opus 5比 約4割安く動作', '当社も業務自動化で活用中'], VIOLET)
panel('p_muse', 'Meta Muse のポイント', ['個人向けのAIエージェント', 'メール・予約などを代行', 'アプリを閉じても動き続ける', '9/29 中小企業版も登場'], VIOLET)
panel('p_cab', 'Cybercab', ['2人乗り', 'ハンドル・ペダル・ミラーなし', '9/3 オースティンで有料運行開始'], CYAN)
panel('p_tour', 'アジア展示ツアー', ['9/9〜 香港', '東京・大阪・名古屋でも公開予定'], RED)
panel('p_nhtsa', 'これからの論点', ['米国の安全当局が認証の経緯を調査', '問われるのは「社会の受け入れ」'], GOLD)
panel('p_flight', '飛行の記録', ['エンジン1基が途中停止', '飛行時間 約10時間 → 約3時間', 'それでも主な目標は達成'], CYAN)

# ---------- news title (top-left) ----------
def news_title(name, tag, date, title, accent=VIOLET):
    c = new(); ft = F(EN, 30); fd = F(EN, 30); fh = F(JP, 52); d = ImageDraw.Draw(c)
    wt = tw(d, tag, ft)[0]; wh = tw(d, title, fh)[0]
    box = Image.new('RGBA', (max(wh + 80, wt + 300), 190), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([0, 0, box.width, 190], radius=16, fill=NAVY + (232,))
    bd.rounded_rectangle([30, 22, 30 + wt + 36, 72], radius=8, fill=accent); bd.text((48, 28), tag, font=ft, fill=WHITE)
    bd.text((30 + wt + 60, 28), date, font=fd, fill=(190, 210, 225)); bd.text((32, 96), title, font=fh, fill=WHITE)
    place(c, box, 60, 110); save(name, c)
news_title('t_gpt', 'AI NEWS 01', '2026.09.03', 'OpenAI「GPT-6 Astra」発表')
news_title('t_claude', 'AI NEWS 02', '2026.09.22', 'Anthropic「Claude Opus 5.5」公開')
news_title('t_gemini', 'AI NEWS 03', '2026.09.24', 'Google「Gemini Live Avatar」提供開始')
news_title('t_eleven', 'AI NEWS 04', '2026.09.28', 'ElevenLabs「Eleven v4」公開')
news_title('t_muse', 'AI NEWS 05', '2026.09.08', 'Meta「Muse」発表')
news_title('t_cab', 'BIG NEWS 01', '2026.09.03', 'Tesla「Cybercab」有料運行スタート', RED)
news_title('t_ship', 'BIG NEWS 02', '2026.09.28', 'SpaceX「Starship」初の軌道到達', RED)

c = new(); ch = chip('NOW PLAYING ▶ Eleven v4 ＝ いま聞いているNinaの声', size=40, bg=VIOLET + (235,), padx=34, pady=20)
place(c, ch, (W - ch.width) // 2, 700); save('nowplaying', c)
c = new(); ch = chip('SEPTEMBER 2026｜AI & TECH NEWS', size=46, bg=VIOLET + (235,), padx=40, pady=22, font=EN)
place(c, ch, 60, 110); save('sept', c)

# ---------- side-aware cards for Nina shots (_L = left edge, _R = right edge) ----------
def card(lines, accent=CYAN, width=560, head_size=34, body_size=30, tag=None):
    fh = F(JP, head_size); fb = F(JP, body_size); ft = F(EN, 24)
    h = 40 + (52 if tag else 0) + head_size + 24 + len(lines[1:]) * (body_size + 22) + 24
    box = Image.new('RGBA', (width, h), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([0, 0, width, h], radius=16, fill=NAVY + (232,)); bd.rectangle([0, 0, 10, h], fill=accent)
    y = 24
    if tag:
        tw_ = tw(bd, tag, ft)[0]; bd.rounded_rectangle([34, y, 34 + tw_ + 28, y + 40], radius=8, fill=accent); bd.text((48, y + 5), tag, font=ft, fill=WHITE); y += 52
    bd.text((34, y), lines[0], font=fh, fill=accent if not tag else WHITE); y += head_size + 24
    for t in lines[1:]:
        bd.text((34, y), t, font=fb, fill=WHITE); y += body_size + 22
    return box
def sided(name, box, y):
    for sd in 'LR':
        c = new(); x = 50 if sd == 'L' else W - box.width - 50
        place(c, box, x, y); save(f'{name}_{sd}', c)
sided('lt_nina', card(['Nina（ニーナ）', 'ニッシン・パーテクチュアル', '広報部｜公式AIアンバサダー'], CYAN, 560, 46, 28), 560)
sided('p_hnp', card(['HNP処理', 'フェムト秒レーザー表面処理', '特許取得', '日本経済新聞に掲載', '「金型の寿命を最大3倍に」'], CYAN, 580, 46, 30), 230)
sided('t_gemini', card(['Google', '「Gemini Live Avatar」', '企業向けに提供開始'], VIOLET, 560, 40, 32, 'AI NEWS 03  2026.09.24'), 200)
sided('t_eleven', card(['ElevenLabs', '「Eleven v4」公開', '最も感情豊かな音声モデル'], VIOLET, 560, 40, 32, 'AI NEWS 04  2026.09.28'), 200)
sided('sept', card(['9月の', 'AI＆テックニュース', 'まとめて解説！'], VIOLET, 520, 44, 40, 'SEPTEMBER 2026'), 250)
sided('nowplaying', card(['NOW PLAYING ▶', 'Eleven v4', '＝いま聞いている', 'Ninaの声です'], VIOLET, 520, 44, 40), 300)
sided('kyomo', card(['今日も、', '新しく。'], CYAN, 520, 72, 72), 330)

# ---------- castle / photo credits ----------
c = new(); place(c, chip('※外観はイメージです（AI生成）', size=26, bg=(0, 0, 0, 170)), 40, 36, False); save('castle_chip', c)
def credit(name, text):
    c = new(); ch = chip(text, size=20, bg=(0, 0, 0, 160), padx=16, pady=8); place(c, ch, 40, 36, False); save(name, c)
credit('cr_road', '写真：Daniel Lu (dllu) / CC BY-SA 4.0 / Wikimedia Commons')
credit('cr_inside', '写真：Steve Jurvetson / CC BY 2.0 / Wikimedia Commons')
credit('cr_front', '写真：Steve Jurvetson / CC BY 2.0 / Wikimedia Commons')
credit('cr_cc0', '写真：JustAnotherCarDesigner / CC0 / Wikimedia Commons')
credit('cr_ceo', '写真：ニッシン・パーテクチュアル')
credit('cr_site', '写真：ニッシン・パーテクチュアル（pertechtual.co.jp）')
credit('cr_ift3', '実写映像：jackyuan08 / CC BY 3.0 / Wikimedia Commons ※2024年 第3回試験飛行の映像です')
credit('cr_ft11', '写真：Shujianyang / CC BY-SA 4.0 / Wikimedia Commons ※2025年 第11回試験飛行')
credit('cr_ift5', '実写映像：Anne Toal / CC BY 3.0 / Wikimedia Commons ※2024年 第5回試験飛行の映像です')
credit('cr_iss', '写真：NASA / Donald Pettit（ISSから撮影したStarship）/ Public domain ※2024年 第6回試験飛行')

# ---------- full-frame cards ----------
def bg_card():
    im = Image.new('RGBA', (W, H), NAVY + (255,)); d = ImageDraw.Draw(im)
    for i in range(0, W, 80): d.line([(i, 0), (i, H)], fill=(26, 39, 68, 255), width=1)
    for j in range(0, H, 80): d.line([(0, j), (W, j)], fill=(26, 39, 68, 255), width=1)
    d.rectangle([0, H - 14, W, H], fill=CYAN); return im

def opening():
    im = new(); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, H], fill=(10, 18, 34, 150))
    f1 = F(EN, 120); f2 = F(JP, 64); f3 = F(EN, 44)
    t = "Nina's MONTHLY NEWS"; w, _ = tw(d, t, f1); d.text(((W - w) // 2, 330), t, font=f1, fill=WHITE)
    t = '2026年9月号｜生成AI × テクノロジー'; w, _ = tw(d, t, f2); d.text(((W - w) // 2, 500), t, font=f2, fill=CYAN)
    wm = wordmark(0.8); im.alpha_composite(wm, ((W - wm.width) // 2, 640))
    t = 'このNinaは生成AIで制作されています'; f4 = F(JP, 32); w, _ = tw(d, t, f4); d.text(((W - w) // 2, 820), t, font=f4, fill=(200, 210, 220))
    save('open', im)
opening()

def stinger(name, big, sub, accent):
    im = bg_card(); d = ImageDraw.Draw(im); f1 = F(EN, 150); f2 = F(JP, 56)
    w, _ = tw(d, big, f1); d.text(((W - w) // 2, 380), big, font=f1, fill=accent)
    w, _ = tw(d, sub, f2); d.text(((W - w) // 2, 580), sub, font=f2, fill=WHITE); save(name, im)
stinger('st_big', 'BIG NEWS', '世界を驚かせた9月の2大ニュース', RED)

def ending():
    im = bg_card(); d = ImageDraw.Draw(im)
    wm = wordmark(1.0); im.alpha_composite(wm, ((W - wm.width) // 2, 150))
    f = F(JP, 80); t = '今日も、新しく。'; w, _ = tw(d, t, f); d.text(((W - w) // 2, 320), t, font=f, fill=WHITE)
    fs = F(JP, 25); y = 470
    for s in ['【出典】OpenAI（GPT-6 Astra 2026.9.3／Sol・Luna 9.22）｜Anthropic（Claude Opus 5.5 2026.9.22）',
              'Google（Gemini 3.8 Live with Live Avatar 2026.9.24）｜ElevenLabs（Eleven v4 2026.9.28）',
              'Meta（Muse 2026.9.8／Muse for Small Business 9.29）｜Tesla Cybercab（2026.9.3 運行開始）｜SpaceX Starship Flight 14（2026.9.28）',
              'Cybercab写真：Wikimedia Commons（Daniel Lu CC BY-SA 4.0／Steve Jurvetson CC BY 2.0／JustAnotherCarDesigner CC0）',
              'Starship実写：Wikimedia Commons（jackyuan08・Anne Toal CC BY 3.0／Shujianyang CC BY-SA 4.0／NASA Public domain）※過去の試験飛行',
              '※実写表記のない映像はAI生成のイメージです。内容は2026年10月1日時点の公開情報にもとづきます。',
              '※Nina（ニーナ）はニッシン・パーテクチュアルの公式AIアンバサダーで、生成AIで制作されています。',
              '音声：ElevenLabs Eleven v4　映像：Higgsfield（Nano Banana／Wan 2.7／Seedance 2.5）　監修：代表取締役 中村 稔']:
        w, _ = tw(d, s, fs); d.text(((W - w) // 2, y), s, font=fs, fill=(205, 215, 228)); y += 42
    f2 = F(EN, 34); t = '#Nina  #ニーナの工場  #今日も新しく  #ニッシンパーテクチュアル'
    f2 = F(JP, 34); w, _ = tw(d, t, f2); d.text(((W - w) // 2, 860), t, font=f2, fill=CYAN)
    t = 'pertechtual.co.jp'; f3 = F(EN, 40); w, _ = tw(d, t, f3); d.text(((W - w) // 2, 930), t, font=f3, fill=WHITE)
    save('end', im)
ending()

c = new(); d = ImageDraw.Draw(c); f = F(JP, 96); t = '今日も、新しく。'
w, h = tw(d, t, f); box = Image.new('RGBA', (w + 120, h + 90), (0, 0, 0, 0))
ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width, box.height], radius=20, fill=NAVY + (215,))
ImageDraw.Draw(box).text((60, 30), t, font=f, fill=WHITE); place(c, box, (W - box.width) // 2, 660); save('kyomo', c)
c = new(); wm = wordmark(1.3); place(c, wm, (W - wm.width) // 2, 760); save('wm_big', c)
print('gfx ok', len(os.listdir(OUT)))
