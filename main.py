from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import requests, bitrix

app = FastAPI()

@app.post("/lead-score")
async def lead_score(id: str):
    try:
        card = bitrix.deal_get(id)
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=500, detail=f"Erro HTTP ao conectar com Bitrix24: {http_err}")
    except requests.exceptions.RequestException as err:
        print(f"Erro de conexão ao Bitrix24: {err}")
        raise HTTPException(status_code=500, detail=f"Erro de conexão ao Bitrix24: {err}")
    
    pontuacao = 0

    inicial = card.get('UF_CRM_1758287802')
    qualificacoes_realizadas = int(card.get('UF_CRM_1758291069013')) if card.get('UF_CRM_1758291069013') else 0
    
    if not inicial:
        return JSONResponse(
            {
                "error": {
                    "code": "MISSING_REQUIRED_FIELD",
                    "message": "O campo (UF_CRM_1758287802) é um campo obrigatório e não foi encontrado ou está vazio para o negócio fornecido.",
                }
            }, 
            status_code=400
        )
    
    # Fluxo A
    if inicial == "425":
        resposta1 = card.get('UF_CRM_1758287977')
        match resposta1:
            case "433":
                pass
            case "435":
                pontuacao += 1
            case "437":
                pontuacao += 2

        resposta2 = card.get('UF_CRM_1758288169')
        match resposta2:
            case "439":
                pass
            case "441":
                pontuacao += 1
            case "443":
                pontuacao += 2
        
        resposta3 = card.get('UF_CRM_1758288782')
        match resposta3:
            case "465":
                pontuacao += 2
            case "467":
                pontuacao += 1
            case "469":
                pass
    
    # Fluxo B
    elif inicial == "427":
        resposta1 = card.get('UF_CRM_1758288450')
        match resposta1:
            case "445":
                pontuacao += 2
            case "447":
                pontuacao += 1
            case "449":
                pass
        
        resposta2 = card.get('UF_CRM_1758288592')
        match resposta2:
            case "451":
                pontuacao += 2
            case "453":
                pontuacao += 1
            case "455":
                pass
            case "457":
                pontuacao += 1

        resposta3 = card.get('UF_CRM_1758288715')
        match resposta3:
            case "459":
                pontuacao += 2
            case "461":
                pontuacao += 1
            case "463":
                pass
    
    bitrix.deal_update(id, 
        {
            "UF_CRM_1758289316": pontuacao,
            "UF_CRM_1758289334": "Quente" if pontuacao > 4 else "Morno" if pontuacao > 2 else "Frio",
        }
    )
    
    if qualificacoes_realizadas < 1:
        del card['ID']
        card['STAGE_ID'] = "C3:NEW"
        card['CATEGORY_ID'] = "3"
        card["UF_CRM_1758289316"] = pontuacao,
        card["UF_CRM_1758289334"] = "Quente" if pontuacao > 4 else "Morno" if pontuacao > 2 else "Frio"
        bitrix.deal_add(card)

    return JSONResponse(
        {
            "status": "success",
            "message": "Lead Score feito com sucesso.",
        },
        status_code=200
    )
    
