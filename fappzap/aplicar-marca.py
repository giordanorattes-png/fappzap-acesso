# Transforma o RustDesk desta pasta no FappZap Acesso. Roda no CI logo depois do checkout
# (com os submódulos), antes de qualquer compilação, numa cópia limpa (roda uma vez só).
#
# Cada troca confere que o texto original ainda existe. Se uma versão nova do RustDesk mudar
# um desses trechos, o script PARA com o nome do arquivo, em vez de compilar um programa com
# meia marca (ou, pior, apontando para o servidor público do RustDesk).
#
# O que NÃO muda de propósito: tudo que o RustDesk mostra para quem está sendo acessado
# (ícone na bandeja, aviso de conexão, botão de desconectar, "Powered by RustDesk"). Só a marca.
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MARCA = Path(__file__).resolve().parent / "marca"

# O nome interno não pode ter espaço: o RustDesk o usa como esquema de link (fappzap-acesso://),
# nome do .exe, chave de registro e alvo de taskkill. Só letras, números e hífen.
APP_NAME = "FappZap-Acesso"
NOME_VISIVEL = "FappZap Acesso"
ORG = "com.fappsolutions"
SERVIDOR = "acesso.fappsolutions.com"
# Chave PÚBLICA do servidor (/srv/rustdesk/data/id_ed25519.pub na VPS). Não é segredo.
CHAVE_PUBLICA = "lT1N3Da8QQs5CL4TbCKZY7e304PT+pFxdQWX5XHyCxY="
PACOTE_ANDROID = "com.fappsolutions.acesso"
COR_FUNDO_ANDROID = "#0e7490"
EMPRESA = "Fapp Solutions"
COPYRIGHT = "© 2026 Fapp Solutions. Baseado no RustDesk (AGPL-3.0), © Purslane Tech Pte. Ltd."


def trocar(caminho, padrao, novo, regex=False):
    p = RAIZ / caminho
    s = p.read_text(encoding="utf-8")
    if regex:
        s, n = re.subn(padrao, novo, s, flags=re.M)
    else:
        n = s.count(padrao)
        s = s.replace(padrao, novo)
    if n == 0:
        sys.exit(f"aplicar-marca: não achei o trecho esperado em {caminho}: {padrao!r}")
    p.write_text(s, encoding="utf-8")


