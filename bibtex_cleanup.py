import re, os, argparse, bibtexparser, unicodedata

def strclean(s):
    s = re.sub(r'\\[a-zA-Z]+\{?([a-zA-Z])\}?', r'\1', s)
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r'[^a-z0-9 ]', '', s.lower())
    return s

def clean_entries(entries, delete_set, doi_set, id_set, cache_id_set): 
    for entry in entries:
        if 'abstract' in entry:
            del entry['abstract']

        if 'keywords' in entry:
            del entry['keywords']

        if 'language' in entry:
            del entry['language']

        try:
            entry['author'] = entry.get('author', '') or entry.get('editor', '')
            author = entry.get('author', '').split(',')[0].lower()
            author = strclean(author.split()[-1])
            year = entry.get('year', '').split()[-1]
            doi = entry.get('doi', '')
            
            wordlist = {
                "the", "and", "of", "for", "to", "in", "on", "at", "with", "a", "an", "by"
            }
            titlelist = re.findall(r"[a-z]+", strclean(entry.get('title', '')))
            titlelist = [w[0] for w in titlelist if w not in wordlist]
            titleabv = "".join(titlelist[:4])

            i = 1
            bib_id = f"{author}{year[-2:]}{titleabv}"
            alt_bib_id = bib_id
            while alt_bib_id in id_set:
                alt_bib_id = f"{author}{year[-2:]}{titleabv}{chr(ord('a') + i)}"
                i += 1

            if bib_id in id_set and doi in doi_set:
                delete_set.add(entry['ID'])
            elif bib_id in id_set and doi not in doi_set:
                entry['ID'] = alt_bib_id
            else:
                entry['ID'] = bib_id

            if entry['ID'] in cache_id_set:
                delete_set.add(entry['ID'])

        except:
            delete_set.add(entry['ID'])
            continue

        id_set.add(entry['ID'])
        doi_set.add(doi)
        
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-z', '--zoterobib', type=str, help='Name of Zotero BibTex file', default='zotero.bib')
    parser.add_argument('-m', '--mendeleybib', type=str, help='Name of Mendeley BibTex file', default='mendeley.bib')
    parser.add_argument('-d', '--debug', type=bool, help='Activate Debug Mode', default=False)
    args = parser.parse_args()

    zotero_ref_path = os.path.join(os.path.dirname(__file__), args.zoterobib)
    mendeley_ref_path = os.path.join(os.path.dirname(__file__), args.mendeleybib)
    cache_path = os.path.join(os.path.dirname(__file__), 'clean_ref_cache.bib')

    if os.path.exists(zotero_ref_path):
        with open(zotero_ref_path) as infile:
            bibdb = bibtexparser.load(infile)
    else:
        bibdb = bibtexparser.bibdatabase.BibDatabase()

    if os.path.exists(mendeley_ref_path):
        with open(mendeley_ref_path) as infile2:
            bibdb2 = bibtexparser.load(infile2)
    else:
        bibdb2 = bibtexparser.bibdatabase.BibDatabase()

    if not os.path.exists(cache_path):
        with open(cache_path, 'w') as infile3:
            pass
    with open(cache_path) as infile3:
        cachebibdb = bibtexparser.load(infile3)

    entry_id_delete = set()
    cache_id = {entry.get('ID', '') for entry in cachebibdb.entries}
    seen_id = set()
    logged_refs = set()

    clean_entries(bibdb.entries, entry_id_delete, logged_refs, seen_id, cache_id)
    clean_entries(bibdb2.entries, entry_id_delete, logged_refs, seen_id, cache_id)

    entry_sorted = sorted([entry for entry in bibdb.entries 
                         if not entry.get('ID') in entry_id_delete] + 
                          [entry for entry in bibdb2.entries 
                         if not entry.get('ID') in entry_id_delete] +
                          [entry for entry in cachebibdb.entries], 
                        key=lambda x: x['ID'])

    bibdb_sorted = bibtexparser.bibdatabase.BibDatabase()
    bibdb_sorted.entries = entry_sorted

    with open(
        os.path.join(os.path.dirname(__file__), 'clean_ref.bib'), 'w'
    ) as outfile:
        bibtexparser.dump(bibdb_sorted, outfile)

    if not args.debug:
        with open(cache_path, 'w') as outfile2:
            bibtexparser.dump(bibdb_sorted, outfile2)
    
    
if __name__ == "__main__":
    main()