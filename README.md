<p align="center">
  <img alt="Logo Maia em Carneiro" src="assets/logo.png" width="350">
</p>

# Maia em Carneiro

Um pequenino projeto com um **worker em Python** que consulta a API Airlabs (schedules do aeroporto OPO), grava contagens no **Supabase** e um **dashboard local em Flask** para ver na hora o que está na base de dados sem ser preciso abrir o painel do Supabase.

---

## Neste repositório tens:

| Parte | O quê |
|--------|--------|
| `worker/` | Lógica Airlabs + Supabase + agendamento (duas vezes por dia por defeito). |
| `webapp/` | Dashboard Flask **só em localhost** com vista **mês a mês**, lista de dias, logo em `assets/logo.png`. |

A tabela no Supabase chama-se `flight_monthly_rollup` e usa `entry_type` `day` ou `month`, como já definiste.

### Estrutura do `webapp/`

```
webapp/
├── routes
│   ├── __init__.py
│   ├── dashboard.py
│   ├── media.py
│   └── repo_assets.py
├── services
│   ├── __init__.py
│   ├── month_options.py
│   ├── month_view.py
│   └── repository.py
├── static
│   └── css
│       ├── base
│       │   ├── reset.css
│       │   └── variables.css
│       ├── components
│       │   ├── alerts.css
│       │   ├── kpi.css
│       │   ├── search.css
│       │   └── table.css
│       ├── layout
│       │   ├── shell.css
│       │   └── toolbar.css
│       ├── utilities
│       │   └── code.css
│       └── dashboard.css
├── templates
│   ├── dashboard.html
│   └── error.html
├── __init__.py
├── app.py
└── config.py
```

---

## Variáveis de ambiente

Copia o `.env.example` para `.env` e preenche com os teus valores reais.

- **SUPABASE_URL** -> URL do projeto Supabase.  
- **SUPABASE_KEY** -> chave com permissão de escrita (em backend costuma ser a *service role*; nunca no frontend).  
- **AIRLABS_API_KEY** -> chave da conta Airlabs.  
- **AIRPORT_IATA** -> por defeito `OPO`.  
- **WORKER_TIMEZONE** -> por defeito `Europe/Lisbon` (o “hoje” do job segue este fuso).  
- **SCHEDULE_TIMES** -> horas em que o job corre, por defeito `12:00,23:50`.  
- **RUN_ON_START** -> se `true`, corre logo ao arrancar (útil no Railway para não esperar até à meia-noite).  
- **AIRLABS_LIMIT** -> limite por pedido à API (máximo permitido pelo plano Airlabs).

Para o dashboard local, bastam **SUPABASE_URL** e **SUPABASE_KEY** (os mesmos do worker).

Opcionais só para o Flask:

- **FLASK_PORT** -> por defeito `5000`.  
- **FLASK_DEBUG** -> `1` para modo debug (não uses em produção pública).

---

## Começar do zero na base de dados

Se tens registos antigos errados e queres **apagar tudo** e voltar a encher só a partir de hoje:

1. Na máquina local (com `.env` já configurado):

   ```bash
   python -m worker.main --reset-table --yes
   python -m worker.main --once
   ```

   O primeiro comando esvazia a tabela `flight_monthly_rollup`. O segundo pede dados ao Airlabs e grava o dia atual + recalcula o mês.

2. Alternativa no Supabase: no **SQL Editor**, podes executar `DELETE FROM public.flight_monthly_rollup;`, tens o mesmo efeito, desde que saibas que não há FKs noutras tabelas a apontar para estas linhas.

O `--reset-table` **não** corre sozinho, é preciso `--yes` para não apagares dados por engano.

---

## Instalação e testes locais

Recomenda-se um ambiente virtual.

**Windows (PowerShell), na pasta do projeto:**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Garante que existe `.env` (a partir de `.env.example`).

**Worker, uma execução:**

```powershell
python -m worker.main --once
```

**Worker, a correr em ciclo (agendado):**

```powershell
python -m worker.main
```

Para parar: `Ctrl+C`.

---

## Dashboard local (Flask)

Vista **mensal**: lista todos os dias do mês **até hoje** (no fuso `WORKER_TIMEZONE`), com voos por dia quando existir registo na BD. **Não há calendário com dias futuros**, assim evitando confusão e pedidos inválidos.

```powershell
python -m flask --app webapp.app run --host 127.0.0.1 --port 5000
```

Abre `http://127.0.0.1:5000`

- Navegação **‹ ›** entre meses; o mês futuro em relação a “hoje” é bloqueado no servidor.  
- Dropdown **Saltar para** com os últimos 48 meses (só até ao mês atual).  
- Parâmetro opcional: `?m=2026-05` (se for inválido ou futuro, volta ao mês atual com aviso).  
- Campo **Filtrar** filtra a tabela no browser (sem novo pedido ao servidor).  
- Logo: coloca o ficheiro em [`assets/logo.png`](assets/logo.png), aparece no topo.

Paleta: fundo escuro, azul profundo e verde escuro nos destaques.

**Importante:** não expor à internet. Usa `127.0.0.1` apenas em desenvolvimento.

---

## Railway

1. Novo serviço a partir deste repositório.  
2. **Start command:** `python -m worker.main`  
3. Copia as mesmas variáveis do `.env` para as **Variables** do Railway (URL Supabase, key, Airlabs, etc.).  
4. Faz deploy. O `requirements.txt` faz o Railway instalar as dependências automaticamente.

Se no primeiro deploy quiseres base limpa, podes correr **uma vez** localmente o `--reset-table --yes` antes de deixares o worker popular dados, ou usar o SQL no Supabase.

---

## Organização do código do worker

O ficheiro `worker/main.py` ficou só com o arranque e argumentos da linha de comandos. O resto reparte-se assim:

- `constants.py` -> nomes de tabela, URL Airlabs, texto por defeito das horas.  
- `settings.py` -> `Settings`, leitura do ambiente, logging.  
- `airlabs.py` -> pedidos HTTP e contagem de partidas + chegadas para o dia.  
- `db.py` -> cliente Supabase, upserts lógicos, limpeza de linhas com mais de dois meses, reset da tabela.  
- `jobs.py` -> um “passo” completo: contar → dia → mês → limpeza.  
- `scheduler.py` -> APScheduler com as duas janelas diárias.