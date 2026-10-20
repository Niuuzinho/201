#!/usr/bin/env python3
"""Gera www/index.html a partir de conteudo/material.md e ferramentas/template.html.

Uso: python3 ferramentas/build.py  (precisa do pacote markdown: pip install markdown)
"""
import glob, json, re, html as htmlmod
import markdown

import os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, 'conteudo', 'material.md')
TEMPLATE = os.path.join(RAIZ, 'ferramentas', 'template.html')
OUT = os.path.join(RAIZ, 'www', 'index.html')

text = open(SRC, encoding='utf-8').read()
lines = text.split('\n')

MATERIAS = [
    # id, nome, bloco, como achar no markdown (h2 ou h3), lead
    ('portugues', 'Língua Portuguesa', 'Comum', ('h2', 'Língua Portuguesa'), None),
    ('informatica', 'Noções de Informática', 'Comum', ('h2', 'Noções de Informática'), None),
    ('adm-publica', 'Administração Pública', 'Comum', ('h2', 'Administração Pública'), None),
    ('direito-adm', 'Direito Administrativo e Licitações', 'Específico', ('h2', 'Específicos: Direito Administrativo e Licitações'), None),
    ('administracao', 'Noções de Administração', 'Específico', ('h3', 'Noções de Administração'),
     'Estruturas, PODC, processos, qualidade e projetos. Decore as classificações: são as mais cobradas.'),
    ('gestao-pessoas', 'Gestão de Pessoas', 'Específico', ('h3', 'Noções de Gestão de Pessoas'),
     'Processos de gestão de pessoas e teorias de motivação e liderança. Teorias com nome de autor caem muito.'),
    ('materiais', 'Recursos Materiais', 'Específico', ('h3', 'Noções de Recursos Materiais'),
     'Classificação, estoques, compras e armazenagem. Curva ABC e ponto de pedido são clássicos de prova.'),
    ('arquivologia', 'Arquivologia', 'Específico', ('h3', 'Noções de Arquivologia'),
     'A teoria das três idades e a tabela de temporalidade são o coração da matéria.'),
    ('atendimento', 'Atendimento ao Público', 'Específico', ('h3', 'Noções de Atendimento ao Público'),
     'Mais intuitivo, mas a banca cobra o significado exato de cada atributo.'),
]


def md(s):
    out = markdown.markdown(s, extensions=['tables', 'sane_lists'])
    out = re.sub(r'<table>', '<div class="tbl"><table>', out)
    out = re.sub(r'</table>', '</table></div>', out)
    out = re.sub(r'<a href="(http[^"]+)"', r'<a target="_blank" rel="noopener" href="\1"', out)
    # caixas de destaque: > **Macete:** ... vira <blockquote class="tip">
    for rotulo, cls in (('Macete', 'tip'), ('Cai em prova', 'exam'), ('Atenção', 'warn'), ('Exemplo', '')):
        out = re.sub(r'<blockquote>(\s*<p><strong>' + re.escape(rotulo) + r')', r'<blockquote class="' + cls + r'">\1', out)
    return out


