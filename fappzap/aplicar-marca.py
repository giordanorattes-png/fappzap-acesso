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
