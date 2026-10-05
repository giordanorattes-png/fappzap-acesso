# FappZap Acesso na Microsoft Store — roteiro de envio

> **O que a Store entrega e o que NÃO entrega.** Dentro de um pacote da Store o Windows não deixa um serviço
> abrir o programa na sessão do usuário (erro 575, verificado em 04/10/2026 com 3 variações). Por isso a versão da
> Store **não tem serviço**: serve para **atendimento com o cliente presente** (ele abre o programa, passa o ID e a
> senha/aceita a conexão). O **acesso sem supervisão** continua sendo o instalador `.msi`. A Store dá assinatura e
> confiança da Microsoft (sem o aviso do SmartScreen nem o bloqueio do Smart App Control).

## 0. O que já está pronto

- Variante `loja` no repositório (`fappzap/msix/AppxManifest.loja.xml` + `FAPPZAP_VARIANTE=loja` no `aplicar-marca.py`):
  sem serviço, sem capacidades restritas de serviço (`packagedServices`/`localSystemServices`), sem o botão **Instalar**
  (instalar copiaria o programa para fora do pacote). Ficam só `internetClient` e `runFullTrust`.
- O pacote sai do GitHub Actions: **Actions → FappZap Acesso (Windows e Android) → Run workflow** com
  `variante = loja`, uma **tag nova** (ex.: `acesso-1.5.0-loja-1`) e `revisao`. O `.msix` aparece no release da tag
  como `fappzap-acesso-<versão>-loja-x64.msix` (sem assinatura: a Microsoft assina). O MSI/.exe dessa tag são da variante
  da loja e **não** devem ser distribuídos.
- A versão do pacote é `1.5.<revisao>.0` (a Store exige o último número 0 e versão maior a cada envio: **suba a revisão**
  em cada reenvio).

## 1. No Partner Center (só você: a conta é sua)

1. **Apps e jogos → Novo produto → App MSIX ou PWA** → reserve o nome **FappZap Acesso**.
2. Em **Gerenciamento do produto → Identidade do produto**, copie três valores:
   - `Package/Identity/Name` (o padrão que usei é `FappSolutions.FappZapAcesso` — confirme)
   - `Package/Identity/Publisher` (o padrão é `CN=997374EF-248E-4CB5-BE11-B0218CDA905C`, o mesmo do FappZap Suporte)
   - `Package/Properties/PublisherDisplayName` (já é "Fapp Solutions")
3. Se o **Name** ou o **Publisher** forem diferentes dos padrões, rode o workflow informando `identidade` e `publisher`.
   **O pacote só é aceito se esses valores baterem exatamente.**

## 2. Envio

- **Preço:** gratuito. **Mercados:** os mesmos do FappZap Suporte.
- **Categoria sugerida:** Utilitários e ferramentas (ou Negócios). **Classificação etária:** responda o questionário:
  sem violência, sem conteúdo adulto, sem compras; o app permite **comunicação entre usuários** (acesso remoto) — responda
  que sim, sem conteúdo gerado por usuário compartilhado publicamente.
- **Pacotes:** envie o `.msix` (Envios → Pacotes). Sistema mínimo: Windows 10 1903 (10.0.18362), só x64.
- **Política de privacidade (URL):** a mesma do FappZap Suporte. A Privacidade 1.26+ do FappZap descreve o FappZap
  Acesso (nome da máquina, ID, senha criada pelo programa, endereço de rede, o que a equipe vê, como desinstalar).
- **Contato de suporte:** contato@fappsolutions.com. **Site:** https://fappsolutions.com
- **Capturas de tela:** pelo menos 1 em 1366×768 ou maior (PNG). Sugestão: a tela inicial com o ID e a senha; o aviso de
  conexão; o ícone da bandeja. Gere pela Sandbox (script de teste da variante da loja).

## 3. Textos da ficha

### Português (Brasil)
**Nome:** FappZap Acesso
**Descrição curta:** Acesso remoto da Fapp Solutions: o suporte entra no seu computador só com a sua permissão.
**Descrição:**
O FappZap Acesso é o programa de acesso remoto da Fapp Solutions. Quando você precisa de ajuda, abra o programa, passe o
número de ID para o atendente e aceite a conexão. Enquanto alguém está conectado, o programa mostra um aviso e você pode
desconectar a qualquer momento.

• Atendimento com você presente: você vê tudo o que o suporte faz.
• Aviso na tela quando alguém se conecta e botão para encerrar.
• Conexão pelo servidor da própria Fapp Solutions.
• Baseado no RustDesk, software livre (AGPL-3.0). O código-fonte está publicado.

**Novidades:** Primeira versão na Microsoft Store.

### English (United States)
**Name:** FappZap Acesso
**Short description:** Remote access from Fapp Solutions: support only enters your computer with your permission.
**Description:**
FappZap Acesso is Fapp Solutions' remote access program. When you need help, open the program, give the ID number to the
support agent and accept the connection. While someone is connected the program shows a notice and you can disconnect at
any time.

• Attended support: you see everything the agent does.
• On-screen notice when someone connects, with a button to end the session.
• Connection through Fapp Solutions' own server.
• Based on RustDesk, free software (AGPL-3.0). The source code is published.

**What's new:** First release on the Microsoft Store.

### Español (España)
**Nombre:** FappZap Acesso
**Descripción corta:** Acceso remoto de Fapp Solutions: el soporte solo entra en su equipo con su permiso.
**Descripción:**
FappZap Acesso es el programa de acceso remoto de Fapp Solutions. Cuando necesite ayuda, abra el programa, dé el número de
ID al agente y acepte la conexión. Mientras alguien está conectado, el programa muestra un aviso y usted puede desconectar
en cualquier momento.

• Atención con usted presente: usted ve todo lo que hace el soporte.
• Aviso en pantalla cuando alguien se conecta y botón para terminar.
• Conexión por el servidor propio de Fapp Solutions.
• Basado en RustDesk, software libre (AGPL-3.0). El código fuente está publicado.

**Novedades:** Primera versión en Microsoft Store.

## 4. Notas para a certificação (cole em inglês, em "Notas para certificação")

> FappZap Acesso is a branded build of the open-source RustDesk remote desktop client (AGPL-3.0, source:
> https://github.com/giordanorattes-png/fappzap-acesso). It is a remote support tool used with the customer present.
>
> - **Consent and transparency:** the person being accessed starts the app, shares the ID, sees a notice while a
>   connection is active and can disconnect at any time. A tray icon is shown while the app runs. Nothing is installed
>   outside the package and no Windows service is registered in this Store version (the "Install" button is removed).
> - **Restricted capability `runFullTrust`:** the app is a full desktop (Win32/Flutter) application packaged for the Store;
>   it needs to run as a normal desktop process to capture the screen and inject input for the remote session.
> - **Network:** it only connects to our own rendezvous/relay server (acesso.fappsolutions.com) and to the peer.
> - **How to test:** install the package on two Windows PCs, open the app on both, enter the ID shown on one into the other
>   and press Connect; accept the incoming connection on the first PC. The default server and key are built in.
> - **Account:** none required.

## 5. Depois de aprovado

- Atualize o link de download no FappZap Suporte, em Downloads e na ficha de acesso remoto (a loja entra ao lado do
  MSI). O MSI continua sendo o caminho do **acesso sem supervisão**.
- Cada versão nova do RustDesk: rebasear o branch `fappzap`, rodar `montar-workflow.py`, compilar de novo com
  `variante = loja` e **revisão maior**, enviar o novo `.msix`.
