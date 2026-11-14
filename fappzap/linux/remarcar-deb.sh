#!/usr/bin/env bash
# Passa o .deb que o build.py do RustDesk gera (pacote "rustdesk") para o FappZap Acesso.
#
# Por que não basta o APP_NAME: no Linux o RustDesk usa get_app_name().to_lowercase() — "fappzap-acesso" —
# como nome do serviço systemd (systemctl enable/stop fappzap-acesso) e para achar os próprios processos
# (ps/pkill "fappzap-acesso --server", "--tray"). Com o executável e o serviço ainda chamados "rustdesk",
# o serviço nunca reiniciaria o --server da sessão do usuário. Então o executável, a pasta, o serviço, os
# atalhos e o esquema de link (fappzap-acesso://) passam todos a ter esse nome. O pacote vira
# "fappzap-acesso" e convive com o RustDesk oficial (arquivos, serviço e configuração separados).
#
# Uso: remarcar-deb.sh <rustdesk-X.deb> <saida.deb>
set -euo pipefail
ENTRADA="$1"
SAIDA="$2"
A=fappzap-acesso
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
P="$T/p"
dpkg-deb -R "$ENTRADA" "$P"

exige() { [ -e "$1" ] || { echo "remarcar-deb: $1 sumiu (o build.py do RustDesk mudou; revisar)" >&2; exit 1; }; }
for f in usr/share/rustdesk/rustdesk usr/share/rustdesk/files/systemd/rustdesk.service \
         usr/share/applications/rustdesk.desktop usr/share/applications/rustdesk-link.desktop \
         usr/share/icons/hicolor/256x256/apps/rustdesk.png usr/share/icons/hicolor/scalable/apps/rustdesk.svg \
         DEBIAN/control DEBIAN/postinst DEBIAN/prerm DEBIAN/postrm DEBIAN/preinst; do
  exige "$P/$f"
done

mv "$P/usr/share/rustdesk" "$P/usr/share/$A"
mv "$P/usr/share/$A/rustdesk" "$P/usr/share/$A/$A"
mv "$P/usr/share/$A/files/systemd/rustdesk.service" "$P/usr/share/$A/files/systemd/$A.service"
mv "$P/usr/share/applications/rustdesk.desktop" "$P/usr/share/applications/$A.desktop"
mv "$P/usr/share/applications/rustdesk-link.desktop" "$P/usr/share/applications/$A-link.desktop"
mv "$P/usr/share/icons/hicolor/256x256/apps/rustdesk.png" "$P/usr/share/icons/hicolor/256x256/apps/$A.png"
mv "$P/usr/share/icons/hicolor/scalable/apps/rustdesk.svg" "$P/usr/share/icons/hicolor/scalable/apps/$A.svg"

# Serviço, scripts do dpkg e atalhos: só nomes de arquivo, caminho e serviço — nenhum binário passa por aqui.
TEXTOS=("$P/usr/share/$A/files/systemd/$A.service" "$P"/DEBIAN/{preinst,postinst,prerm,postrm}
        "$P/usr/share/applications/$A.desktop" "$P/usr/share/applications/$A-link.desktop")
sed -i -e "s/rustdesk/$A/g" -e 's/RustDesk/FappZap Acesso/g' "${TEXTOS[@]}"
grep -q "ExecStart=/usr/bin/$A --service" "$P/usr/share/$A/files/systemd/$A.service" || { echo "remarcar-deb: serviço sem ExecStart esperado" >&2; exit 1; }
if grep -n -i "rustdesk" "${TEXTOS[@]}"; then echo "remarcar-deb: sobrou rustdesk nos textos acima" >&2; exit 1; fi

# control: pacote, quem mantém e descrição (as dependências ficam as do RustDesk).
sed -i -e "s/^Package: rustdesk$/Package: $A/" \
       -e 's/^Maintainer: .*/Maintainer: Fapp Solutions <suporte@fappsolutions.com>/' \
       -e 's|^Homepage: .*|Homepage: https://fappsolutions.com|' \
       -e 's/^Description: .*/Description: FappZap Acesso - acesso remoto do FappZap (baseado no RustDesk, AGPL-3.0)/' \
       "$P/DEBIAN/control"
grep -q "^Package: $A$" "$P/DEBIAN/control" || { echo "remarcar-deb: Package não trocou" >&2; exit 1; }

(cd "$P" && find . -type f ! -path './DEBIAN/*' -printf '%P\0' | sort -z | xargs -0 md5sum > DEBIAN/md5sums)
dpkg-deb --root-owner-group -Zxz -b "$P" "$SAIDA"
dpkg-deb -I "$SAIDA" | sed -n '/Package:/,/Description:/p'
echo "remarcar-deb: $SAIDA"
