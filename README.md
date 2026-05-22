# FIAP Secure Systems — Architecture Diagram Analyzer

> Hackathon Integrado IADT + SOAT — FIAP PosTech

Sistema back-end que recebe diagramas de arquitetura (imagem ou PDF), processa com IA e gera relatórios técnicos automáticos com componentes, riscos e recomendações.

📹 **Demonstração:** https://vimeo.com/1194863539?share=copy&fl=sv&fe=ci

📦 **Repositório:** https://github.com/acaoliveira/fiap-hackathon-architecture-analyzer

---

## Descrição do Problema

Empresas com sistemas distribuídos possuem dezenas de diagramas de arquitetura analisados manualmente, consumindo tempo especialista e não escalando. Este MVP automatiza essa análise usando IA multimodal (Claude) dentro de uma arquitetura de microsserviços.

---

## Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser / Cliente HTTP                      │
└───────────┬─────────────────────────────┬───────────────────────┘
            │ HTTP :3000                  │ REST :8000
            ▼                             ▼
┌───────────────────────┐     ┌───────────────────────┐
│      Frontend         │────▶│     API Gateway       │
│   (HTML/CSS/JS)       │     │  (BFF / Roteamento)   │
└───────────────────────┘     └───────┬───────┬───────┘
                            │       │ REST
                   REST     │       └────────────────────────┐
                            ▼                                ▼
               ┌────────────────────────┐     ┌─────────────────────────┐
               │   Upload & Orquestração│     │    Report Service       │
               │       Service          │     │                         │
               │  ┌──────────────────┐  │     │  ┌───────────────────┐  │
               │  │  PostgreSQL (DB1) │  │     │  │ PostgreSQL (DB2)  │  │
               │  └──────────────────┘  │     │  └───────────────────┘  │
               └───────────┬────────────┘     └─────────────────────────┘
                           │                               ▲
                           │ AMQP (async)                  │ REST
                           ▼                               │
                    ┌─────────────────┐                    │
                    │   RabbitMQ      │                    │
                    │  (Mensageria)   │                    │
                    └────────┬────────┘                    │
                             │ AMQP (async)                │
                             ▼                             │
               ┌─────────────────────────────┐            │
               │    Processing Service        ├────────────┘
               │  (Worker IA)                 │
               │  ┌────────────────────────┐  │
               │  │  Claude API (Anthropic) │  │
               │  │  + Guardrails          │  │
               │  └────────────────────────┘  │
               └─────────────────────────────┘
```

### Fluxo Principal

1. **Upload** → Cliente envia diagrama via `POST /api/v1/analyses`
2. **Orquestração** → Upload Service valida, persiste o arquivo e cria registro com status `RECEIVED`
3. **Mensageria (assíncrono)** → Upload Service publica evento `analyses.created` no RabbitMQ
4. **Processamento** → Processing Service consome o evento, chama a Claude API com a imagem/PDF
5. **Guardrails** → Validação de entrada e saída do modelo; sanitização dos campos
6. **Relatório** → Processing Service persiste o relatório via Report Service
7. **Status** → Status atualizado para `ANALYZED` (ou `ERROR`)
8. **Consulta** → Cliente consulta `GET /api/v1/analyses/{id}/report`

---

## Microsserviços

| Serviço | Porta | Responsabilidade | Banco |
|---------|-------|-----------------|-------|
| `frontend` | 3000 | Interface web — upload e visualização de relatórios | — |
| `api-gateway` | 8000 | BFF — roteamento e validação de entrada | — |
| `upload-service` | 8001 | Recebe arquivos, cria jobs, publica eventos | PostgreSQL `upload_db` |
| `processing-service` | — | Consome fila, analisa com IA, persiste resultado | — |
| `report-service` | 8003 | Armazena e serve relatórios técnicos | PostgreSQL `report_db` |

Cada serviço segue **Clean Architecture** (domain → application → infrastructure → interfaces).

---

## Inteligência Artificial

**Abordagem escolhida:** LLM multimodal (Claude) com prompt engineering e guardrails.

**Justificativa:** Claude suporta nativamente imagens e PDFs em uma única chamada, eliminando pipelines de OCR separados. A abordagem de prompt estruturado com saída JSON é mais confiável para relatórios técnicos do que detecção de objetos genérica.

**Pipeline de IA:**
```
Arquivo (imagem/PDF)
      │
      ▼
[Guardrail de entrada]
  - Verifica tipo MIME permitido
  - Verifica tamanho (máx 15 MB)
  - Verifica se arquivo existe e não está vazio
      │
      ▼
[Claude API — claude-sonnet-4-6]
  - System prompt com regras estritas de output
  - User: arquivo (base64) + prompt de análise
  - Saída esperada: JSON estruturado
      │
      ▼
[Guardrail de saída]
  - Valida JSON válido
  - Valida campos obrigatórios
  - Sanitiza tipos de componentes
  - Trunca campos longos (máx 400 chars)
  - Detecta resposta de erro do modelo
      │
      ▼
Relatório sanitizado
```

**Limitações do modelo:**
- Pode não identificar corretamente componentes em diagramas muito complexos ou com notação não-padrão
- Qualidade da análise depende da resolução e legibilidade do diagrama
- Pode gerar riscos genéricos quando o diagrama está incompleto
- Latência variável da API pode afetar o tempo de processamento

---

## Requisitos

- Docker e Docker Compose
- Chave de API Anthropic (`ANTHROPIC_API_KEY`)

---

## Instruções de Execução

### 1. Clonar o repositório

```bash
git clone <repo-url>
cd hackathon
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Editar .env e preencher ANTHROPIC_API_KEY
```

### 3. Subir os serviços

```bash
docker compose up --build
```

### 4. Acessar a interface web

Abra no navegador:
```
http://localhost:3000
```

A interface permite:
- Arrastar e soltar ou selecionar um diagrama (PNG, JPG, WEBP, GIF, PDF)
- Acompanhar o status do processamento em tempo real
- Visualizar o relatório completo com componentes, riscos e recomendações

### 5. Testar via API (opcional)

```bash
# Upload de um diagrama
curl -X POST http://localhost:8000/api/v1/analyses \
  -F "file=@/caminho/para/diagrama.png"

