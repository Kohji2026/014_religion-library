"""
Excelの「宗教一覧」シートから宗教ロゴ画像を抽出してlogos/フォルダに保存するスクリプト
==========================================================================
・画像は sheet2.xml (= 宗教一覧) の行3にある vm 属性付きセルに格納
・vm=N → richValueRel.xml の N番目(1-indexed) → rId → 画像ファイル
・行2で列番号 → 宗教名を取得

実行:
    uv run --with openpyxl extract_logos.py
"""

import re
import zipfile
from pathlib import Path

def _load_env():
    """スクリプトと同じフォルダの .env からパス設定を読み込む"""
    env = {}
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

_env = _load_env()
INPUT_EXCEL = Path(_env.get("RELIGION_EXCEL", ""))
OUTPUT_DIR  = Path(__file__).parent / "logos"

def col_letter_to_num(col_str):
    """A→1, B→2, Z→26, AA→27, ..."""
    n = 0
    for ch in col_str:
        n = n * 26 + (ord(ch) - ord('A') + 1)
    return n

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    with zipfile.ZipFile(INPUT_EXCEL, 'r') as z:
        namelist = z.namelist()

        # ===== 共有文字列テーブル =====
        shared_strings = []
        if 'xl/sharedStrings.xml' in namelist:
            ss_xml = z.read('xl/sharedStrings.xml').decode('utf-8', errors='replace')
            for si in re.findall(r'<si>(.*?)</si>', ss_xml, re.DOTALL):
                texts = re.findall(r'<t[^>]*>([^<]*)</t>', si)
                shared_strings.append(''.join(texts))
        print(f"共有文字列: {len(shared_strings)} 件")

        # ===== richValueRel.xml.rels: rId → 画像ファイル名 =====
        rels_path = 'xl/richData/_rels/richValueRel.xml.rels'
        rid_to_img = {}
        if rels_path in namelist:
            rels_xml = z.read(rels_path).decode('utf-8', errors='replace')
            # <Relationship Id="rId26" Type="..." Target="../media/image26.png"/>
            for m in re.finditer(r'Id="(rId\d+)"[^>]+Target="\.\.\/media\/([^"]+)"', rels_xml):
                rid_to_img[m.group(1)] = m.group(2)
        print(f"rId→画像マッピング: {len(rid_to_img)} 件")

        # ===== richValueRel.xml: 位置(0-indexed) → rId =====
        rvrel_path = 'xl/richData/richValueRel.xml'
        pos_to_rid = {}
        if rvrel_path in namelist:
            rvrel_xml = z.read(rvrel_path).decode('utf-8', errors='replace')
            rids = re.findall(r'r:id="(rId\d+)"', rvrel_xml)
            for i, rid in enumerate(rids):
                pos_to_rid[i] = rid
        print(f"位置→rId: {len(pos_to_rid)} 件")

        # ===== sheet2.xml (宗教一覧) の読み込み =====
        sheet2_path = 'xl/worksheets/sheet2.xml'
        if sheet2_path not in namelist:
            print("sheet2.xmlが見つかりません")
            return
        s2xml = z.read(sheet2_path).decode('utf-8', errors='replace')

        # --- 行2: 列番号 → 宗教名 ---
        col_to_name = {}
        row2m = re.search(r'<row[^>]+r="2"[^>]*>(.*?)</row>', s2xml, re.DOTALL)
        if row2m:
            for cm in re.finditer(r'<c r="([A-Z]+)2"[^>]*t="s"[^>]*><v>(\d+)</v>', row2m.group(1)):
                col_num = col_letter_to_num(cm.group(1))
                ss_idx  = int(cm.group(2))
                if ss_idx < len(shared_strings):
                    name = shared_strings[ss_idx]
                    if name:  # 空でなければ
                        col_to_name[col_num] = name
        print(f"\n行2 宗教名({len(col_to_name)}件): {list(col_to_name.values())[:10]}...")

        # --- 行3: 列番号 → vm値 (画像インデックス) ---
        col_to_vm = {}
        row3m = re.search(r'<row[^>]+r="3"[^>]*>(.*?)</row>', s2xml, re.DOTALL)
        if row3m:
            for cm in re.finditer(r'<c r="([A-Z]+)3"[^>]*vm="(\d+)"', row3m.group(1)):
                col_num = col_letter_to_num(cm.group(1))
                vm_val  = int(cm.group(2))
                col_to_vm[col_num] = vm_val
        print(f"行3 vm属性({len(col_to_vm)}件): {dict(list(col_to_vm.items())[:5])}...")

        # ===== vm値 → 画像ファイル を解決 =====
        # vm=N → pos_to_rid の N-1番目(0-indexed) → rId → 画像
        def vm_to_imgfile(vm_val):
            pos = vm_val - 1  # 1-indexed → 0-indexed
            rid = pos_to_rid.get(pos)
            if rid:
                return rid_to_img.get(rid, None)
            return None

        # ===== 対応マップを出力して保存 =====
        print("\n--- 対応マップ ---")
        saved = 0
        missing = []

        for col in sorted(col_to_vm.keys()):
            vm  = col_to_vm[col]
            rel = col_to_name.get(col, f"col{col}")
            img = vm_to_imgfile(vm)

            pos = vm - 1
            rid = pos_to_rid.get(pos, '?')
            print(f"  列{col:2d} [{rel:<15}]  vm={vm} → pos={pos} → {rid} → {img or '(なし)'}")

            if img:
                src = f"xl/media/{img}"
                if src in namelist:
                    ext = Path(img).suffix
                    dest = OUTPUT_DIR / f"{rel}{ext}"
                    dest.write_bytes(z.read(src))
                    saved += 1
                else:
                    missing.append(f"{rel}: {src}")
            else:
                missing.append(f"{rel}: vm={vm}に対応画像なし")

        print(f"\n✅ 保存: {saved} 件")
        if missing:
            print(f"⚠️  保存できなかった宗教: {len(missing)} 件")
            for m in missing:
                print(f"   {m}")

    print(f"\n保存先: {OUTPUT_DIR}")
    for f in sorted(OUTPUT_DIR.iterdir()):
        print(f"  {f.name}  ({f.stat().st_size:,} bytes)")

if __name__ == '__main__':
    main()
