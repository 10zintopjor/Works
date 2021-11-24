import csv
import re
import pyewts
import yaml
import shutil
import logging
import subprocess
import unidecode
import requests
from git import Repo
from github import Github
from pathlib import Path
from rdflib import Graph
from rdflib.namespace import RDF, RDFS, SKOS, OWL, Namespace, NamespaceManager, XSD


config = {
    "OP_ORG": "https://github.com/Openpecha"
}


BDR = Namespace("http://purl.bdrc.io/resource/")
BDO = Namespace("http://purl.bdrc.io/ontology/core/")
EWTSCONV = pyewts.pyewts()


logging.basicConfig(
    filename="readme_update.log",
    format="%(levelname)s: %(message)s",
    level=logging.INFO
)


def notifier(msg):
    logging.info(msg)


def clean_dir(layers_output_dir):
    if layers_output_dir.is_dir():
        shutil.rmtree(str(layers_output_dir))


def update_repo(g, pecha_id, file_path, commit_msg, new_content):
    try:
        repo = g.get_repo(f"Openpecha/{pecha_id}")
        contents = repo.get_contents(f"{file_path}", ref="master")
        repo.update_file(contents.path, commit_msg,
                         new_content, contents.sha, branch="master")
        print(f'{pecha_id} update completed..')
    except:
        print('Repo not found')


def get_new_readme(pecha_id, title, alternative_title, author, work_id, initial_type, total_vol, plain_title, pages_title, tag):
    Title = f"|{pecha_id}|{title} "
    Table = f"| --- | --- "
    if alternative_title != None:
        AlternativeTitle = f"|Alternative Title |{alternative_title}"
    else:
        AlternativeTitle = f"|Alternative Title |"
    if author != None:
        Author = f'|Author| {author}'
    else:
        Author = f'|Author | '
    Bdrcid = f"|BDRC ID | {work_id}"
    if initial_type == "ocr":
        Creator = f"|Creator | Google OCR"
    else:
        Creator = f"|Creator | {initial_type}"
    NumOfVol = f"|Number of Volumes| {total_vol}"
    Download = f'|<img width="25" src="https://img.icons8.com/fluent/48/000000/download-2.png"/>  Download | [![](https://img.icons8.com/color/20/000000/txt.png)Plain Text](https://github.com/Openpecha/{pecha_id}/releases/download/v{tag}/{plain_title}), [![](https://img.icons8.com/color/20/000000/txt.png)Text with Pagination](https://github.com/Openpecha/{pecha_id}/releases/download/v{tag}/{pages_title})'
    Edit = f'|<img width="25" src="https://img.icons8.com/color/25/000000/edit-property.png">Edit Online| [<img width="25" src="https://avatars.githubusercontent.com/u/45091458?s=200&v=4"> Open in Editor](http://editor.openpecha.org/{pecha_id})'
    BdrcLink = f'|<img width="25" src="https://img.icons8.com/plasticine/100/000000/pictures-folder.png"/>  Source Images | [<img width="25" src="https://library.bdrc.io/icons/BUDA-small.svg"> Images of text file open in BUDA](https://library.bdrc.io/show/bdr:{work_id})'
    new_readme = f"{Title}\n{Table}\n{AlternativeTitle}\n{Author}\n{Bdrcid}\n{Creator}\n{NumOfVol}\n{Edit}\n{Download}\n{BdrcLink}"
    return new_readme


def get_author_id(g, work_id):
    try:
        work_id = f"M{work_id}"
        instance_ids = g.objects(BDR[work_id], BDO["instanceOf"])
        for instance_id in instance_ids:
            instance_id = get_id(str(instance_id))
        agent_ids = g.objects(BDR[instance_id], BDO["creator"])
        for agent_id in agent_ids:
            agent_id = get_id(str(agent_id))
        author_ids = g.objects(BDR[agent_id], BDO["agent"])
        for author_id in author_ids:
            author_id = get_id(str(author_id))
        return author_id
    except:
        notifier(f"{pecha_id} no author")
        return None


