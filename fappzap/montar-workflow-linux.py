# Monta .github/workflows/fappzap-acesso-linux.yml a partir do flutter-build.yml do RustDesk,
# do mesmo jeito que o montar-workflow.py faz com o de Windows e Android (ver o comentário de lá).
#
# O que sai: o .deb de Linux x86_64 (Debian, Ubuntu, Kali...) no release da tag escolhida, com a marca
# trocada por fappzap/linux/remarcar-deb.sh, e um teste que instala esse .deb num container do Kali
# (kalilinux/kali-rolling), sobe o --server e confere que a máquina ganhou um ID no NOSSO servidor.
# Fora: ARM, rpm, SUSE, Arch, AppImage, Flatpak e o .deb "unattended-wayland" (drm).
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / ".github/workflows/flutter-build.yml"
DESTINO = RAIZ / ".github/workflows/fappzap-acesso-linux.yml"
JOBS = ["generate-bridge", "build-rustdesk-linux"]

texto = FONTE.read_text(encoding="utf-8")
cab, corpo = texto.split("\njobs:\n", 1)


def exigir(cond, msg):
    if not cond:
        sys.exit(f"montar-workflow-linux: {msg} (o flutter-build.yml do RustDesk mudou; revisar o script)")


blocos = re.split(r"(?m)^(?=  [A-Za-z0-9_-]+:\s*$)", corpo)
por_nome = {}
for b in blocos:
    m = re.match(r"  ([A-Za-z0-9_-]+):", b)
    if m:
        por_nome[m.group(1)] = b
for j in JOBS:
    exigir(j in por_nome, f"job {j} sumiu")
jobs = {j: por_nome[j] for j in JOBS}

L = jobs["build-rustdesk-linux"]
# Só x86_64.
L, n = re.subn(r"\n          - \{[^}]*?arch: aarch64[^}]*\}", "", L, flags=re.S)
exigir(n == 1 and "aarch64-unknown-linux-gnu" not in L, "não consegui tirar o ARM")

# A marca entra logo depois do checkout (com submódulos: a chave mora no hbb_common).
CHECKOUT = re.compile(r"(      - name: Checkout source code\n        uses: actions/checkout@[^\n]+\n        with:\n          submodules: recursive\n)")
PASSO = ("\n      - name: Aplicar a marca FappZap Acesso\n        shell: bash\n"
         "        run: python3 fappzap/aplicar-marca.py\n")
L, n = CHECKOUT.subn(r"\1" + PASSO, L)
exigir(n == 1, "checkout do Linux não encontrado")

# Sem rpm/SUSE: o build para no .deb.
L, n = re.subn(r"\n\n            # rpm package\n.*?(?=\n\n      - name: Publish debian/rpm package\n)", "\n", L, flags=re.S)
exigir(n == 1, "trecho do rpm mudou")

# Publicação: troca a marca do .deb e publica só ele; sem Arch.
PUB = re.compile(r"      - name: Publish debian/rpm package\n.*\Z", re.S)
exigir(PUB.search(L), "passo Publish debian/rpm package mudou")
L = PUB.sub("""      - name: Marca FappZap Acesso no .deb
        run: |
          sudo chown -R "$(id -u):$(id -g)" .
          bash fappzap/linux/remarcar-deb.sh rustdesk-${{ env.VERSION }}-x86_64.deb fappzap-acesso-${{ env.VERSION }}-x86_64.deb

      - name: Publish debian package
        uses: softprops/action-gh-release@de2c0eb89ae2a093876385947365aca7b0e5f844 # v1
        with:
          prerelease: true
          tag_name: ${{ env.TAG_NAME }}
          files: |
            fappzap-acesso-*.deb

      - name: Upload deb
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: fappzap-acesso-linux-deb
          path: fappzap-acesso-${{ env.VERSION }}-x86_64.deb

""", L)
jobs["build-rustdesk-linux"] = L

