# Monta .github/workflows/fappzap-acesso-apple.yml a partir do flutter-build.yml do RustDesk,
# do mesmo jeito que o montar-workflow.py faz com o de Windows e Android (ver o comentário de lá).
#
# O que sai: o .dmg do Mac (Apple Silicon e Intel) no release da tag escolhida, e o app de iPhone
# compilado SEM assinatura (artefato fappzap-acesso-ios-sem-assinatura), para assinar no Mac com a
# conta Apple e instalar pelo Xcode/devicectl. A assinatura e a notarização do RustDesk só rodam com
# os segredos MACOS_* deles, que não existem aqui: ficam desligadas sozinhas.
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / ".github/workflows/flutter-build.yml"
DESTINO = RAIZ / ".github/workflows/fappzap-acesso-apple.yml"
APP = "FappZap-Acesso"
JOBS = ["generate-bridge", "build-for-macOS", "build-rustdesk-ios"]

texto = FONTE.read_text(encoding="utf-8")
cab, corpo = texto.split("\njobs:\n", 1)


def exigir(cond, msg):
    if not cond:
        sys.exit(f"montar-workflow-apple: {msg} (o flutter-build.yml do RustDesk mudou; revisar o script)")


blocos = re.split(r"(?m)^(?=  [A-Za-z0-9_-]+:\s*$)", corpo)
por_nome = {}
for b in blocos:
    m = re.match(r"  ([A-Za-z0-9_-]+):", b)
    if m:
        por_nome[m.group(1)] = b
for j in JOBS:
    exigir(j in por_nome, f"job {j} sumiu")
jobs = {j: por_nome[j] for j in JOBS}

CHECKOUT = re.compile(r"(      - name: Checkout source code\n        uses: actions/checkout@[^\n]+\n        with:\n          submodules: recursive\n)")
PASSO = ("\n      - name: Aplicar a marca FappZap Acesso\n        shell: bash\n"
         "        run: python3 fappzap/aplicar-marca.py\n")
for j in ["build-for-macOS", "build-rustdesk-ios"]:
    novo, n = CHECKOUT.subn(r"\1" + PASSO, jobs[j])
    exigir(n == 1, f"checkout de {j} não encontrado")
    jobs[j] = novo

# Mac: o .app passa a se chamar FappZap-Acesso.app (PRODUCT_NAME que o aplicar-marca.py põe).
m = jobs["build-for-macOS"]
exigir('create-dmg --icon "RustDesk.app"' in m, "create-dmg do Mac mudou")
m = (m.replace("RustDesk.app", f"{APP}.app")
      .replace("rustdesk-${{ env.VERSION }}", "fappzap-acesso-${{ env.VERSION }}")
      .replace("name: rustdesk-unsigned-macos-", "name: fappzap-acesso-sem-assinatura-macos-")
      .replace("for name in rustdesk*??.dmg", "for name in fappzap-acesso*??.dmg")
      .replace("rustdesk*-${{ matrix.job.arch }}.dmg", "fappzap-acesso*-${{ matrix.job.arch }}.dmg"))
exigir("RustDesk.app" not in m, "sobrou RustDesk.app no job do Mac")
jobs["build-for-macOS"] = m

# iPhone: o RustDesk deixa o envio do .ipa comentado. Sem assinatura não sai .ipa, então
# sobe o Runner.app de dentro do .xcarchive (zipado com ditto, que preserva os links dos frameworks).
i = jobs["build-rustdesk-ios"]
exigir("          flutter build ipa --release --no-codesign\n" in i, "build do iPhone mudou")
i = re.sub(r"\n      # - name: Upload Artifacts\n.*\Z", "\n", i, flags=re.S)
i = i.rstrip("\n") + """

      - name: Empacotar o app de iPhone sem assinatura
        shell: bash
        run: |
          ditto -c -k --sequesterRsrc --keepParent flutter/build/ios/archive/Runner.xcarchive/Products/Applications/Runner.app fappzap-acesso-${{ env.VERSION }}-ios-sem-assinatura.zip

      - name: Enviar o app de iPhone sem assinatura
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: fappzap-acesso-ios-sem-assinatura
          path: fappzap-acesso-${{ env.VERSION }}-ios-sem-assinatura.zip

"""
jobs["build-rustdesk-ios"] = i

cab = re.sub(r"^name: .*$", "name: FappZap Acesso (Mac e iPhone)", cab, count=1, flags=re.M)
cab = re.sub(r"(?ms)^on:\n.*?(?=^# NOTE|^env:)", """on:
  workflow_dispatch:
    inputs:
      tag:
        description: "Tag do release onde o .dmg do Mac entra (ex.: acesso-1.5.0-mac-1)"
        required: true
        type: string

permissions:
  contents: write

""", cab, count=1)
cab = cab.replace("${{ inputs.upload-tag }}", "${{ inputs.tag }}")
cab = cab.replace('UPLOAD_ARTIFACT: "${{ inputs.upload-artifact }}"', 'UPLOAD_ARTIFACT: "true"')
exigir("inputs.upload-tag" not in cab and "TAG_NAME" in cab, "cabeçalho mudou")

saida = ("# GERADO por fappzap/montar-workflow-apple.py a partir do flutter-build.yml — não editar à mão.\n"
         + cab + "\njobs:\n" + "".join(jobs[j] for j in JOBS))
saida = saida.replace("${{ !inputs.upload-artifact && ", "${{ false && ")
saida = saida.replace("${{ inputs.upload-artifact }}", "true")
exigir("inputs.upload-artifact" not in saida, "sobrou inputs.upload-artifact")
DESTINO.write_text(saida, encoding="utf-8")
print(f"montar-workflow-apple: {DESTINO.relative_to(RAIZ)} ({len(saida.splitlines())} linhas)")