# Consultar status
curl http://localhost:8000/api/v1/analyses/abc-123

# Consultar relatório (quando status = ANALYZED)
curl http://localhost:8000/api/v1/analyses/abc-123/report
```

Documentação interativa da API (Swagger): `http://localhost:8000/docs`

### 6. Monitorar RabbitMQ (opcional)

Acesse `http://localhost:15672` (usuário: `admin`, senha: `admin`)

---

## Endpoints da API

### API Gateway (`:8000`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/v1/analyses` | Upload de diagrama (multipart/form-data) |
| `GET` | `/api/v1/analyses/{id}` | Consulta status do processamento |
| `GET` | `/api/v1/analyses/{id}/report` | Obtém relatório gerado |
| `GET` | `/health` | Health check |

### Status possíveis

| Status | Significado |
|--------|-------------|
| `RECEIVED` | Arquivo recebido e na fila |
| `PROCESSING` | IA analisando o diagrama |
| `ANALYZED` | Relatório gerado com sucesso |
| `ERROR` | Falha no processamento |

### Exemplo de resposta — Relatório

```json
{
  "report_id": "uuid",
  "analysis_id": "uuid",
  "summary": "Arquitetura de microsserviços com API Gateway central...",
  "components": [
    {"name": "API Gateway", "type": "gateway", "description": "Ponto de entrada único..."},
    {"name": "User Service", "type": "service", "description": "Gerencia autenticação..."},
    {"name": "PostgreSQL", "type": "database", "description": "Persistência principal..."}
  ],
  "architectural_risks": [
    {
      "severity": "high",
      "title": "Ponto único de falha no API Gateway",
      "description": "Sem redundância configurada, uma falha derruba todo o sistema."
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "title": "Implementar redundância no Gateway",
      "action": "Configurar múltiplas instâncias com load balancer (ex: NGINX ou AWS ALB)."
    }
  ],
  "created_at": "2026-05-20T12:00:00"
}
```

---

## Executar Testes

```bash
# Todos os serviços
for svc in api-gateway upload-service processing-service report-service; do
  echo "=== $svc ==="
  cd services/$svc && pip install -r requirements.txt && pytest tests/ -v && cd ../..
done
```

---

## Segurança

### Requisitos de segurança adotados

**Validação de entrada:**
- Tipos MIME permitidos: apenas `image/png`, `image/jpeg`, `image/webp`, `image/gif`, `application/pdf`
- Limite de tamanho de arquivo: 10 MB no upload, 15 MB na análise
- Arquivos vazios rejeitados com HTTP 400
- Validação de UUID nos parâmetros de rota

**Uso controlado da IA:**
- System prompt com regras estritas de output (somente JSON, sem texto livre)
- Guardrail de saída valida estrutura, tipos permitidos e tamanho dos campos
- Detecção de resposta de erro do modelo (`{"error": "not_architecture_diagram"}`)
- Truncamento automático de campos para prevenir overflow
- Retry com backoff exponencial em caso de rate limit

**Tratamento seguro de falhas da IA:**
- Exceções do modelo são capturadas e mapeadas para status `ERROR`
- Mensagem de erro sanitizada antes de persistir (máx 500 chars)
- Falha no Report Service não propaga exceção não tratada

**Comunicação entre serviços:**
- Comunicação interna via rede Docker isolada (`hackathon-net`)
- Sem exposição de portas internas ao host (exceto API Gateway :8000)
- RabbitMQ com usuário/senha configuráveis via variáveis de ambiente
- API Key da Anthropic injetada como variável de ambiente, nunca em código

**Riscos e limitações identificados:**
- Em produção, adicionar HTTPS/TLS no API Gateway
- Autenticação/autorização não implementada neste MVP (adicionar JWT/OAuth2)
- Arquivos são armazenados em volume local — em produção usar S3/GCS com lifecycle policy
- Sem rate limiting no API Gateway (adicionar middleware em produção)
- A chave `ANTHROPIC_API_KEY` deve ser gerenciada via secrets manager em produção (AWS Secrets Manager, Vault)

---

## Estrutura do Projeto

```
hackathon/
├── docker-compose.yml
├── .env.example
├── .github/workflows/ci.yml
├── README.md
└── services/
    ├── frontend/              # Interface web (HTML/CSS/JS + Nginx) — :3000
    ├── api-gateway/           # BFF — roteia requisições — :8000
    ├── upload-service/        # Recebe arquivos, cria jobs, publica na fila — :8001
    ├── processing-service/    # Worker IA — consome fila, chama Claude
    └── report-service/        # Persiste e serve relatórios — :8003
```

Cada serviço segue Clean Architecture:
```
src/
├── domain/          # Entidades e interfaces de repositório
├── application/     # Casos de uso
├── infrastructure/  # Implementações (DB, mensageria, IA, HTTP)
└── interfaces/      # Controllers HTTP, schemas Pydantic
```

---

## CI/CD

Pipeline GitHub Actions em `.github/workflows/ci.yml`:

1. **Test** — roda `pytest` para cada serviço em paralelo
2. **Build** — constrói todas as imagens Docker
3. **Integration** — sobe os serviços e verifica health checks (somente branch `main`)
