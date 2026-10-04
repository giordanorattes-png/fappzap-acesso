# FappZap Acesso

Versão do [RustDesk](https://github.com/rustdesk/rustdesk) com a marca da Fapp Solutions,
apontada para o servidor `acesso.fappsolutions.com`. É o acesso sem supervisão usado pelo
suporte do FappZap. Licença: AGPL-3.0, a mesma do RustDesk; o código está todo aqui.

O que muda em relação ao RustDesk: nome, ícone, servidor, chave pública do servidor e o pacote
do Android (`com.fappsolutions.acesso`). Tudo que o RustDesk mostra a quem está sendo acessado
continua igual: o ícone na bandeja, o aviso de conexão, o botão de desconectar e o
"Powered by RustDesk".

## Como é montado

O branch `fappzap` é a tag oficial do RustDesk mais esta pasta. Nada do código do RustDesk é
editado no git: a marca entra na hora da compilação.

| arquivo | o que faz |
|---|---|
| `aplicar-marca.py` | troca nome, servidor, chave e pacote e copia os ícones de `marca/`. Para com erro se algum trecho esperado sumir numa versão nova. |
| `montar-workflow.py` | gera `.github/workflows/fappzap-acesso.yml` a partir do `flutter-build.yml` do RustDesk (só Windows x64 e Android). |
| `icone-acesso.svg` | o desenho do ícone. |
| `gerar-marca.mjs` + `gerar-ico.py` | geram `marca/` a partir do SVG (precisam do sharp e do Pillow). |

## Compilar

Actions → **FappZap Acesso (Windows e Android)** → Run workflow, com a tag do release (ex.:
`acesso-1.5.0-1`). Saem no release: o instalador `.msi`, o `.exe` portátil e os APKs.

O APK é assinado com a chave dos segredos `ANDROID_*` do repositório. A cópia da chave fica
fora do git; sem ela não dá para atualizar o app já instalado nos celulares.

## Versão nova do RustDesk

1. `git fetch upstream --tags` e `git rebase --onto <tag nova> <tag antiga> fappzap`.
2. `python fappzap/montar-workflow.py` e conferir o diff do workflow.
3. Rodar o workflow com uma tag nova. Se o `aplicar-marca.py` parar, ajustar o trecho que mudou.
