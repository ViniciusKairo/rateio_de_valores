Sistema de Custos e Rateio por PA
Visão Geral

O Sistema de Custos e Rateio por PA é uma aplicação desktop desenvolvida em Python com interface gráfica moderna utilizando CustomTkinter, projetada para automatizar o processamento de arquivos Excel, consolidar custos operacionais por serviço, calcular rateios centralizados e gerar relatórios finais em PDF.

O sistema foi criado para reduzir erros manuais, padronizar análises financeiras e otimizar a distribuição de custos entre PAs (Postos de Atendimento / Unidades), com base em volume operacional e regras de rateio específicas.

Objetivo Principal

Automatizar o processo de:

Importação de múltiplos arquivos Excel
Identificação e normalização de serviços
Leitura e padronização de PAs
Cadastro e histórico de preços por serviço
Cálculo de custo direto por unidade
Rateio centralizado do PA 5014_0
Distribuição proporcional por volume
Consolidação final por PA
Exportação de relatório em PDF
Principais Funcionalidades
Importação Inteligente de Arquivos Excel
Permite importar múltiplos arquivos .xlsx e .xls
Identifica automaticamente:
Nome do serviço
Quantidade por PA
Origem do arquivo
Processa lotes completos
Normalização de Dados
Corrige padrões inconsistentes de nomenclatura de PA
Padroniza formatos como:
Cooperativa e PA: XXXX_X
Banco de Dados SQLite Integrado

Armazena automaticamente o valor unitário de cada serviço para reutilização futura.

Tabela:
precos (
    servico TEXT PRIMARY KEY,
    valor REAL
)
Cálculo de Rateio Automatizado
Regra:

O custo do PA 5014_0 é tratado como centro de custo e redistribuído proporcionalmente entre os demais PAs com base no volume (Qtd).

Fórmula:
% Rateio = Qtd do PA / Total de volumes
Valor Rateio = % Rateio × Valor total PA 5014_0
Custo Final = Custo Direto + Rateio
Interface do Sistema
Sidebar:
Importar arquivos
Calcular rateio
Exportar PDF
Limpar lote
Encerrar sistema
Painel Principal:
Aba Valores do Lote
Serviços encontrados
Histórico de preços
Validação visual:
Verde = válido
Laranja = negativo
Vermelho = inválido
Aba Resultados
Resumo consolidado
Tabela por PA
Custos:
Direto
Rateio
Final
Aba Log
Histórico detalhado da execução
Erros de importação
Ajustes automáticos
Tecnologias Utilizadas
Linguagem:
Python 3.x
Bibliotecas:
customtkinter
pandas
sqlite3
fpdf
tkinter
os
re
Estrutura Base do Projeto
SistemaRateio/
│
├── app_desktop.py
├── config_precos.db
├── README.md
└── arquivos_excel/
Instalação
Clone o projeto:
git clone https://github.com/seuusuario/seurepositorio.git
Instale as dependências:
pip install customtkinter pandas openpyxl fpdf
Como Executar
python app_desktop.py
Estrutura Esperada dos Arquivos Excel
O sistema considera:
Linha 6: Nome do serviço
Coluna B (a partir da linha 10): Descrição dos PAs
Geração de PDF

O relatório exportado contém:

Quantidade de arquivos processados
Serviços considerados
Rateio total
Volumes totais
Custos por PA
Total consolidado
Marca d’água de confidencialidade
Segurança e Controle
Recursos:
Histórico persistente de preços
Validação de entradas
Controle de erros por lote
Logs operacionais
Banco local
Benefícios Estratégicos
Antes:
Processo manual
Alto risco de erro
Rateio demorado
Inconsistência de padrão
Depois:
Automação
Padronização
Escalabilidade
Auditoria
Rapidez operacional
Melhorias Futuras
Exportação para Excel
Dashboard com gráficos
Login por usuário
Controle de permissões
Banco em nuvem
Integração com Power BI
Tema corporativo personalizado
Público-Alvo
Analistas financeiros
Controladoria
Operações administrativas
Gestão de custos
Cooperativas e unidades multi-PA
Observações Técnicas
Requisitos:
Python 3.10+
Windows recomendado
Excel estruturado corretamente
Autor

Vinícius Kairo
Desenvolvedor em transição para Engenharia de Software
Foco em automação, análise de dados e soluções empresariais

Licença

Uso interno / confidencial
Projeto desenvolvido para fins operacionais e de produtividade.