def parse_author_ttl(author_ttl, work_id):
    g = Graph()
    try:
        g.parse(data=author_ttl, format="ttl")
    except:
        print(f"{work_id}.ttl Contains bad syntax")
        return {}
    author_id = get_author_id(g, work_id)
    if author_id != None:
        author = g.value(BDR[author_id], SKOS["prefLabel"])
        if author.language == "bo-x-ewts":
            author = ewtstobo(author)
        return author
    else:
        return None


def get_author_ttl(work_id):
    try:
        author_ttl = requests.get(
            f"http://purl.bdrc.io/query/graph/OP_info?R_RES=bdr:{work_id}&format=ttl")
        return author_ttl.text
    except:
        print(' TTL not Found!!!')
        return None


def get_title(metadata):
    meta_title = metadata['source_metadata']['title']
    return meta_title


def ewtstobo(ewtsstr):
    res = EWTSCONV.toUnicode(ewtsstr)
    return res


def get_id(URI):
    return URI.split("/")[-1]


def get_title_ids(g, work_id):
    title_ids = []
    volumes = g.objects(BDR[work_id], BDO["hasTitle"])
    for volume in volumes:
        title_id = get_id(str(volume))
        title_ids.append(title_id)
    return title_ids


def parse_readme_info(meta_ttl, work_id):
    title_list = []
    eng_title = []
    title_info = {}
    curr_title = {}
    alternative_title = None
    work_id = f"M{work_id}"
    g = Graph()
    try:
        g.parse(data=meta_ttl, format="ttl")
    except:
        logging.warning(f"{work_id}.ttl Contains bad syntax")
        return {}
    title_ids = get_title_ids(g, work_id)
    title_ids.sort()
    for title_id in title_ids:
        title = g.value(BDR[title_id], RDFS.label)
        if title.language == "bo-x-ewts":
            title_list.append(title)
        else:
            if title.language == "en":
                eng_title.append(title)
            elif title.language == "zh-latn-pinyin-x-ndia":
                eng_title.append(title)
    if len(title_list) >= 2:
        print(f"this is the legth {len(title_list)}")
        for num, title in enumerate(title_list, 0):
            title_len = len(title)
            title = ewtstobo(title)
            if title_len in title_info.keys():
                title_len += 1
            curr_title[title_len] = {"title": title}
            title_info.update(curr_title)
            curr_title = {}
    else:
        if len(title_list) == 1:
            title = title_list[0]
            main_title = ewtstobo(title)
            return main_title, None
        elif len(eng_title) != 0:
            for num, title in enumerate(eng_title, 0):
                title_len = len(title)
                curr_title[title_len] = {"title": title}
                title_info.update(curr_title)
                curr_title = {}
    num = 1
    for key, value in sorted(title_info.items()):
        if num == 1:
            main_title = value["title"]
            num += 1
        elif num == 2:
            alternative_title = value["title"]
    return main_title, alternative_title


def get_ttl(work_id):
    try:
        ttl = requests.get(f"http://purl.bdrc.io/graph/M{work_id}.ttl")
        return ttl.text
    except:
        print(' TTL not Found!!!')
        return None


def get_meta_info(metadata):
    initial_type = metadata['initial_creation_type']
    meta_bdrcid = metadata['source_metadata']['id'][4:]
    return meta_bdrcid, initial_type


def get_meta(g, pecha_id):
    try:
        repo = g.get_repo(f"Openpecha/{pecha_id}")
        contents = repo.get_contents(f"{pecha_id}.opf/meta.yml")
        return contents.decoded_content.decode()
    except:
        print('Repo Not Found')
        return ''


def get_total_vol(g, pecha_id):
    repo = g.get_repo(f"Openpecha/{pecha_id}")
    contents = repo.get_contents(f"{pecha_id}.opf/base")
    total_vol = 0
    for content in contents:
        total_vol += 1
    return total_vol


