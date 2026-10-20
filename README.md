# Caderno 201

App de estudos para o concurso da UFBA 2026, **Cargo 201 (Assistente em Administração)**: todo o conteúdo programático resumido por matéria, marcação do que já foi estudado, busca e teste rápido no fim de cada matéria.

## Instalar no celular (Android)

1. Abra a aba **Releases** deste repositório no celular.
2. Baixe o arquivo `Caderno201-vX.Y.Z.apk` da versão mais nova.
3. Abra o arquivo. Na primeira vez, o Android pede para permitir instalar apps desta fonte: permita e toque em **Instalar**.

Para atualizar, abra **Configurações** (engrenagem no topo) e toque em **Procurar atualização**. Se houver versão nova, toque em **Baixar e instalar**. O progresso continua.

Em **Configurações** você também escolhe o tema (claro, escuro, sépia, oceano, floresta, preto total, alto contraste ou automático), a cor de destaque, o tamanho e a fonte do texto, a data da prova, entra com o GitHub e guarda ou restaura uma cópia do progresso.

## Perfil e progresso

- Sem login, o progresso fica salvo só no aparelho.
- Com **Entrar com GitHub**, o app mostra um código. Você digita esse código em github.com/login/device e autoriza. O progresso passa a ficar num Gist secreto da sua conta (`caderno-201-progresso.json`) e sincroniza entre aparelhos. Não apague esse Gist.
- O app só pede permissão de **gist**. Ele não mexe nos seus repositórios.

### Configurar o login (uma vez só)

1. No GitHub: **Settings → Developer settings → OAuth Apps → New OAuth App**.
2. Nome: `Caderno 201`. Em *Homepage URL* e *Authorization callback URL*, use o link deste repositório.
3. Depois de criar, marque **Enable Device Flow** e salve.
4. Copie o **Client ID** e cole em `www/config.js`, no campo `clientId`.
5. Aumente o número em `versao.txt` para lançar uma versão nova (abaixo).

O Client ID é público. Não coloque o *Client secret* em nenhum arquivo.

## Lançar uma versão nova

O APK é gerado pelo GitHub Actions (`.github/workflows/apk.yml`):

1. Faça as mudanças que quiser.
2. Aumente o número em `versao.txt` (ex.: de `1.0.0` para `1.0.1`; sempre maior que o anterior) e envie para o GitHub.
3. Em alguns minutos aparece uma versão nova na aba **Releases**, com o APK anexado. O botão **Checar atualização** do app passa a oferecê-la.

Se o número não mudar, nada é publicado. Para gerar de novo uma versão que falhou, use **Actions → Gerar APK → Run workflow**.

## Editar o conteúdo

- O texto de estudo fica em `conteudo/material.md`.
- O visual e o funcionamento ficam em `ferramentas/template.html`. As questões dos testes ficam em `ferramentas/build.py`.
- Depois de editar, gere a página com `python3 ferramentas/build.py` (precisa de `pip install markdown`). Isso atualiza `www/index.html`.

## Estrutura

| Pasta/arquivo | O que é |
| --- | --- |
| `www/` | O app em si (página gerada, `config.js`, `version.js`) |
| `conteudo/` | Material de estudo em Markdown |
| `ferramentas/` | Gerador da página e dos ícones |
| `android-recursos/` | Ícones e chave de assinatura do APK |
| `capacitor.config.json`, `package.json` | Configuração do Capacitor, que transforma a página em app Android |

A chave em `android-recursos/assinatura.keystore` assina todas as versões do APK. Ela precisa ser sempre a mesma, senão o Android recusa a atualização por cima da versão instalada.
