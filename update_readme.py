import os
import json
import re
from datetime import datetime

# Caminhos relativos ao repositório git (que será a pasta Tucelos)
README_PATH = "README.md"
CREDENTIALS_DIR = "credentials"

def parse_credentials():
    credentials = {}
    
    if not os.path.exists(CREDENTIALS_DIR):
        print(f"Diretório '{CREDENTIALS_DIR}' não encontrado.")
        return []

    # Lista todos os arquivos JSON que começam com "credential-"
    for filename in os.listdir(CREDENTIALS_DIR):
        if filename.endswith(".json") and filename.startswith("credential-"):
            filepath = os.path.join(CREDENTIALS_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Identificador único da credencial
                cred_url = data.get("id", "")
                if not cred_url:
                    continue
                
                # Extração de campos
                name = data.get("name")
                issuer_name = data.get("issuer", {}).get("name", "Unknown")
                valid_from_str = data.get("validFrom", "")
                
                # Formata a data de AAAA-MM-DD para DD/MM/AAAA
                date_formatted = ""
                if valid_from_str:
                    # Remove a parte do timezone se necessário para compatibilidade com fromisoformat antiga
                    cleaned_date = valid_from_str.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(cleaned_date)
                    date_formatted = dt.strftime("%d/%m/%Y")
                
                image = data.get("image")
                image_url = ""
                if isinstance(image, dict):
                    image_url = image.get("id", "")
                elif isinstance(image, str):
                    image_url = image
                
                # Armazena usando o cred_url como chave para remover duplicatas
                # (já que temos versões -ob3 e -w3cvc da mesma credencial)
                credentials[cred_url] = {
                    "name": name,
                    "issuer": issuer_name,
                    "date": date_formatted,
                    "image": image_url,
                    "url": cred_url
                }
                print(f"Processado: {name} (Emissor: {issuer_name})")
            except Exception as e:
                print(f"Erro ao processar o arquivo {filename}: {e}")
                
    # Ordena as credenciais por data de emissão decrescente (mais recentes primeiro)
    def get_sort_key(item):
        try:
            return datetime.strptime(item["date"], "%d/%m/%Y")
        except Exception:
            return datetime.min

    sorted_creds = sorted(credentials.values(), key=get_sort_key, reverse=True)
    return sorted_creds

def update_readme(creds):
    if not os.path.exists(README_PATH):
        print(f"Erro: '{README_PATH}' não encontrado no diretório atual ({os.getcwd()}).")
        return
        
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme_content = f.read()
        
    # Gera a seção das certificações formatada
    cert_section = "### 📜 Certificações\n\n"
    if not creds:
        cert_section += "*Nenhuma certificação cadastrada ainda.*\n"
    else:
        for c in creds:
            # Mostra o badge em miniatura se houver imagem
            badge_img = f'<img src="{c["image"]}" width="22" height="22" align="center" alt="Badge"/> ' if c["image"] else ""
            cert_section += f"- {badge_img}[**{c['name']}**]({c['url']}) - *{c['issuer']}* ({c['date']})\n"
        
    # Substitui o bloco entre os marcadores <!-- START_SECTION:certifications --> e <!-- END_SECTION:certifications -->
    start_marker = "<!-- START_SECTION:certifications -->"
    end_marker = "<!-- END_SECTION:certifications -->"
    
    if start_marker in readme_content and end_marker in readme_content:
        pattern = re.compile(rf"{start_marker}.*?{end_marker}", re.DOTALL)
        new_content = pattern.sub(f"{start_marker}\n\n{cert_section}\n{end_marker}", readme_content)
        
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("README.md atualizado com sucesso!")
    else:
        print("Marcadores de seção não encontrados no README.md.")

if __name__ == "__main__":
    creds = parse_credentials()
    update_readme(creds)