def get_asset_titles(g, pecha_id):
    content = Path(
        f"./{pecha_id}/.github/workflows/create_release.yml").read_text(encoding='utf-8')
    release_yml = yaml.safe_load(content)
    release_project = release_yml['jobs']['release-project']['steps'][5]
    if release_project['name'] == "upload plain assets":
        plain_string = release_project['with']['asset_name']
    release_project = release_yml['jobs']['release-project']['steps'][6]
    if release_project['name'] == "upload pages assets":
        pages_string = release_project['with']['asset_name']
    plain_title = unidecode.unidecode(plain_string)
    pages_title = unidecode.unidecode(pages_string)
    return plain_title, pages_title


def get_branch(repo, branch):
    if branch in repo.heads:
        return branch
    return "master"


def download_pecha(pecha_id, out_path=None, branch="master"):
    pecha_url = f"{config['OP_ORG']}/{pecha_id}.git"
    out_path = Path(out_path)
    out_path.mkdir(exist_ok=True, parents=True)
    pecha_path = out_path / pecha_id
    Repo.clone_from(pecha_url, str(pecha_path))
    repo = Repo(str(pecha_path))
    branch_to_pull = get_branch(repo, branch)
    repo.git.checkout(branch_to_pull)
    print(f"{pecha_id} Downloaded ")
    return pecha_path


def get_tags(pecha_id):
    tags = subprocess.run(
        f'cd ./{pecha_id}; git tag', shell=True, capture_output=True, text=True)
    tag = tags.stdout
    tags = re.split(f"\\\n", tag)
    highest_tag = 0
    for _, tag in enumerate(tags, 1):
        if tag:
            tag = float(tag[1:])
            if highest_tag <= tag:
                highest_tag = tag
    return int(highest_tag)


if __name__ == "__main__":
    token = "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"
    g = Github(token)

    with open("catalog.csv", newline="") as csvfile:
        pechas = list(csv.reader(csvfile, delimiter=","))
        for pecha in pechas[3992:]:
            pecha_id = re.search("\[.+\]", pecha[0])[0][1:-1]
            file_path = "./"
            readme_path = "./README.md"
            commit_msg = 'readme updated'
            total_vol = get_total_vol(g, pecha_id)
            meta = get_meta(g, pecha_id)
            metadata = yaml.safe_load(meta)
            pecha_path = download_pecha(pecha_id, file_path)
            work_id, initial_type = get_meta_info(metadata)
            plain_title, pages_title = get_asset_titles(g, pecha_id)
            print(plain_title)
            print(pages_title)
            tag = get_tags(pecha_id)
            if tag >= 1:
                print(f"tag is {tag}")
                author_ttl = get_author_ttl(work_id)
                if author_ttl:
                    author = parse_author_ttl(author_ttl, work_id)
                    print(f"author is {author}")
                else:
                    author = None
                meta_ttl = get_ttl(work_id)
                clean_dir(pecha_path)
                if meta_ttl != None:
                    title, alternative_title = parse_readme_info(
                        meta_ttl, work_id)
                    print(f"{title}\n{alternative_title}")
                    if author != None:
                        new_readme = get_new_readme(
                            pecha_id, title, alternative_title, author, work_id, initial_type, total_vol, plain_title, pages_title, tag)
                    else:
                        new_readme = get_new_readme(
                            pecha_id, title, alternative_title, None, work_id, initial_type, total_vol, plain_title, pages_title, tag)
                else:
                    meta_title = get_title(metadata)
                    if author != None:
                        new_readme = get_new_readme(
                            pecha_id, meta_title, None, author, work_id, initial_type, total_vol, plain_title, pages_title, tag)
                    else:
                        new_readme = get_new_readme(
                            pecha_id, meta_title, None, None, work_id, initial_type, total_vol, plain_title, pages_title, tag)
                update_repo(g, pecha_id, readme_path, commit_msg, new_readme)
                notifier(f"{pecha_id}")
            else:
                clean_dir(pecha_path)
                notifier(f"{pecha_id} github not worked")