# 1. Servidor, chave, nome e organização
cfg = "libs/hbb_common/src/config.rs"
trocar(cfg, r'^pub const RENDEZVOUS_SERVERS: &\[&str\] = &\[[^\]]*\];',
       f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{SERVIDOR}"];', regex=True)
trocar(cfg, r'^pub const RS_PUB_KEY: &str = "[^"]*";',
       f'pub const RS_PUB_KEY: &str = "{CHAVE_PUBLICA}";', regex=True)
trocar(cfg, r'(pub static ref APP_NAME: RwLock<String> = RwLock::new\(")[^"]*("\.to_owned\(\)\);)',
       rf'\g<1>{APP_NAME}\g<2>', regex=True)
trocar(cfg, r'(pub static ref ORG: RwLock<String> = RwLock::new\(")[^"]*("\.to_owned\(\)\);)',
       rf'\g<1>{ORG}\g<2>', regex=True)
# O servidor também entra como configuração padrão: sem isto o RustDesk se acha no servidor
# público e mostra "configure seu próprio servidor" embaixo da tela. Padrão (não travado):
# quem precisar ainda pode trocar em Rede; apagando, volta para o nosso do mesmo jeito.
trocar(cfg, "pub static ref DEFAULT_SETTINGS: RwLock<HashMap<String, String>> = Default::default();",
       "pub static ref DEFAULT_SETTINGS: RwLock<HashMap<String, String>> = RwLock::new(HashMap::from(["
       f'("custom-rendezvous-server".to_owned(), "{SERVIDOR}".to_owned()), '
       f'("key".to_owned(), "{CHAVE_PUBLICA}".to_owned())]));')

# 1b. VARIANTE DA MICROSOFT STORE (FAPPZAP_VARIANTE=loja): sem "Instalar". Instalar copiaria o programa para
# fora do pacote da Store (o Windows deixaria de confiar nele e a Store não quer isso). O resto é igual.
import os
if os.environ.get("FAPPZAP_VARIANTE") == "loja":
    trocar(cfg, "pub static ref HARD_SETTINGS: RwLock<HashMap<String, String>> = Default::default();",
           "pub static ref HARD_SETTINGS: RwLock<HashMap<String, String>> = RwLock::new(HashMap::from(["
           '("disable-installation".to_owned(), "Y".to_owned())]));')

# 2. Windows: metadados do .exe (Propriedades → Detalhes e o Gerenciador de Tarefas)
trocar("Cargo.toml", r'^LegalCopyright = ".*"$', f'LegalCopyright = "{COPYRIGHT}"', regex=True)
trocar("Cargo.toml", r'^ProductName = "RustDesk"$', f'ProductName = "{NOME_VISIVEL}"', regex=True)
trocar("Cargo.toml", r'^FileDescription = ".*"$', f'FileDescription = "{NOME_VISIVEL}"', regex=True)
trocar("Cargo.toml", r'^OriginalFilename = ".*"$', f'OriginalFilename = "{APP_NAME}.exe"', regex=True)
rc = "flutter/windows/runner/Runner.rc"
for campo, valor in [("CompanyName", EMPRESA), ("FileDescription", NOME_VISIVEL),
                     ("LegalCopyright", COPYRIGHT), ("OriginalFilename", f"{APP_NAME}.exe"),
                     ("ProductName", NOME_VISIVEL)]:
    trocar(rc, rf'(VALUE "{campo}", )"[^"]*"', rf'\g<1>"{valor}"', regex=True)

# 3. Android: pacote próprio (instala ao lado do RustDesk oficial), nome e cor do ícone
trocar("flutter/android/app/build.gradle", r'applicationId "[^"]*"', f'applicationId "{PACOTE_ANDROID}"', regex=True)
man = "flutter/android/app/src/main/AndroidManifest.xml"
trocar(man, 'android:label="RustDesk Input"', f'android:label="{NOME_VISIVEL} Input"')
trocar(man, 'android:label="RustDesk"', f'android:label="{NOME_VISIVEL}"')
trocar("flutter/android/app/src/main/res/values/strings.xml", ">RustDesk<", f">{NOME_VISIVEL}<")
trocar("flutter/android/app/src/main/res/values/strings.xml", "RustDesk screen sharing", f"{NOME_VISIVEL} screen sharing")
trocar("flutter/android/app/src/main/res/values/strings.xml", "Keeps the RustDesk remote", f"Keeps the {NOME_VISIVEL} remote")
trocar("flutter/android/app/src/main/res/values/ic_launcher_background.xml",
       r'(<color name="ic_launcher_background">)#[0-9a-fA-F]+(</color>)', rf'\g<1>{COR_FUNDO_ANDROID}\g<2>', regex=True)

# 3b. Cores do tema claro iguais às do painel do FappZap (tailwind.config.js do FappZap:
# primary 500 #6366f1 / 600 #4f46e5, fundo #F5F3FF, bordas #E0E7FF). O tema escuro fica o do RustDesk.
tema = "flutter/lib/common.dart"
for antes, depois in [
    ("static const Color grayBg = Color(0xFFEFEFF2);", "static const Color grayBg = Color(0xFFF5F3FF);"),
    ("static const Color accent = Color(0xFF0071FF);", "static const Color accent = Color(0xFF4F46E5);"),
    ("static const Color accent50 = Color(0x770071FF);", "static const Color accent50 = Color(0x774F46E5);"),
    ("static const Color accent80 = Color(0xAA0071FF);", "static const Color accent80 = Color(0xAA4F46E5);"),
    ("static const Color idColor = Color(0xFF00B6F0);", "static const Color idColor = Color(0xFF4F46E5);"),
    ("static const Color button = Color(0xFF2C8CFF);", "static const Color button = Color(0xFF6366F1);"),
    ("hoverColor: Color.fromARGB(255, 224, 224, 224),", "hoverColor: Color(0xFFE0E7FF),"),
    ("primary: Colors.blue, secondary: accent, background: grayBg),", "primary: accent, secondary: accent, background: grayBg),"),
    # Só a ColorThemeExtension.light: a dark tem border 0xFF555555 e highlight 0xFF3F3F3F.
    ("border: Color(0xFFCCCCCC),\n    border2: Color(0xFFBBBBBB),",
     "border: Color(0xFFE0E7FF),\n    border2: Color(0xFFC7D2FE),"),
    ("highlight: Color(0xFFE5E5E5),", "highlight: Color(0xFFEEF2FF),"),
]:
    trocar(tema, antes, depois)
trocar("flutter/android/app/src/main/res/values/colors.xml", "#FF0071FF", "#FF4F46E5")

# 3c. Pacote da Microsoft Store (MSIX). Fora do pacote nada disto muda o comportamento.
# (1) Instalado pela Store, o programa mora em ...\WindowsApps\...: sem isto ele procura a si
#     mesmo em Program Files, não se acha instalado, vira "portátil", pede administrador e fecha.
trocar("src/platform/windows.rs",
       "    if path.is_empty() {\n        path = get_default_install_path();\n    }\n    path = path.trim_end_matches('\\\\').to_owned();\n",
       "    if path.is_empty() {\n        path = get_default_install_path();\n    }\n"
       "    // FappZap Acesso: no pacote da Store, a instalação é a pasta do próprio pacote.\n"
       "    if let Ok(exe) = std::env::current_exe() {\n"
       "        if exe.to_string_lossy().to_lowercase().contains(\"\\\\windowsapps\\\\\") {\n"
       "            if let Some(dir) = exe.parent() {\n"
       "                path = dir.to_string_lossy().to_string();\n"
       "            }\n"
       "        }\n"
       "    }\n"
       "    path = path.trim_end_matches('\\\\').to_owned();\n")
# (2) O serviço empacotado abre o programa na sessão do usuário: o processo filho herdava a
#     identidade do pacote e morria ao iniciar (erro 575). Com o "breakaway" ele roda como no
#     instalador MSI. Só pede o breakaway quando o próprio serviço está dentro de um pacote.
#     As tentativas e o registro estão em fappzap/patches/lancamento-empacotado.cc.
trocar("src/platform/windows.cc",
       "    HANDLE LaunchProcessWin(LPCWSTR cmd, DWORD dwSessionId, BOOL as_user, BOOL show, DWORD *pDwTokenPid)\n",
       (Path(__file__).resolve().parent / "patches" / "lancamento-empacotado.cc").read_text(encoding="utf-8")
       + "    HANDLE LaunchProcessWin(LPCWSTR cmd, DWORD dwSessionId, BOOL as_user, BOOL show, DWORD *pDwTokenPid)\n")
trocar("src/platform/windows.cc",
       "            if (CreateProcessAsUserW(hToken, NULL, buf, NULL, NULL, FALSE, dwCreationFlags, lpEnvironment, NULL, &si, &pi))\n",
       "            if (FzCreateProcess(hToken, buf, dwCreationFlags, lpEnvironment, &si, &pi))\n")

# 3d. Visual no padrão do FappZap: fonte Inter, botões, campos, diálogos e cartões do painel
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

# 4. Ícones: fappzap/marca/ espelha os caminhos do repositório
copiados = 0
for origem in MARCA.rglob("*"):
    if origem.is_file() and not origem.name.startswith("."):
        destino = RAIZ / origem.relative_to(MARCA)
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origem, destino)
        copiados += 1
if copiados < 30:
    sys.exit(f"aplicar-marca: só {copiados} arquivos de marca - rode fappzap/gerar-marca.mjs")

print(f"aplicar-marca: {APP_NAME} -> {SERVIDOR}, {copiados} arquivos de marca")
