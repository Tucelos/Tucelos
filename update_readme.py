import os
import json
import re
from datetime import datetime

# Caminhos relativos ao repositório git (que será a pasta Tucelos)
README_PATH = "README.md"
COURSES_DIR = "cursos"
CERTS_DIR = "certificacoes"

def parse_credentials_from_dir(directory_path):
    credentials = {}
    
    if not os.path.exists(directory_path):
        print(f"Diretório '{directory_path}' não encontrado.")
        return []

    # Lista todos os arquivos JSON que começam com "credential-"
    for filename in os.listdir(directory_path):
        if filename.endswith(".json") and filename.startswith("credential-"):
            filepath = os.path.join(directory_path, filename)
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
                
                # Pega a data de criação precisa do proof para ordenação detalhada
                proof_created = data.get("proof", {}).get("created", "")
                
                # Armazena usando o cred_url como chave para remover duplicatas
                # (já que temos versões -ob3 e -w3cvc da mesma credencial)
                credentials[cred_url] = {
                    "name": name,
                    "issuer": issuer_name,
                    "date": date_formatted,
                    "image": image_url,
                    "url": cred_url,
                    "raw_date": valid_from_str,
                    "created_at": proof_created
                }
                print(f"Processado [{directory_path}]: {name} (Emissor: {issuer_name})")
            except Exception as e:
                print(f"Erro ao processar o arquivo {filename} em {directory_path}: {e}")
                
    # Ordena as credenciais por data de emissão decrescente (mais recentes primeiro)
    def get_sort_key(item):
        try:
            if item.get("created_at"):
                return datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        except Exception:
            pass
        try:
            if item.get("raw_date"):
                return datetime.fromisoformat(item["raw_date"].replace("Z", "+00:00"))
        except Exception:
            pass
        try:
            return datetime.strptime(item["date"], "%d/%m/%Y")
        except Exception:
            return datetime.min

    sorted_creds = sorted(credentials.values(), key=get_sort_key, reverse=True)
    return sorted_creds

def generate_section_content(creds, title, image_size, is_empty_placeholder):
    section = f"### {title}\n\n"
    if not creds:
        section += f"{is_empty_placeholder}\n"
    else:
        # Exibe os badges em formato de grade (lado a lado)
        html_links = []
        for c in creds:
            if c["image"]:
                tooltip = f"{c['name']} - {c['issuer']} ({c['date']})"
                html_links.append(
                    f'<a href="{c["url"]}" target="_blank">\n'
                    f'  <img src="{c["image"]}" width="{image_size}" height="{image_size}" title="{tooltip}" alt="{c["name"]}" />\n'
                    f'</a>'
                )
        section += " &nbsp;&nbsp; ".join(html_links) + "\n"
    return section

def update_readme(certifications, courses):
    if not os.path.exists(README_PATH):
        print(f"Erro: '{README_PATH}' não encontrado no diretório atual ({os.getcwd()}).")
        return
        
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme_content = f.read()
        
    # Gera a seção das certificações formatada
    cert_section = generate_section_content(
        certifications,
        "📜 Certificações",
        image_size=110,
        is_empty_placeholder="*Nenhuma certificação cadastrada ainda.*"
    )

    # Gera a seção dos cursos formatada
    courses_section = generate_section_content(
        courses,
        "📚 Cursos",
        image_size=95,
        is_empty_placeholder="*Nenhum curso cadastrado ainda.*"
    )
        
    # Substitui o bloco entre os marcadores <!-- START_SECTION:certifications --> e <!-- END_SECTION:certifications -->
    start_cert = "<!-- START_SECTION:certifications -->"
    end_cert = "<!-- END_SECTION:certifications -->"
    if start_cert in readme_content and end_cert in readme_content:
        pattern = re.compile(rf"{start_cert}.*?{end_cert}", re.DOTALL)
        readme_content = pattern.sub(f"{start_cert}\n\n{cert_section}\n{end_cert}", readme_content)
    else:
        print("Marcadores de certificações não encontrados no README.md.")
        
    # Substitui o bloco entre os marcadores <!-- START_SECTION:courses --> e <!-- END_SECTION:courses -->
    start_courses = "<!-- START_SECTION:courses -->"
    end_courses = "<!-- END_SECTION:courses -->"
    if start_courses in readme_content and end_courses in readme_content:
        pattern = re.compile(rf"{start_courses}.*?{end_courses}", re.DOTALL)
        readme_content = pattern.sub(f"{start_courses}\n\n{courses_section}\n{end_courses}", readme_content)
    else:
        print("Marcadores de cursos não encontrados no README.md.")
        
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("README.md atualizado com sucesso!")

if __name__ == "__main__":
    certifications = parse_credentials_from_dir(CERTS_DIR)
    courses = parse_credentials_from_dir(COURSES_DIR)
    update_readme(certifications, courses)