# Teste no Kali: instala o .deb, sobe o --server (sem systemd no container) e espera o ID e o
# key_confirmed = true no FappZap-Acesso.toml — o RustDesk só grava isso quando o hbbs responde OK ao
# RegisterPk (rendezvous_mediator.rs), ou seja, a máquina ficou registrada no NOSSO servidor.
TESTE = """  testar-no-kali:
    needs: [build-rustdesk-linux]
    name: instalar no Kali (container kalilinux/kali-rolling)
    runs-on: ubuntu-24.04
    container: kalilinux/kali-rolling
    steps:
      - name: Baixar o .deb
        uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1
        with:
          name: fappzap-acesso-linux-deb
          path: ./deb

      - name: Instalar
        run: |
          export DEBIAN_FRONTEND=noninteractive
          apt-get update -y
          apt-get install -y ./deb/fappzap-acesso-*.deb xvfb xauth iproute2 procps
          dpkg -s fappzap-acesso | sed -n '/Package:/p;/Version:/p;/Status:/p'
          test -x /usr/share/fappzap-acesso/fappzap-acesso
          test -L /usr/bin/fappzap-acesso
          cat /etc/os-release | head -3

      - name: Abrir e registrar no servidor do FappZap Acesso
        run: |
          xvfb-run -a -s "-screen 0 1280x800x24" fappzap-acesso --server > server.log 2>&1 &
          CFG=~/.config/fappzap-acesso/FappZap-Acesso.toml
          OK=0
          for i in $(seq 1 60); do
            ID=$(fappzap-acesso --get-id 2>/dev/null | tail -1 | tr -dc '0-9')
            grep -q "^key_confirmed = true" "$CFG" 2>/dev/null && OK=1
            [ -n "$ID" ] && [ "$OK" = 1 ] && break
            sleep 2
          done
          ls -la ~/.config/fappzap-acesso/ || true
          grep -E "^(id|key_confirmed|rendezvous_server) " "$CFG" || true
          grep -E "custom-rendezvous-server|relay-server" ~/.config/fappzap-acesso/FappZap-Acesso2.toml || true
          tail -n 30 ~/.local/share/logs/FappZap-Acesso/server/*.log 2>/dev/null || tail -n 30 server.log
          echo "ID=$ID registrado_no_hbbs=$OK"
          test -n "$ID" && test "$OK" = 1
"""

cab = re.sub(r"^name: .*$", "name: FappZap Acesso (Linux)", cab, count=1, flags=re.M)
cab = re.sub(r"(?ms)^on:\n.*?(?=^# NOTE|^env:)", """on:
  workflow_dispatch:
    inputs:
      tag:
        description: "Tag do release onde o .deb entra (ex.: acesso-1.5.0-linux-1)"
        required: true
        type: string
  push:
    tags:
      - "acesso-*-linux-*"

permissions:
  contents: write

""", cab, count=1)
cab = cab.replace("${{ inputs.upload-tag }}", "${{ inputs.tag || github.ref_name }}")
cab = cab.replace('UPLOAD_ARTIFACT: "${{ inputs.upload-artifact }}"', 'UPLOAD_ARTIFACT: "true"')
exigir("inputs.upload-tag" not in cab and "TAG_NAME" in cab, "cabeçalho mudou")

saida = ("# GERADO por fappzap/montar-workflow-linux.py a partir do flutter-build.yml — não editar à mão.\n"
         + cab + "\njobs:\n" + "".join(jobs[j] for j in JOBS) + "\n" + TESTE)
saida = saida.replace("${{ !inputs.upload-artifact && ", "${{ false && ")
saida = saida.replace("${{ inputs.upload-artifact }}", "true")
exigir("inputs.upload-artifact" not in saida, "sobrou inputs.upload-artifact")
DESTINO.write_text(saida, encoding="utf-8")
print(f"montar-workflow-linux: {DESTINO.relative_to(RAIZ)} ({len(saida.splitlines())} linhas)")