@app.post("/validar-cadastro")
async def validar_cadastro(id: str):
    try:
        card = bitrix.deal_get(id)
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=500, detail=f"Erro HTTP ao conectar com Bitrix24: {http_err}")
    except requests.exceptions.RequestException as err:
        print(f"Erro de conexão ao Bitrix24: {err}")
        raise HTTPException(status_code=500, detail=f"Erro de conexão ao Bitrix24: {err}")
    
    etapa = card.get('STAGE_ID')
    id_contato = card.get('CONTACT_ID')

    # Cadastro Validado
    if etapa == "C7:PREPARATION":
        equivalentes = bitrix.deal_list({"CATEGORY_ID": "1", "=CONTACT_ID": id_contato, "STAGE_ID": "C1:8"}, [])

        if not equivalentes:
            return JSONResponse(
                {
                    "error": {
                        "code": "PARTIAL_SUCESS",
                        "message": "O negócio foi processado, mas não foi encontrado um equivalente",
                    }
                }, 
                status_code=200
            )
        
        equivalente = equivalentes[0]
        equivalente_id = equivalente.get('ID')

        bitrix.deal_update(equivalente_id, 
            {
                "UF_CRM_1750270946576": card.get("UF_CRM_1750270946576"), # Limite de Crédito
                "STAGE_ID": "C1:WON"
            }
        )

        return JSONResponse(
            {
                "status": "success",
                "message": "O negócio equivalente foi atualizado com sucesso.",
            },
            status_code=200
        )
    
    # Cadastro Não Validado 
    elif etapa == "C7:PREPAYMENT_INVOICE":
        equivalentes = bitrix.deal_list({"CATEGORY_ID": "1", "=CONTACT_ID": id_contato, "STAGE_ID": "C1:8"}, [])

        if not equivalentes:
            return JSONResponse(
                {
                    "error": {
                        "code": "PARTIAL_SUCESS",
                        "message": "O negócio foi processado, mas não foi encontrado um equivalente",
                    }
                }, 
                status_code=200
            )
        
        equivalente = equivalentes[0]
        equivalente_id = equivalente.get('ID')

        bitrix.deal_update(equivalente_id, 
            {
                "UF_CRM_1756753221010": card.get('UF_CRM_1756753221010'), # Motivo da reprovação de cadastro
                "STAGE_ID": "C1:9"
            }
        )

        return JSONResponse(
            {
                "status": "success",
                "message": "O negócio equivalente foi atualizado com sucesso.",
            },
            status_code=200
        )


    else:
        return JSONResponse(
            {
                "error": {
                    "code": "UNEXPECTED_COLUMN",
                    "message": "O negócio não está na coluna esperada.",
                }
            }, 
            status_code=400
        )

@app.post("/aprovar-credito")
async def aprovar_credito(id: str):
    try:
        card = bitrix.deal_get(id)
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=500, detail=f"Erro HTTP ao conectar com Bitrix24: {http_err}")
    except requests.exceptions.RequestException as err:
        print(f"Erro de conexão ao Bitrix24: {err}")
        raise HTTPException(status_code=500, detail=f"Erro de conexão ao Bitrix24: {err}")
    
    etapa = card.get('STAGE_ID')
    id_contato = card.get('CONTACT_ID')

    # Crédito Aprovado
    if etapa == "C7:4":
        equivalentes = bitrix.deal_list({"CATEGORY_ID": "3", "=CONTACT_ID": id_contato, "STAGE_ID": "C3:17"}, [])

        if not equivalentes:
            return JSONResponse(
                {
                    "error": {
                        "code": "PARTIAL_SUCESS",
                        "message": "O negócio foi processado, mas não foi encontrado um equivalente",
                    }
                }, 
                status_code=200
            )
        
        equivalente = equivalentes[0]
        equivalente_id = equivalente.get('ID')

        bitrix.deal_update(equivalente_id, 
            {
                "STAGE_ID": "C3:18"
            }
        )

        return JSONResponse(
            {
                "status": "success",
                "message": "O negócio equivalente foi atualizado com sucesso.",
            },
            status_code=200
        )
    
    # Crédito Reprovado
    elif etapa == "C7:3":
        equivalentes = bitrix.deal_list({"CATEGORY_ID": "3", "=CONTACT_ID": id_contato, "STAGE_ID": "C3:17"}, [])

        if not equivalentes:
            return JSONResponse(
                {
                    "error": {
                        "code": "PARTIAL_SUCESS",
                        "message": "O negócio foi processado, mas não foi encontrado um equivalente",
                    }
                }, 
                status_code=200
            )
        
        equivalente = equivalentes[0]
        equivalente_id = equivalente.get('ID')

        bitrix.deal_update(equivalente_id, 
            {
                "UF_CRM_1756753660736": card.get('UF_CRM_1756753660736'), # Motivo da reprovação de crédito
                "STAGE_ID": "C3:19"
            }
        )

        return JSONResponse(
            {
                "status": "success",
                "message": "O negócio equivalente foi atualizado com sucesso.",
            },
            status_code=200
        )

    else:
        return JSONResponse(
            {
                "error": {
                    "code": "UNEXPECTED_COLUMN",
                    "message": "O negócio não está na coluna esperada.",
                }
            }, 
            status_code=400
        )
