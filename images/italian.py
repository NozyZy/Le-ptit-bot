#!/usr/bin/env python3
"""
Extraction des personnages depuis la page Italian Brainrot Wiki
Usage:
  python italian.py              -> Telecharge automatiquement la page
  python italian.py fichier.htm  -> Utilise un fichier HTML local
"""

import re
import json
import sys
import os

# URL de la page
WIKI_URL = "https://italianbrainrot.miraheze.org/wiki/List_of_characters"

# Images a ignorer (icones, drapeaux, symboles)
IGNORE_PATTERNS = [
    'Variant.png', 'Star-', 'Modmade', 'Lostmedia',
    'Corporation', 'Before', 'Reference', 'Flag_of_',
    'Wiki.png', 'Hausa.png', 'Kanuri.png', 'Javanese.png',
    'Kampampangan.png', 'Sundanese.png', 'Waray_Language.png'
]

# Noms a ignorer (categories, pas des personnages individuels)
IGNORE_NAMES = [
    'Brainrots', 'width', 'height', 'Jump to', 'navigation',
    'search', 'Legend', 'Symbols', 'Countries', 'Non-countries'
]


def download_page(url):
    """Telecharge le contenu de la page"""
    try:
        import requests
    except ImportError:
        print("La bibliotheque 'requests' n'est pas installee")
        print("   Installez-la avec : pip install requests")
        sys.exit(1)

    print(f"Telechargement de la page depuis {url}...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"Page telechargee ({len(response.text):,} caracteres)\n")
        return response.text
    except Exception as e:
        print(f"Erreur : {e}")
        print(f"\nTelechargez la page manuellement et relancez avec :")
        print(f"   python {os.path.basename(__file__)} fichier.htm")
        sys.exit(1)


def load_local_file(filepath):
    """Charge un fichier HTML local"""
    print(f"Lecture du fichier local : {filepath}")

    if not os.path.exists(filepath):
        print("Erreur : Le fichier n'existe pas")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Fichier charge ({len(content):,} caracteres)\n")
    return content


def is_character_image(img_path):
    """Verifie si c'est une image de personnage (pas une icone/drapeau)"""
    return not any(pattern in img_path for pattern in IGNORE_PATTERNS)


def is_valid_name(name):
    """Verifie si le nom est un personnage valide (pas une categorie)"""
    if not name or len(name) <= 1:
        return False
    # Verifier les noms a ignorer
    return not any(ignored.lower() in name.lower() for ignored in IGNORE_NAMES)


def get_full_image_url(thumb_url):
    """Convertit une URL de miniature en URL d'image complete"""
    # Format: //static.wikitide.net/italianbrainrotwiki/thumb/a/ab/Image.png/30px-Image.png
    # Devient: https://static.wikitide.net/italianbrainrotwiki/a/ab/Image.png

    if thumb_url.startswith('//'):
        thumb_url = 'https:' + thumb_url

    # Si c'est une miniature, extraire le chemin original
    if '/thumb/' in thumb_url:
        # Supprimer la partie /XXpx-filename a la fin
        match = re.match(r'(https?://static\.wikitide\.net/italianbrainrotwiki)/thumb/(.+?)/\d+px-[^/]+$', thumb_url)
        if match:
            return f"{match.group(1)}/{match.group(2)}"

    return thumb_url


def extract_from_normal_html(html_content):
    """Extrait les personnages depuis du HTML normal (page telechargee)"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
    except ImportError:
        print("BeautifulSoup non disponible, utilisation du parsing regex")
        return None

    characters = []
    seen = set()

    # Trouver la section "List of Brainrots"
    list_section = soup.find('h2', id='List_of_Brainrots')
    if not list_section:
        # Chercher par texte
        for h2 in soup.find_all('h2'):
            if 'List of Brainrots' in h2.get_text():
                list_section = h2
                break

    if not list_section:
        print("Section 'List of Brainrots' non trouvee, analyse de toute la page")
        search_area = soup
    else:
        # Chercher dans le contenu apres cette section
        search_area = soup

    # Trouver tous les <li> avec des images de personnages
    for li in search_area.find_all('li'):
        # Chercher une image de personnage dans ce <li>
        img = None
        for span in li.find_all('span', typeof='mw:File'):
            img_tag = span.find('img')
            if img_tag and img_tag.get('src'):
                src = img_tag['src']
                if 'italianbrainrotwiki' in src and is_character_image(src):
                    img = img_tag
                    break

        if not img:
            continue

        # Chercher le nom du personnage (dernier lien avec du texte)
        name = None
        for link in li.find_all('a'):
            text = link.get_text().strip()
            # Ignorer les liens vides ou invalides
            if is_valid_name(text):
                name = text

        if not name:
            continue

        # Construire l'URL complete
        img_url = get_full_image_url(img['src'])

        # Eviter les doublons
        key = f"{name}|{img_url}"
        if key not in seen:
            seen.add(key)
            characters.append({"name": name, "img": img_url})

    return characters


def extract_from_view_source(html_content):
    """Extrait les personnages depuis du HTML view-source"""
    characters = []
    seen = set()

    # Trouver le debut de la section "List of Brainrots"
    list_start = html_content.find('List_of_Brainrots')
    if list_start == -1:
        list_start = html_content.find('List of Brainrots')
    if list_start == -1:
        print("Attention: Section 'List of Brainrots' non trouvee, analyse complete")
        list_start = 0
    else:
        print(f"Section 'List of Brainrots' trouvee a la position {list_start}")

    # Extraire uniquement le contenu apres cette section
    content_to_parse = html_content[list_start:]

    # Pattern pour le format view-source
    # Image: //static.wikitide.net/italianbrainrotwiki/thumb/path/file.png
    # Nom: <span>NomPersonnage</span><span>&lt;/<span class="end-tag">a</span>&gt;

    # Pattern simplifie: chercher les images italianbrainrotwiki suivies d'un nom
    pattern = r'//static\.wikitide\.net/italianbrainrotwiki/(?:thumb/)?([^"<>\s]+?\.(?:png|jpg|jpeg|webp|gif))(?:/\d+px-[^"<>\s]+)?[^<]*?</a>.*?<a[^>]*>.*?<span>([^<]{2,100})</span><span>&lt;/<span class="end-tag">a</span>'

    for match in re.finditer(pattern, content_to_parse, re.DOTALL):
        img_path = match.group(1)
        name = match.group(2).strip()

        # Ignorer les icones
        if not is_character_image(img_path):
            continue

        # Ignorer les noms invalides
        if not is_valid_name(name):
            continue

        # Construire l'URL complete
        img_url = f"https://static.wikitide.net/italianbrainrotwiki/{img_path}"

        # Eviter les doublons
        key = f"{name}|{img_url}"
        if key not in seen:
            seen.add(key)
            characters.append({"name": name, "img": img_url})

    return characters


def extract_characters(html_content):
    """Extrait les personnages depuis le HTML (auto-detecte le format)"""

    # Detecter si c'est du view-source
    is_view_source = '<span class="start-tag">' in html_content or '<span class="end-tag">' in html_content

    if is_view_source:
        print("Format view-source detecte")
        characters = extract_from_view_source(html_content)
    else:
        print("Format HTML normal detecte")
        characters = extract_from_normal_html(html_content)

        # Fallback sur regex si BeautifulSoup echoue
        if characters is None:
            characters = extract_fallback_regex(html_content)

    return characters


def extract_fallback_regex(html_content):
    """Methode de fallback avec regex pour HTML normal"""
    characters = []
    seen = set()

    # Pattern pour HTML normal
    pattern = r'<img[^>]*src="((?:https?:)?//static\.wikitide\.net/italianbrainrotwiki/[^"]+)"[^>]*>.*?<a[^>]*>([^<]+)</a>'

    for match in re.finditer(pattern, html_content, re.DOTALL):
        img_url = match.group(1)
        name = match.group(2).strip()

        if not is_character_image(img_url):
            continue

        if not is_valid_name(name):
            continue

        if img_url.startswith('//'):
            img_url = 'https:' + img_url

        img_url = get_full_image_url(img_url)

        key = f"{name}|{img_url}"
        if key not in seen:
            seen.add(key)
            characters.append({"name": name, "img": img_url})

    return characters


def save_results(characters, output_file='italian.json'):
    """Sauvegarde les resultats dans un fichier JSON"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_file)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(characters, f, indent=2, ensure_ascii=False)

    return output_path


def main():
    print("=" * 60)
    print("   Extracteur de personnages - Italian Brainrot Wiki")
    print("=" * 60)
    print()

    # Source
    if len(sys.argv) > 1:
        html_content = load_local_file(sys.argv[1])
    else:
        html_content = download_page(WIKI_URL)

    # Extraction
    print("Extraction des personnages...\n")
    characters = extract_characters(html_content)

    if characters:
        print(f"{len(characters)} personnages trouves !\n")

        # Sauvegarde
        output_path = save_results(characters)

        # Apercu
        print("Apercu des personnages:")
        for i, char in enumerate(characters[:15], 1):
            print(f"   {i:3}. {char['name']}")
        if len(characters) > 15:
            print(f"        ... et {len(characters) - 15} autres")

        print(f"\nFichier cree : {output_path}")
    else:
        print("Aucun personnage trouve")
        print("\nConseils:")
        print("  - Verifiez que le fichier HTML contient bien la liste des personnages")
        print("  - Essayez de telecharger la page directement (sans argument)")


if __name__ == "__main__":
    main()
