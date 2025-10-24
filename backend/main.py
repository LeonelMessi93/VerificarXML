from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO

app = FastAPI(title="Verificar XML API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NS = {"ns": "http://www.portalfiscal.inf.br/nfe"}

def get_text(element, path):
    if element is None:
        return ""
    node = element.find(path, NS)
    return node.text if node is not None else ""

def xml_to_dataframe(xml_bytes: bytes) -> pd.DataFrame:
    root = ET.fromstring(xml_bytes)

    infNFe = root.find(".//ns:infNFe", NS)
    if infNFe is None:
        raise ValueError("Não foi possível localizar o nó <infNFe> no XML informado.")

    ide = infNFe.find("ns:ide", NS)
    emit = infNFe.find("ns:emit", NS)
    enderEmit = emit.find("ns:enderEmit", NS) if emit is not None else None
    dest = infNFe.find("ns:dest", NS)
    enderDest = dest.find("ns:enderDest", NS) if dest is not None else None
    transp = infNFe.find("ns:transp", NS)
    transporta = transp.find("ns:transporta", NS) if transp is not None else None
    total = infNFe.find("ns:total", NS)
    icmsTot = total.find("ns:ICMSTot", NS) if total is not None else None
    protNFe = root.find(".//ns:protNFe", NS)
    infProt = protNFe.find("ns:infProt", NS) if protNFe is not None else None

    rows = []
    for det in infNFe.findall("ns:det", NS):
        prod = det.find("ns:prod", NS)
        imposto = det.find("ns:imposto", NS)

        icms_any, icms_tag = None, ""
        if imposto is not None:
            for tag in ["ICMS00", "ICMS10", "ICMS20", "ICMS30", "ICMS40", "ICMS51", "ICMS60", "ICMS70", "ICMS90"]:
                node = imposto.find(f".//ns:{tag}", NS)
                if node is not None:
                    icms_any, icms_tag = node, tag
                    break

        row = {
            "ChaveNFe": get_text(infProt, "ns:chNFe"),
            "IDE_nNF": get_text(ide, "ns:nNF"),
            "IDE_serie": get_text(ide, "ns:serie"),
            "IDE_dhEmi": get_text(ide, "ns:dhEmi"),
            "Emitente_CNPJ": get_text(emit, "ns:CNPJ"),
            "Emitente_Nome": get_text(emit, "ns:xNome"),
            "Destinatario_ID": get_text(dest, "ns:CNPJ") or get_text(dest, "ns:idEstrangeiro"),
            "Destinatario_Nome": get_text(dest, "ns:xNome"),
            "Produto_NumItem": det.get("nItem"),
            "Produto_Codigo": get_text(prod, "ns:cProd"),
            "Produto_Descricao": get_text(prod, "ns:xProd"),
            "Produto_NCM": get_text(prod, "ns:NCM"),
            "Produto_CFOP": get_text(prod, "ns:CFOP"),
            "Produto_qCom": get_text(prod, "ns:qCom"),
            "Produto_vUnCom": get_text(prod, "ns:vUnCom"),
            "Produto_vProd": get_text(prod, "ns:vProd"),
            "ICMS_Grupo": icms_tag,
            "ICMS_orig": get_text(icms_any, "ns:orig") if icms_any is not None else "",
            "ICMS_CST": get_text(icms_any, "ns:CST") if icms_any is not None else "",
            "Total_vNF": get_text(icmsTot, "ns:vNF"),
            "Emitente_UF": get_text(enderEmit, "ns:UF"),
            "Destinatario_UF": get_text(enderDest, "ns:UF"),
        }
        rows.append(row)

    if not rows:
        raise ValueError("Nenhum item <det> foi encontrado no XML.")

    df = pd.DataFrame(rows)
    for col in ["Produto_qCom", "Produto_vUnCom", "Produto_vProd", "Total_vNF"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

@app.post("/upload")
async def upload_xml(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith(".xml"):
            return JSONResponse({"error": "Envie um arquivo .xml"}, status_code=400)

        xml_bytes = await file.read()
        df = xml_to_dataframe(xml_bytes)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="XML")
        output.seek(0)

        filename = "Validador_XML.xlsx"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(output,
                                 media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers=headers)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/upload_json")
async def upload_xml_json(file: UploadFile = File(...), preview_rows: int = Query(100, ge=1, le=1000)):
    """
    Variante para pré-visualização no site: retorna JSON com até 'preview_rows' linhas.
    """
    try:
        if not file.filename.lower().endswith(".xml"):
            return JSONResponse({"error": "Envie um arquivo .xml"}, status_code=400)

        xml_bytes = await file.read()
        df = xml_to_dataframe(xml_bytes)

        # Limita a prévia pra evitar respostas gigantes
        preview = df.head(preview_rows).to_dict(orient="records")
        return {"columns": list(df.columns), "rows": preview, "total_rows": len(df)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/ping")
def ping():
    return {"ok": True}
