# Edita fappzap/aplicar-marca.py para acrescentar o passo 3d (visual no padrão do FappZap).
# Roda uma vez, à mão, por quem mantém o fork. Não faz parte da compilação.
import io
from pathlib import Path

p = Path(__file__).resolve().parent / "aplicar-marca.py"
s = io.open(p, encoding="utf-8").read()
ancora = "# 4. Ícones: fappzap/marca/ espelha os caminhos do repositório\n"
assert s.count(ancora) == 1, "âncora do passo 4 não achada"
assert "# 3d." not in s, "o passo 3d já existe"

novo = r'''# 3d. Visual no padrão do FappZap: fonte Inter, botões, campos, diálogos e cartões do painel
# (cantos de 8 a 16 px, bordas lilás #E0E7FF, texto #1E1B4B, botão índigo sem sombra pesada).
# Só o tema CLARO muda de cor; o escuro mantém as cores do RustDesk e ganha a fonte e os cantos.
def trocar_na_regiao(caminho, inicio, fim, antes, depois):
    p = RAIZ / caminho
    s = p.read_text(encoding="utf-8")
    i = s.index(inicio)
    j = s.index(fim, i)
    reg = s[i:j]
    if reg.count(antes) < 1:
        sys.exit(f"aplicar-marca: não achei, no tema, o trecho esperado em {caminho}: {antes!r}")
    p.write_text(s[:i] + reg.replace(antes, depois) + s[j:], encoding="utf-8")

CLARO = ("static ThemeData lightTheme", "static ThemeData darkTheme")
ESCURO = ("static ThemeData darkTheme", "static ThemeMode getThemeModePreference")
for (ini, fim) in (CLARO, ESCURO):
    trocar_na_regiao(tema, ini, fim, "useMaterial3: false,\n", "useMaterial3: false,\n    fontFamily: 'Inter',\n")
    trocar_na_regiao(tema, ini, fim, "borderRadius: BorderRadius.circular(18.0),", "borderRadius: BorderRadius.circular(16.0),")

# claro: diálogo, campos, texto, botões e menu
trocar_na_regiao(tema, *CLARO, "          width: 1,\n          color: grayBg,\n", "          width: 1,\n          color: Color(0xFFE0E7FF),\n")
trocar_na_regiao(tema, *CLARO,
    "            fillColor: grayBg,\n            filled: true,\n            isDense: true,\n            border: OutlineInputBorder(\n              borderRadius: BorderRadius.circular(8),\n            ),\n",
    "            fillColor: Colors.white,\n            filled: true,\n            isDense: true,\n"
    "            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),\n"
    "            border: OutlineInputBorder(\n              borderRadius: BorderRadius.circular(8),\n              borderSide: BorderSide(color: Color(0xFFE0E7FF)),\n            ),\n"
    "            enabledBorder: OutlineInputBorder(\n              borderRadius: BorderRadius.circular(8),\n              borderSide: BorderSide(color: Color(0xFFE0E7FF)),\n            ),\n"
    "            focusedBorder: OutlineInputBorder(\n              borderRadius: BorderRadius.circular(8),\n              borderSide: BorderSide(color: Color(0xFF6366F1), width: 1.5),\n            ),\n")
trocar_na_regiao(tema, *CLARO,
    "        backgroundColor: MyTheme.accent,\n        shape: RoundedRectangleBorder(",
    "        backgroundColor: MyTheme.accent,\n        foregroundColor: Colors.white,\n        elevation: 0,\n"
    "        textStyle: const TextStyle(fontWeight: FontWeight.w600),\n        shape: RoundedRectangleBorder(")
trocar_na_regiao(tema, *CLARO,
    "        backgroundColor: grayBg,\n        foregroundColor: Colors.black87,\n",
    "        backgroundColor: Colors.white,\n        foregroundColor: Color(0xFF1E1B4B),\n"
    "        side: BorderSide(color: Color(0xFFE0E7FF)),\n        textStyle: const TextStyle(fontWeight: FontWeight.w600),\n")
trocar_na_regiao(tema, *CLARO, "Colors.black87", "Color(0xFF1E1B4B)")
trocar_na_regiao(tema, *CLARO, "Color(0xFFECECEC)", "Color(0xFFE0E7FF)")
trocar_na_regiao(tema, *CLARO, "borderRadius: BorderRadius.all(Radius.circular(8.0)),", "borderRadius: BorderRadius.all(Radius.circular(10.0)),")
# escuro: botão principal com o mesmo peso de letra e sem sombra
trocar_na_regiao(tema, *ESCURO,
    "        backgroundColor: MyTheme.accent,\n        foregroundColor: Colors.white,\n",
    "        backgroundColor: MyTheme.accent,\n        foregroundColor: Colors.white,\n        elevation: 0,\n        textStyle: const TextStyle(fontWeight: FontWeight.w600),\n")
trocar_na_regiao(tema, *ESCURO, "      primary: Colors.blue,\n", "      primary: accent,\n")

# "Conectar" e demais botões do RustDesk: cantos de 8 px (eram 5) e letra mais firme.
botao = "flutter/lib/desktop/widgets/button.dart"
trocar(botao, "BorderRadius.circular(widget.radius ?? 5)", "BorderRadius.circular(widget.radius ?? 8)")
trocar(botao, "fontSize: widget.textSize ?? 12.0,", "fontSize: widget.textSize ?? 13.0,\n                      fontWeight: FontWeight.w600,")

# Fonte Inter (SIL OFL 1.1), embutida no programa: 4 pesos, ~1,7 MB.
for peso, nome in ((400, "Regular"), (500, "Medium"), (600, "SemiBold"), (700, "Bold")):
    destino = RAIZ / "flutter" / "assets" / "fonts" / f"Inter-{nome}.ttf"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).resolve().parent / "fontes" / f"Inter-{nome}.ttf", destino)
shutil.copyfile(Path(__file__).resolve().parent / "fontes" / "Inter-LICENSE.txt", RAIZ / "flutter" / "assets" / "fonts" / "Inter-LICENSE.txt")
trocar("flutter/pubspec.yaml", "  fonts:\n    - family: GestureIcons\n",
       "  fonts:\n    - family: Inter\n      fonts:\n"
       "        - asset: assets/fonts/Inter-Regular.ttf\n          weight: 400\n"
       "        - asset: assets/fonts/Inter-Medium.ttf\n          weight: 500\n"
       "        - asset: assets/fonts/Inter-SemiBold.ttf\n          weight: 600\n"
       "        - asset: assets/fonts/Inter-Bold.ttf\n          weight: 700\n"
       "    - family: GestureIcons\n")

'''
s = s.replace(ancora, novo + ancora)
io.open(p, "w", encoding="utf-8", newline="").write(s)
print("passo 3d acrescentado")
