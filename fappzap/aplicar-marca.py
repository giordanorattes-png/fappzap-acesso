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
trocar("src/platform/windows.cc",
       "            if (CreateProcessAsUserW(hToken, NULL, buf, NULL, NULL, FALSE, dwCreationFlags, lpEnvironment, NULL, &si, &pi))\n",
       "            // FappZap Acesso: fora do pacote da Store quando o servico esta empacotado.\n"
       "            STARTUPINFOEXW six;\n"
       "            ZeroMemory(&six, sizeof six);\n"
       "            six.StartupInfo = si;\n"
       "            six.StartupInfo.cb = sizeof six;\n"
       "            std::vector<BYTE> attrBuf;\n"
       "            DWORD policy = 0x01; // PROCESS_CREATION_DESKTOP_APP_BREAKAWAY_ENABLE_PROCESS_TREE\n"
       "            typedef LONG(WINAPI * PGetCurrentPackageFullName)(UINT32 *, PWSTR);\n"
       "            PGetCurrentPackageFullName fzPkg = (PGetCurrentPackageFullName)GetProcAddress(GetModuleHandleW(L\"kernel32.dll\"), \"GetCurrentPackageFullName\");\n"
       "            UINT32 fzLen = 0;\n"
       "            BOOL fzEmpacotado = fzPkg && fzPkg(&fzLen, NULL) == ERROR_INSUFFICIENT_BUFFER;\n"
       "            if (fzEmpacotado)\n"
       "            {\n"
       "                SIZE_T attrSize = 0;\n"
       "                InitializeProcThreadAttributeList(NULL, 1, 0, &attrSize);\n"
       "                attrBuf.resize(attrSize);\n"
       "                six.lpAttributeList = (LPPROC_THREAD_ATTRIBUTE_LIST)attrBuf.data();\n"
       "                if (InitializeProcThreadAttributeList(six.lpAttributeList, 1, 0, &attrSize) &&\n"
       "                    UpdateProcThreadAttribute(six.lpAttributeList, 0, ProcThreadAttributeValue(18, FALSE, TRUE, FALSE), &policy, sizeof policy, NULL, NULL))\n"
       "                {\n"
       "                    dwCreationFlags |= EXTENDED_STARTUPINFO_PRESENT;\n"
       "                }\n"
       "                else\n"
       "                {\n"
       "                    six.lpAttributeList = NULL;\n"
       "                }\n"
       "            }\n"
       "            BOOL fzOk = (dwCreationFlags & EXTENDED_STARTUPINFO_PRESENT)\n"
       "                ? CreateProcessAsUserW(hToken, NULL, buf, NULL, NULL, FALSE, dwCreationFlags, lpEnvironment, NULL, &six.StartupInfo, &pi)\n"
       "                : CreateProcessAsUserW(hToken, NULL, buf, NULL, NULL, FALSE, dwCreationFlags, lpEnvironment, NULL, &si, &pi);\n"
       "            if (six.lpAttributeList)\n"
       "                DeleteProcThreadAttributeList(six.lpAttributeList);\n"
       "            if (fzOk)\n")

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
