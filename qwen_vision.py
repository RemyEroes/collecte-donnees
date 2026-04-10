import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from pdf2image import convert_from_path
import json
import os
import re

def traiter_pdf_qwen2_vl(chemin_pdf):
    filename_without_extension = os.path.splitext(os.path.basename(chemin_pdf))[0]
    print("1. Conversion du PDF en image...")
    pages = convert_from_path(chemin_pdf, dpi=100)  # Réduction de la résolution à 100 DPI
    image_temp = "page_temp.jpg"
    pages[0].save(image_temp, "JPEG")  # On prend la page 1 pour l'exemple

    print("2. Chargement du modèle Qwen2-VL-2B sur la puce Apple (MPS)...")
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen2-VL-2B-Instruct",
        torch_dtype=torch.bfloat16,
        device_map="mps"
    )
    processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-2B-Instruct")

    print("3. Analyse de l'image en cours (cela peut prendre 1 à 2 minutes la première fois)...")

    prompt = """
    Tu es un expert en extraction de données. Regarde cette image qui est le classement officiel d'une course de ski.
    Extrait toutes les lignes de résultats des skieurs et formate-les dans un tableau JSON.

    Utilise EXACTEMENT ces clés :
    - "rank" (entier)
    - "bib" (entier)
    - "fis_code" (chaine)
    - "name" (chaine)
    - "year_birth" (entier)
    - "country_code" (chaine de 3 lettres)
    - "time_raw" (chaine, ex: "1:52.31")
    - "diff_raw" (chaine, ex: "+0.07")
    - "distance" (float)
    - "points" (float)
    - "ski" (chaine)

    Renvoie UNIQUEMENT un tableau JSON valide (commençant par [ et finissant par ]). Si une info manque, mets null. N'ajoute AUCUN texte avant ou après le JSON.
    """

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_temp},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to("mps")

    # Génération de la réponse avec une limite réduite de tokens
    generated_ids = model.generate(**inputs, max_new_tokens=5000)  # Réduction à 500 tokens
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    os.remove(image_temp)

    print("\n4. Extraction terminée. Nettoyage des données...")
    json_str = output_text.strip()
    if json_str.startswith("```json"):
        json_str = json_str.replace("```json", "", 1)
    if json_str.endswith("```"):
        json_str = re.sub(r'```$', '', json_str)

    try:
        data = json.loads(json_str)
        fichier_sortie = f"resultats-qwen/resultats_{filename_without_extension}.json"
        with open(fichier_sortie, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Succès ! Données sauvegardées dans {fichier_sortie}")
    except json.JSONDecodeError:
        print("❌ Erreur : Le modèle n'a pas généré un JSON pur. Voici la réponse brute :")
        print(output_text)

if __name__ == "__main__":
    mon_pdf = "pdf-scrapping-men/1948-downhill.pdf"
    traiter_pdf_qwen2_vl(mon_pdf)
