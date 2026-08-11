# 📊 B3 Investment Screener

Ferramenta local para análise fundamentalista de ações e FIIs (Fundos Imobiliários) da B3, usando dados do [Fundamentus](https://fundamentus.com.br).

## 🎯 Funcionalidades

- **Duas classes de ativos**: Ações e Fundos Imobiliários (FIIs)
- **Filtros configuráveis**: Ajuste valores mínimos e máximos para cada métrica
- **Ranking automático**: Score composto baseado em valuation, qualidade e yield
- **Tooltips explicativos**: Cada métrica tem descrição de significado e relevância
- **Interface em português**: 100% PT-BR
- **Cache local**: Dados armazenados em SQLite, refresh manual
- **Rate limiting**: Máximo 1 atualização por hora (respeita o Fundamentus)

## 📋 Requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

## 🚀 Instalação e Uso

### Opção 1: Docker (Recomendado)

```bash
# Iniciar aplicação
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar aplicação
docker-compose down
```

Acesse: **http://localhost:8000**

**Vantagens:**
- Zero configuração de ambiente
- Isolado do sistema host
- Persistência de dados em `./data/`
- Restart automático

### Opção 2: Direto no host

**1. Instalar dependências**
```bash
pip install -r requirements.txt
```

**2. Iniciar servidor**
```bash
uvicorn app:app --reload
# ou
python app.py
# ou
./start.sh
```

**3. Acessar aplicação**

Abra o navegador em: **http://localhost:8000**

## 📖 Como Usar

### Primeira vez

1. Clique em **"Atualizar dados"** para fazer scraping do Fundamentus
2. Aguarde alguns segundos enquanto os dados são carregados
3. Os dados ficam em cache local (SQLite) — não precisa atualizar sempre

### Filtrando ações

1. Selecione a aba **"Ações"**
2. Ajuste os filtros (P/L, P/VP, ROIC, etc.)
3. Resultados são filtrados automaticamente (debounce de 300ms)
4. Clique nos cabeçalhos da tabela para ordenar

### Filtrando FIIs

1. Selecione a aba **"Fundos Imobiliários"**
2. Ajuste os filtros (Dividend Yield, P/VP, Vacância, etc.)
3. Resultados são filtrados automaticamente
4. Score composto considera yield, valuation e qualidade

### Score Composto

#### Ações (0-100)
- **Value (40%)**: Menor P/L, P/VP, EV/EBIT = melhor
- **Quality (40%)**: Maior ROIC, ROE = melhor
- **Yield (10%)**: Maior Div.Yield = melhor
- **Growth (10%)**: Maior Cresc.Rec.5a = melhor

#### FIIs (0-100)
- **Yield (50%)**: Maior Div.Yield, FFO Yield, Cap Rate = melhor
- **Valuation (30%)**: P/VP próximo de 1.0 = melhor
- **Quality (20%)**: Maior liquidez, menor vacância = melhor

## 🗂️ Estrutura do Projeto

```
invest/
├── app.py                     # FastAPI backend
├── requirements.txt           # Dependências Python
├── scrapers/
│   ├── fundamentus.py         # Scraper Fundamentus
│   └── utils.py               # Parsing utilities
├── models/
│   ├── database.py            # SQLite operations
│   └── schemas.py             # Pydantic models + scoring
├── static/
│   ├── style.css              # Estilos CSS
│   └── app.js                 # Alpine.js frontend
├── templates/
│   └── index.html             # Single-page UI
└── data/
    └── screener.db            # SQLite database (auto-criado)
```

## 🌐 Expor na Web

### Usando Docker com porta customizada

```bash
# Edite docker-compose.yml, altere ports para:
ports:
  - "80:8000"  # ou outra porta externa
```

### Nginx reverse proxy (produção)

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Segurança

Para exposição pública, considere:
- Adicionar autenticação básica (nginx auth_basic)
- HTTPS com Let's Encrypt
- Rate limiting no nginx
- Firewall rules

## 🔧 Configuração Avançada

### Alterar porta (sem Docker)

```bash
uvicorn app:app --reload --port 3000
```

### Docker com porta customizada

Edite `docker-compose.yml`:
```yaml
ports:
  - "3000:8000"  # host:container
```

### Desabilitar rate limiting

Edite `app.py`:
```python
MIN_REFRESH_INTERVAL = timedelta(seconds=0)
```

⚠️ **Aviso**: Scraping frequente pode resultar em bloqueio pelo Fundamentus.

## 🐛 Troubleshooting

### Erro ao fazer scraping

**Sintoma**: `Failed to fetch stocks data: 403 Forbidden`

**Solução**: Fundamentus pode ter bloqueado temporariamente. Aguarde algumas horas e tente novamente. Se persistir, verifique se o site mudou a estrutura HTML.

### Dados vazios após scraping

**Sintoma**: Scraping retorna `Successfully refreshed 0 stocks`

**Solução**: Estrutura HTML do Fundamentus provavelmente mudou. Verifique os seletores CSS em `scrapers/fundamentus.py`.

### Filtros não funcionam

**Sintoma**: Alterar filtro não muda resultados

**Solução**: Verifique console do navegador (F12). Pode ser erro JavaScript ou API retornando erro.

## 🛡️ Fontes Alternativas

Se o Fundamentus bloquear scraping ou mudar estrutura, considere:

- **Status Invest** (https://statusinvest.com.br) — tem versão pública e API não-oficial
- **Investidor10** (https://investidor10.com.br) — dados fundamentalistas alternativos
- **B3 oficial** — dados brutos (mais complexo de processar)

Para trocar fonte, edite `scrapers/fundamentus.py` e implemente novos scrapers.

## ⚠️ Aviso Legal

Esta ferramenta é **apenas para fins educacionais**. Não constitui recomendação de investimento. Sempre faça sua própria análise e consulte um profissional certificado antes de investir.

Os dados são obtidos de fontes públicas (Fundamentus) e podem conter erros ou estar desatualizados.

## 📝 Licença

Uso pessoal livre. Para uso comercial ou redistribuição, consulte o autor.

## 🤝 Contribuindo

Pull requests são bem-vindos. Para mudanças grandes, abra uma issue primeiro.

---

**Desenvolvido com FastAPI + Alpine.js + SQLite** 🚀
