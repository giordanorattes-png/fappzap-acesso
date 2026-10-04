# Monta .github/workflows/fappzap-acesso.yml a partir do flutter-build.yml do RustDesk.
#
# Por que gerar em vez de escrever à mão: o flutter-build.yml é o que o RustDesk usa para os
# instaladores oficiais (versões de Flutter, NDK, vcpkg, drivers...). A cada versão nova do
# RustDesk, rebaseia-se o branch fappzap na tag nova e roda-se este script de novo — a nossa
# compilação herda as correções deles sem copiar 2.600 linhas na mão.
#
# O que ele faz: fica só com Windows x64 e Android; aplica a marca logo depois de cada checkout;
# troca os nomes dos arquivos para fappzap-acesso-*; dá o nome FappZap-Acesso ao .exe e ao MSI;
# tira o que é da RustDesk (assinatura deles, molde de MSI do gerador pago, iOS, Mac, Linux).
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / ".github/workflows/flutter-build.yml"
DESTINO = RAIZ / ".github/workflows/fappzap-acesso.yml"
APP = "FappZap-Acesso"
JOBS = ["generate-bridge", "build-RustDeskTempTopMostWindow", "build-for-windows-flutter",
        "build-rustdesk-android", "build-rustdesk-android-universal"]

texto = FONTE.read_text(encoding="utf-8")
cab, corpo = texto.split("\njobs:\n", 1)


def exigir(cond, msg):
    if not cond:
        sys.exit(f"montar-workflow: {msg} (o flutter-build.yml do RustDesk mudou; revisar o script)")


# ── jobs: separa pelo recuo de 2 espaços e fica só com os nossos ──
blocos = re.split(r"(?m)^(?=  [A-Za-z0-9_-]+:\s*$)", corpo)
por_nome = {}
for b in blocos:
    m = re.match(r"  ([A-Za-z0-9_-]+):", b)
    if m:
        por_nome[m.group(1)] = b
for j in JOBS:
    exigir(j in por_nome, f"job {j} sumiu")
jobs = {j: por_nome[j] for j in JOBS}

# Sem ARM: só Windows x64 (o matrix de cada job lista os alvos em blocos "- {...}").
def sem_arm(b):
    return re.sub(r"\n          - \{[^}]*?(?:windows-11-arm|aarch64-pc-windows)[^}]*\}", "", b, flags=re.S)
jobs["build-RustDeskTempTopMostWindow"] = sem_arm(jobs["build-RustDeskTempTopMostWindow"])
jobs["build-for-windows-flutter"] = sem_arm(jobs["build-for-windows-flutter"])
exigir("aarch64-pc-windows" not in jobs["build-for-windows-flutter"], "não consegui tirar o Windows ARM")

# A marca entra logo depois de cada checkout (com submódulos: a chave mora no hbb_common).
CHECKOUT = re.compile(r"(      - name: Checkout source code\n        uses: actions/checkout@[^\n]+\n        with:\n          submodules: recursive\n)")
PASSO = ("\n      - name: Aplicar a marca FappZap Acesso\n        shell: bash\n"
         "        run: python3 fappzap/aplicar-marca.py\n")
for j in ["build-for-windows-flutter", "build-rustdesk-android", "build-rustdesk-android-universal"]:
    novo, n = CHECKOUT.subn(r"\1" + PASSO, jobs[j])
    exigir(n == 1, f"checkout de {j} não encontrado")
    jobs[j] = novo

# Windows: o .exe com o nosso nome, o MSI com --app-name e sem o molde do gerador pago.
w = jobs["build-for-windows-flutter"]
alvo = "runner/Release ./rustdesk\n"
exigir(alvo in w, "passo que move o Release para ./rustdesk mudou")
w = w.replace(alvo, alvo + f"          mv ./rustdesk/rustdesk.exe ./rustdesk/{APP}.exe\n", 1)
exigir("-e ../../rustdesk/rustdesk.exe" in w, "gerador do portátil mudou")
w = w.replace("-e ../../rustdesk/rustdesk.exe", f"-e ../../rustdesk/{APP}.exe")
exigir("python preprocess.py --arp -d ../../rustdesk" in w, "preprocess do MSI mudou")
w = w.replace("python preprocess.py --arp -d ../../rustdesk",
              f'python preprocess.py --arp -d ../../rustdesk --app-name {APP} --manufacturer "Fapp Solutions"')
w = re.sub(r"\n      - name: Build pre-built MSI template\n.*?(?=\n      - name: Sign rustdesk self-extracted file)",
           "\n", w, flags=re.S)
exigir("RDAPPNAM" not in w, "não consegui tirar o molde de MSI")
jobs["build-for-windows-flutter"] = w

# Nomes dos arquivos publicados.
for j in jobs:
    jobs[j] = (jobs[j].replace("SignOutput/rustdesk-", "SignOutput/fappzap-acesso-")
               .replace("signed-apk/rustdesk-", "signed-apk/fappzap-acesso-")
               .replace("../rustdesk-${{ env.VERSION }}", "../fappzap-acesso-${{ env.VERSION }}")
               .replace("name: rustdesk-${{ env.VERSION }}", "name: fappzap-acesso-${{ env.VERSION }}")
               .replace("name: rustdesk-unsigned-windows", "name: fappzap-acesso-sem-assinatura-windows"))

# ── cabeçalho: disparo manual, publica no release da tag escolhida ──
cab = re.sub(r"^name: .*$", "name: FappZap Acesso (Windows e Android)", cab, count=1, flags=re.M)
cab = re.sub(r"(?ms)^on:\n.*?(?=^# NOTE|^env:)", """on:
  workflow_dispatch:
    inputs:
      tag:
        description: "Tag do release onde os arquivos entram (ex.: acesso-1.5.0-1)"
        required: true
        type: string

permissions:
  contents: write

""", cab, count=1)
cab = cab.replace("${{ inputs.upload-tag }}", "${{ inputs.tag }}")
cab = cab.replace('UPLOAD_ARTIFACT: "${{ inputs.upload-artifact }}"', 'UPLOAD_ARTIFACT: "true"')
exigir("inputs.upload-tag" not in cab and "TAG_NAME" in cab, "cabeçalho mudou")

saida = ("# GERADO por fappzap/montar-workflow.py a partir do flutter-build.yml — não editar à mão.\n"
         + cab + "\njobs:\n" + "".join(jobs[j] for j in JOBS))
saida = saida.replace("${{ inputs.upload-artifact }}", "true")
DESTINO.write_text(saida, encoding="utf-8")
print(f"montar-workflow: {DESTINO.relative_to(RAIZ)} ({len(saida.splitlines())} linhas)")