def plain(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', htmlmod.unescape(s)).strip()


def block_between(start, stop_pred):
    out = []
    i = start
    while i < len(lines) and not stop_pred(lines[i]):
        out.append(lines[i]); i += 1
    return out


def find(prefix):
    for i, l in enumerate(lines):
        if l.strip() == prefix:
            return i
    raise SystemExit('não achei ' + prefix)


def topic(num, title, body_md):
    h = md(body_md.strip())
    return {'num': num, 'title': title.strip().rstrip('.'), 'html': h, 'text': plain(h)}


data = []
for mid, nome, bloco, (kind, head), lead in MATERIAS:
    topics = []
    if kind == 'h2':
        i = find('## ' + head)
        body = block_between(i + 1, lambda l: l.startswith('## '))
        # lead = texto antes do primeiro ###
        lead_lines, cur, cur_lines = [], None, []
        for l in body:
            m = re.match(r'^### (\d+)\. (.*)$', l)
            if m:
                if cur: topics.append(topic(cur[0], cur[1], '\n'.join(cur_lines)))
                cur, cur_lines = (m.group(1), m.group(2)), []
            elif cur is None:
                lead_lines.append(l)
            else:
                cur_lines.append(l)
        if cur: topics.append(topic(cur[0], cur[1], '\n'.join(cur_lines)))
        lead = ' '.join(x.strip() for x in lead_lines if x.strip())
    else:
        i = find('### ' + head)
        body = block_between(i + 1, lambda l: l.startswith('## ') or l.startswith('### '))
        cur, cur_lines = None, []
        for l in body:
            m = re.match(r'^\*\*([\d][\d\- e]*)\. ([^*]+)\*\*(.*)$', l)
            if m:
                if cur: topics.append(topic(cur[0], cur[1], '\n'.join(cur_lines)))
                cur = (m.group(1), m.group(2))
                rest = m.group(3).strip()
                cur_lines = [rest] if rest else []
            elif cur is not None:
                cur_lines.append(l)
        if cur: topics.append(topic(cur[0], cur[1], '\n'.join(cur_lines)))
    data.append({'id': mid, 'nome': nome, 'bloco': bloco, 'lead': lead, 'topics': topics})

QUIZ = {
 'portugues': [
  ('Em "___ muitas pessoas na fila", qual forma está de acordo com a norma culta?', ['Haviam', 'Havia', 'Houveram', 'Haverão'], 1,
   'No sentido de existir, "haver" é impessoal e fica sempre no singular.'),
  ('Em qual frase a crase está correta?', ['Fui à pé até o prédio.', 'Refiro-me à você.', 'A reunião começa às 14h.', 'Ele começou à chover.'], 2,
   'Há crase na indicação de horas. Não há antes de masculino, de pronome pessoal nem de verbo.'),
  ('Em "Embora estivesse cansado, terminou o relatório", a conjunção "embora" expressa:', ['Causa', 'Concessão', 'Conclusão', 'Condição'], 1,
   'Embora, ainda que e mesmo que são conjunções concessivas.'),
  ('Na Redação Oficial, o fecho para autoridade de hierarquia superior é:', ['Atenciosamente', 'Cordialmente', 'Respeitosamente', 'Saudações'], 2,
   '"Respeitosamente" para superiores; "Atenciosamente" para mesma hierarquia ou inferior.'),
  ('O pronome de tratamento usado para reitores de universidade é:', ['Vossa Excelência', 'Vossa Senhoria', 'Vossa Magnificência', 'Vossa Eminência'], 2,
   'Reitores recebem "Vossa Magnificência", com o vocativo "Magnífico Reitor".'),
 ],
 'informatica': [
  ('O campo "Cco" de um e-mail serve para:', ['Enviar cópia que todos os destinatários veem', 'Enviar cópia oculta', 'Encaminhar com anexos', 'Confirmar leitura'], 1,
   'Cco é cópia oculta: os outros destinatários não veem quem está nesse campo.'),
  ('No Excel, o que acontece com a referência $A$1 ao copiar a fórmula para outra célula?', ['Muda a coluna', 'Muda a linha', 'Não muda', 'Vira #REF!'], 2,
   'O cifrão trava coluna e linha. $A$1 é referência absoluta.'),
  ('Qual praga se espalha sozinha pela rede, sem precisar ser executada pelo usuário?', ['Vírus', 'Worm', 'Cavalo de Troia', 'Adware'], 1,
   'O worm se propaga sozinho. O vírus precisa que o arquivo infectado seja executado.'),
  ('O backup incremental copia:', ['Todos os arquivos', 'O que mudou desde o último backup completo', 'O que mudou desde o último backup de qualquer tipo', 'Só arquivos do sistema'], 2,
   'Incremental: desde o último backup de qualquer tipo. Diferencial: desde o último completo.'),
  ('O atalho Win+L no Windows:', ['Abre o Explorador de Arquivos', 'Bloqueia o computador', 'Mostra a área de trabalho', 'Abre o Gerenciador de Tarefas'], 1,
   'Win+L bloqueia a tela. Win+E abre o Explorador e Win+D mostra a área de trabalho.'),
 ],
 'adm-publica': [
  ('A validade de um concurso público, segundo a CF/88, é de:', ['Até 1 ano, improrrogável', 'Até 2 anos, prorrogável uma vez por igual período', 'Até 4 anos', 'Até 2 anos, prorrogável duas vezes'], 1,
   'CF, art. 37, III: até 2 anos, prorrogável uma vez por igual período.'),
  ('O servidor nomeado por concurso adquire estabilidade após:', ['2 anos de exercício', '3 anos de efetivo exercício e avaliação especial de desempenho', '5 anos de exercício', 'A posse'], 1,
   'CF, art. 41: 3 anos de efetivo exercício, com avaliação especial de desempenho.'),
  ('Pela Lei 8.112, o prazo para a posse é de:', ['15 dias da posse', '30 dias da publicação do ato de nomeação', '60 dias da homologação', '10 dias da nomeação'], 1,
   'Posse em até 30 dias da publicação da nomeação; exercício em até 15 dias da posse.'),
  ('Pela LAI, o órgão deve responder ao pedido de informação em até:', ['10 dias', '20 dias, prorrogáveis por mais 10', '30 dias, prorrogáveis por mais 30', '5 dias úteis'], 1,
   'Resposta imediata ou em até 20 dias, prorrogáveis por mais 10, com justificativa.'),
  ('Depois da reforma de 2021, a improbidade administrativa exige:', ['Culpa ou dolo', 'Apenas culpa grave', 'Dolo', 'Prejuízo acima de 100 salários'], 2,
   'A Lei 14.230/2021 passou a exigir dolo em todas as modalidades de improbidade.'),
  ('Pela Lei 9.784, NÃO pode ser objeto de delegação:', ['Assinatura de ofícios', 'Decisão de recursos administrativos', 'Instrução de processos', 'Atendimento ao público'], 1,
   'Não se delegam: atos normativos, decisão de recursos e matérias de competência exclusiva.'),
 ],
 'direito-adm': [
  ('A UFBA, quanto à natureza jurídica, é:', ['Empresa pública', 'Órgão da administração direta', 'Autarquia federal', 'Sociedade de economia mista'], 2,
   'Universidades federais como a UFBA são autarquias: pessoas jurídicas de direito público criadas por lei.'),
  ('O agente age dentro da sua competência, mas para atingir um fim diferente do previsto em lei. Isso é:', ['Excesso de poder', 'Desvio de finalidade', 'Poder discricionário', 'Autotutela'], 1,
   'Desvio de finalidade: competência certa, fim errado. Excesso: agir além da competência.'),
  ('Qual modalidade de licitação NÃO existe mais na Lei 14.133?', ['Pregão', 'Diálogo competitivo', 'Tomada de preços', 'Leilão'], 2,
   'Tomada de preços e convite foram extintos. É vedado criar novas modalidades.'),
  ('No pregão, o critério de julgamento é:', ['Melhor técnica', 'Menor preço ou maior desconto', 'Maior lance', 'Técnica e preço'], 1,
   'O pregão serve para bens e serviços comuns e julga por menor preço ou maior desconto.'),
  ('A responsabilidade civil do Estado por danos causados por seus agentes é, em regra:', ['Subjetiva', 'Objetiva', 'Inexistente', 'Só criminal'], 1,
   'É objetiva (risco administrativo). O Estado depois cobra do agente se houve dolo ou culpa.'),
 ],
 'administracao': [
  ('No ciclo PDCA, a letra C corresponde a:', ['Controlar', 'Corrigir', 'Verificar (Check)', 'Comunicar'], 2,
   'Plan, Do, Check, Act: planejar, executar, verificar e agir corretivamente.'),
  ('A estrutura organizacional com dupla subordinação (chefe da função e chefe do projeto) é a:', ['Linear', 'Matricial', 'Linha-staff', 'Em rede'], 1,
   'Na matricial, o funcionário responde à área funcional e ao projeto ao mesmo tempo.'),
  ('O planejamento tático é feito:', ['Pela cúpula, a longo prazo', 'Pela gerência, a médio prazo', 'Pela execução, a curto prazo', 'Por consultores externos'], 1,
   'Estratégico: cúpula, longo prazo. Tático: gerência, médio prazo. Operacional: execução, curto prazo.'),
  ('A ferramenta 5W2H serve principalmente para:', ['Mapear causas de um problema', 'Montar um plano de ação', 'Priorizar problemas pelo 80/20', 'Organizar o ambiente de trabalho'], 1,
   '5W2H detalha o que, por que, onde, quando, quem, como e quanto custa: é um plano de ação.'),
 ],
 'gestao-pessoas': [
  ('Para Herzberg, o salário é um fator:', ['Motivacional', 'Higiênico', 'De autorrealização', 'De afiliação'], 1,
   'Fatores higiênicos (salário, ambiente) só evitam insatisfação. Os motivacionais geram satisfação.'),
  ('A Teoria Y de McGregor parte do pressuposto de que as pessoas:', ['Evitam o trabalho', 'Precisam de controle rígido', 'Se motivam e assumem responsabilidade', 'Só trabalham por dinheiro'], 2,
   'Teoria X: pessoas evitam trabalho. Teoria Y: pessoas se motivam e buscam responsabilidade.'),
  ('Recrutamento e seleção pertencem a qual processo de gestão de pessoas?', ['Agregar', 'Aplicar', 'Manter', 'Monitorar'], 0,
   'Agregar = trazer pessoas para a organização (recrutar e selecionar).'),
  ('Na liderança situacional, o estilo do líder varia conforme:', ['O tamanho da equipe', 'A maturidade do liderado', 'O orçamento', 'O cargo do líder'], 1,
   'Hersey-Blanchard: determinar, persuadir, compartilhar ou delegar, conforme a maturidade.'),
 ],
 'materiais': [
  ('Na curva ABC, os itens da classe A são:', ['Muitos itens de pouco valor', 'Poucos itens que concentram a maior parte do valor', 'Itens sem substituto', 'Itens perecíveis'], 1,
   'Classe A: cerca de 20% dos itens e 80% do valor. Classe C: muitos itens de pouco valor.'),
  ('O ponto de pedido é calculado por:', ['Estoque máximo − estoque mínimo', 'Consumo médio × tempo de reposição + estoque mínimo', 'Consumo ÷ estoque médio', 'Estoque mínimo × 2'], 1,
   'Quando o estoque cai a esse nível, faz-se o pedido de compra.'),
  ('PEPS significa:', ['Primeiro que entra, primeiro que sai', 'Primeiro que entra, por último que sai', 'Preço de estoque por saída', 'Pedido emergencial por solicitação'], 0,
   'PEPS: o material mais antigo sai primeiro. UEPS: o último que entra sai primeiro.'),
  ('No recebimento definitivo de material, verifica-se:', ['Apenas a quantidade', 'Qualidade e especificação, com o aceite', 'Somente a nota fiscal', 'O preço de mercado'], 1,
   'Provisório: quantidade e aspecto. Definitivo: qualidade, especificação e aceite.'),
 ],
 'arquivologia': [
  ('A passagem de documentos para o arquivo permanente chama-se:', ['Transferência', 'Recolhimento', 'Eliminação', 'Arranjo'], 1,
   'Transferência: corrente para intermediário. Recolhimento: para o permanente.'),
  ('O instrumento que define prazos de guarda e destinação dos documentos é:', ['Plano de classificação', 'Tabela de Temporalidade e Destinação (TTD)', 'Inventário', 'Protocolo'], 1,
   'A TTD resulta da avaliação e registra prazos de guarda e destinação final.'),
  ('Documentos de valor permanente:', ['Podem ser eliminados após microfilmagem', 'Nunca são eliminados', 'Ficam no arquivo corrente', 'São eliminados após 5 anos'], 1,
   'Permanentes são guardados para sempre, inclusive depois de microfilmados.'),
  ('O valor secundário de um documento é:', ['Administrativo', 'Fiscal', 'Histórico e informativo', 'Legal'], 2,
   'Primário interessa a quem produziu; secundário interessa à sociedade (histórico).'),
  ('O método alfabético de arquivamento é:', ['Indireto', 'Direto', 'Numérico', 'Cronológico'], 1,
   'Alfabético e geográfico são diretos: dispensam índice para a busca.'),
 ],
 'atendimento': [
  ('No atendimento, "discrição" significa:', ['Rapidez', 'Sigilo e reserva sobre o que se ouve', 'Ir direto ao ponto', 'Paciência com o cidadão'], 1,
   'Discrição é reserva. Rapidez é presteza; ir direto ao ponto é objetividade.'),
  ('Empatia é:', ['Ter afinidade com alguém', 'Colocar-se no lugar do outro', 'Concordar com o cidadão', 'Falar sem jargões'], 1,
   'Empatia é se colocar no lugar do outro. Simpatia é afinidade.'),
  ('Na comunicação, "ruído" é:', ['O canal usado', 'Tudo que atrapalha a mensagem', 'A resposta do receptor', 'O código da mensagem'], 1,
   'Ruído é qualquer interferência: barulho, jargão, distração, emoções.'),
  ('Pela Lei 10.048/2000, idosos têm atendimento prioritário a partir de:', ['55 anos', '60 anos', '65 anos', '70 anos'], 1,
   'Idosos com 60 anos ou mais estão entre os públicos com atendimento prioritário.'),
 ],
}

for m in data:
    m['quiz'] = [{'q': q, 'opts': o, 'a': a, 'exp': e} for q, o, a, e in QUIZ[m['id']]]

total = sum(len(m['topics']) for m in data)
print('total', total)

page = open(TEMPLATE, encoding='utf-8').read()
payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
page = page.replace('/*__DATA__*/null', payload)
cabeca, corpo = page.split('<div class="app">', 1)
page = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
        '<script src="config.js"></script>\n<script src="version.js"></script>\n'
        + cabeca + '</head>\n<body>\n<div class="app">' + corpo + '\n</body>\n</html>\n')
open(OUT, 'w', encoding='utf-8').write(page)
print('ok', len(page))
